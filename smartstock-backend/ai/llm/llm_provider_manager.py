"""
llm_provider_manager.py — Multi-provider LLM manager with automatic failover.

Implements circuit breaker pattern, exponential backoff, provider scoring,
and structured logging for observability. No agent may call OpenAI directly;
all LLM calls must route through LLMProviderManager.

Failover priority: Groq → OpenAI → Gemini → xAI
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Dict, Iterator, List, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatResult

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    FAILED = 'failed'
    CIRCUIT_OPEN = 'circuit_open'


@dataclass
class ProviderHealth:
    """Tracks health state for a single provider."""

    name: str
    status: ProviderStatus = ProviderStatus.HEALTHY
    consecutive_failures: int = 0
    total_calls: int = 0
    total_failures: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    avg_latency_ms: float = 0.0
    circuit_open_until: Optional[float] = None
    _latencies: List[float] = field(default_factory=list)
    _lock: Lock = field(default_factory=Lock)

    FAILURE_THRESHOLD: int = 3
    CIRCUIT_TIMEOUT: float = 60.0
    LATENCY_WINDOW: int = 10

    def record_success(self, latency_ms: float):
        with self._lock:
            self.consecutive_failures = 0
            self.total_calls += 1
            self.last_success_time = time.time()
            self.status = ProviderStatus.HEALTHY
            self.circuit_open_until = None
            self._latencies.append(latency_ms)
            if len(self._latencies) > self.LATENCY_WINDOW:
                self._latencies.pop(0)
            self.avg_latency_ms = sum(self._latencies) / len(self._latencies)

    def record_failure(self):
        with self._lock:
            self.consecutive_failures += 1
            self.total_calls += 1
            self.total_failures += 1
            self.last_failure_time = time.time()
            if self.consecutive_failures >= self.FAILURE_THRESHOLD:
                self.status = ProviderStatus.CIRCUIT_OPEN
                self.circuit_open_until = time.time() + self.CIRCUIT_TIMEOUT
                logger.warning(
                    'Circuit breaker OPEN for %s after %d failures.',
                    self.name,
                    self.consecutive_failures,
                )
            else:
                self.status = ProviderStatus.DEGRADED

    def is_available(self) -> bool:
        if self.status == ProviderStatus.CIRCUIT_OPEN:
            if self.circuit_open_until and time.time() > self.circuit_open_until:
                logger.info('Circuit breaker half-open for %s', self.name)
                self.status = ProviderStatus.DEGRADED
                return True
            return False
        return True

    @property
    def error_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_failures / self.total_calls

    def score(self) -> float:
        if not self.is_available():
            return float('inf')
        latency_score = self.avg_latency_ms / 1000.0
        error_score = self.error_rate * 10.0
        return latency_score + error_score


class FailoverChatLLM(BaseChatModel):
    """
    BaseChatModel subclass with automatic provider failover.
    Drop-in replacement for ChatOpenAI — works with LangChain chains and agents.
    """

    llm_pool: list = []
    manager: Any = None
    provider_names: List[str] = []

    class Config:
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        return 'failover-chat-llm'

    @property
    def _identifying_params(self) -> dict:
        return {
            'provider_pool': self.provider_names,
            'primary': self.provider_names[0] if self.provider_names else None,
        }

    def bind_tools(self, tools, **kwargs):
        new_pool = []
        for pname, llm in self.llm_pool:
            try:
                bound = llm.bind_tools(tools, **kwargs)
                new_pool.append((pname, bound))
            except Exception:
                new_pool.append((pname, llm))
        return FailoverChatLLM(
            llm_pool=new_pool,
            manager=self.manager,
            provider_names=self.provider_names,
        )

    def with_structured_output(self, schema, **kwargs):
        new_pool = []
        for pname, llm in self.llm_pool:
            try:
                structured = llm.with_structured_output(schema, **kwargs)
                new_pool.append((pname, structured))
            except Exception:
                new_pool.append((pname, llm))
        return FailoverChatLLM(
            llm_pool=new_pool,
            manager=self.manager,
            provider_names=self.provider_names,
        )

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        last_error = None
        for provider_name, llm in self.llm_pool:
            start = time.time()
            try:
                result = llm._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
                latency_ms = (time.time() - start) * 1000
                self.manager.record_success(provider_name, latency_ms)
                return result
            except Exception as e:
                latency_ms = (time.time() - start) * 1000
                self.manager.record_failure(provider_name)
                last_error = e
                is_transient = self._is_transient_error(e)
                logger.warning(
                    'LLM call failed on %s (transient=%s): %s',
                    provider_name,
                    is_transient,
                    str(e)[:200],
                )
                if not is_transient:
                    raise
                continue
        raise RuntimeError(f'All providers failed. Last error: {last_error}')

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> Iterator[AIMessageChunk]:
        last_error = None
        for provider_name, llm in self.llm_pool:
            start = time.time()
            try:
                for chunk in llm._stream(messages, stop=stop, run_manager=run_manager, **kwargs):
                    yield chunk
                latency_ms = (time.time() - start) * 1000
                self.manager.record_success(provider_name, latency_ms)
                return
            except Exception as e:
                latency_ms = (time.time() - start) * 1000
                self.manager.record_failure(provider_name)
                last_error = e
                if not self._is_transient_error(e):
                    raise
                continue
        raise RuntimeError(f'All providers failed. Last error: {last_error}')

    @staticmethod
    def _is_transient_error(e: Exception) -> bool:
        msg = str(e).lower()
        return any(
            kw in msg
            for kw in (
                '429',
                'rate',
                'too many',
                'resource_exhausted',
                'timeout',
                'timed out',
                'connection',
                '503',
                '502',
                'overloaded',
                'quota',
                'throttl',
            )
        )


class LLMProviderManager:
    """
    Central LLM provider manager with automatic failover.
    """

    PROVIDER_PRIORITY = ['groq', 'openai', 'gemini', 'xai']

    def __init__(self):
        self._health: Dict[str, ProviderHealth] = {}
        self._providers_config: Dict[str, Dict] = {}
        self._initialized = False
        self._init_lock = Lock()

    def _initialize(self):
        if self._initialized:
            return
        with self._init_lock:
            if self._initialized:
                return
            from .provider_config import _PROVIDERS

            self._providers_config = _PROVIDERS
            for name in _PROVIDERS:
                self._health[name] = ProviderHealth(name=name)
            self._initialized = True
            logger.info(
                'LLMProviderManager initialized: %s',
                ' -> '.join(self.PROVIDER_PRIORITY),
            )

    def _get_available_providers(self) -> List[str]:
        self._initialize()
        import os

        available = []
        for name in self.PROVIDER_PRIORITY:
            if name not in self._health:
                continue
            if not self._health[name].is_available():
                continue
            config = self._providers_config[name]
            if not os.getenv(config['api_key_env'], ''):
                continue
            available.append(name)
        available.sort(key=lambda n: self._health[n].score())
        return available

    def get_llm(
        self,
        temperature: float = 0,
        model_override: Optional[str] = None,
        provider_override: Optional[str] = None,
    ) -> FailoverChatLLM:
        self._initialize()

        if provider_override:
            providers_to_try = [provider_override]
        else:
            providers_to_try = self._get_available_providers()

        if not providers_to_try:
            raise RuntimeError(
                'No LLM providers available. '
                f'Health: { {n: h.status.value for n, h in self._health.items()} }'
            )

        llm_pool = []
        for pname in providers_to_try:
            try:
                llm = self._create_llm(pname, temperature, model_override)
                llm_pool.append((pname, llm))
                logger.info(
                    'Created LLM: %s/%s',
                    pname,
                    model_override or self._providers_config[pname]['chat_model'],
                )
            except Exception as e:
                self._health[pname].record_failure()
                logger.warning('Failed to create LLM for %s: %s', pname, e)

        if not llm_pool:
            raise RuntimeError('All providers failed to create LLM instances')

        return FailoverChatLLM(
            llm_pool=llm_pool,
            manager=self,
            provider_names=[n for n, _ in llm_pool],
        )

    def _create_llm(self, provider_name: str, temperature: float, model_override: Optional[str]):
        config = self._providers_config[provider_name]
        model = model_override or config['chat_model']
        import os

        api_key = os.getenv(config['api_key_env'], '')
        if not api_key:
            raise ValueError(f'No API key for {provider_name}')

        if provider_name == 'gemini':
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                google_api_key=api_key,
                request_timeout=30,
                max_retries=0,
                model_kwargs={'max_remote_calls': 1},
            )

        from langchain_openai import ChatOpenAI

        kwargs = {
            'model': model,
            'temperature': temperature,
            'api_key': api_key,
            'request_timeout': 30,
            'max_retries': 0,
        }
        if config['base_url']:
            kwargs['base_url'] = config['base_url']
        return ChatOpenAI(**kwargs)

    def record_success(self, provider_name: str, latency_ms: float):
        self._initialize()
        if provider_name in self._health:
            self._health[provider_name].record_success(latency_ms)

    def record_failure(self, provider_name: str):
        self._initialize()
        if provider_name in self._health:
            self._health[provider_name].record_failure()

    def get_health_report(self) -> Dict[str, Any]:
        self._initialize()
        return {
            name: {
                'status': h.status.value,
                'consecutive_failures': h.consecutive_failures,
                'total_calls': h.total_calls,
                'total_failures': h.total_failures,
                'error_rate': f'{h.error_rate:.1%}',
                'avg_latency_ms': f'{h.avg_latency_ms:.1f}',
                'score': f'{h.score():.3f}',
            }
            for name, h in self._health.items()
        }

    def reset_circuit_breaker(self, provider_name: Optional[str] = None):
        self._initialize()
        targets = [provider_name] if provider_name else list(self._health.keys())
        for name in targets:
            if name in self._health:
                self._health[name].consecutive_failures = 0
                self._health[name].status = ProviderStatus.HEALTHY
                self._health[name].circuit_open_until = None


# Singleton
_manager: Optional[LLMProviderManager] = None


def get_provider_manager() -> LLMProviderManager:
    global _manager
    if _manager is None:
        _manager = LLMProviderManager()
    return _manager
