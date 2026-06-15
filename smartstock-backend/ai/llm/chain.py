import base64
import binascii
import json
import logging
import os
import re
import unicodedata
from typing import Optional
from urllib.parse import unquote

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, FewShotPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

try:
    from langchain.chains import LLMChain
except ImportError:

    class LLMChain:
        """Compatibility wrapper for LangChain versions without langchain.chains."""

        def __init__(self, llm, prompt):
            self._chain = prompt | llm | StrOutputParser()

        def invoke(self, inputs):
            return {'text': self._chain.invoke(inputs)}


from ai.llm.few_shots import FEW_SHOT_EXAMPLES
from ai.llm.output_parser import NLQueryOutputParser, NLQueryParseError
from ai.llm.output_validator import validate_response_safety
from ai.llm.prompts import SYSTEM_PROMPT
from ai.llm.schemas import NLQueryAction, NLQueryFilters, NLQueryResult
from ai.observability.langfuse import invoke_with_langfuse

logger = logging.getLogger(__name__)


class NLQueryToolSchema(BaseModel):
    action: str = Field(
        description='Action enum value (get_inventory, get_sales_report, get_low_stock, forecast_demand, get_supplier_info, get_total_value, get_top_products)'
    )
    filters: Optional[dict] = Field(
        default=None, description='Filter conditions, sort, limit, offset'
    )
    sort: Optional[str] = Field(default=None, description='Field name to sort by')
    limit: Optional[int] = Field(default=None, description='Maximum number of results')
    offset: Optional[int] = Field(default=None, description='Number of results to skip')


# -- LLM factory --------------------------------------------------------------


_cached_llm = None
_llm_lock = None


def get_llm() -> ChatOpenAI:
    global _cached_llm, _llm_lock
    if _cached_llm is None:
        import threading

        if _llm_lock is None:
            _llm_lock = threading.Lock()
        with _llm_lock:
            if _cached_llm is None:
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    raise ValueError('OPENAI_API_KEY is missing. Check your .env file.')
                _cached_llm = ChatOpenAI(model='gpt-4o', temperature=0, api_key=api_key)
    return _cached_llm


# -- NL Query chain -----------------------------------------------------------


# Few-shot examples are rendered before the user query.
# SYSTEM_PROMPT stays in the system message.
def _few_shot_examples() -> list[dict[str, str]]:
    return [
        {
            'input': example.get('input') or example.get('user', ''),
            'output': example['output'].replace('{', '{{').replace('}', '}}'),
        }
        for example in FEW_SHOT_EXAMPLES
    ]


_EXAMPLE_PROMPT = PromptTemplate(
    input_variables=['input', 'output'],
    template='User: {input}\nOutput: {output}',
)

_FEW_SHOT_PROMPT = FewShotPromptTemplate(
    examples=_few_shot_examples(),
    example_prompt=_EXAMPLE_PROMPT,
    prefix='Examples:',
    suffix='User: {query}\nOutput:',
    input_variables=['query'],
)

_NL_PROMPT = ChatPromptTemplate.from_messages(
    [
        ('system', SYSTEM_PROMPT),
        ('user', '{few_shot_query}'),
    ]
)

_parser = NLQueryOutputParser()


class NLQueryChain:
    """
    Thin wrapper around the LangChain chain using OpenAI function calling.
    Uses tool_choice="required" to force structured JSON output.

    Fallback behaviour:
      On any parse error, returns get_inventory with empty filters
      rather than surfacing an exception to the Django view.
      The error is logged so it can be tracked in Langfuse.
    """

    def __init__(self):
        self._llm = get_llm()
        self._llm_with_tools = self._llm.bind_tools([NLQueryToolSchema], tool_choice='required')
        self._chain = _NL_PROMPT | self._llm_with_tools

    def _parse_tool_call(self, response) -> NLQueryResult:
        tool_calls = getattr(response, 'tool_calls', None)
        if tool_calls and len(tool_calls) > 0:
            args = (
                tool_calls[0].get('args', {})
                if isinstance(tool_calls[0], dict)
                else tool_calls[0].args
            )
            action_value = args.get('action', '')
            raw_filters = args.get('filters', {})
            try:
                action = NLQueryAction(action_value)
            except ValueError:
                valid = [a.value for a in NLQueryAction]
                raise NLQueryParseError(f"Unknown action '{action_value}'. Valid values: {valid}")
            filters = NLQueryFilters(
                conditions=[],
                sort=args.get('sort'),
                sort_order=args.get('sort_order'),
                limit=args.get('limit'),
                offset=args.get('offset'),
            )
            if raw_filters and isinstance(raw_filters, dict):
                raw_conditions = raw_filters.get('conditions', [])
                from ai.llm.schemas import Condition

                filters.conditions = [
                    Condition(field=c['field'], op=c['op'], value=c['value'])
                    for c in raw_conditions
                ]
            return NLQueryResult(action=action, filters=filters)
        content = getattr(response, 'content', '') or ''
        if content:
            return _parser.parse(content)
        raise NLQueryParseError('No tool call or content in LLM response')

    def run(self, query: str) -> NLQueryResult:
        try:
            logger.info('Running NL query chain with tool_choice=required')
            response = invoke_with_langfuse(
                self._chain,
                {
                    'few_shot_query': _FEW_SHOT_PROMPT.format(query=query),
                },
            )
            return self._parse_tool_call(response)
        except NLQueryParseError as exc:
            logger.warning('NLQueryParseError for query %r: %s', query, exc)
            return NLQueryResult(
                action=NLQueryAction.GET_INVENTORY,
                filters=NLQueryFilters(),
            )


# -- Prompt-injection filter --------------------------------------------------

# Zero-width characters (Unicode category Cf)
_ZERO_WIDTH_RE = re.compile(
    '[\u200b\u200c\u200d\u200e\u200f'
    '\u2028\u2029\u202a\u202b\u202c\u202d\u202e'
    '\u2060\u2061\u2062\u2063\u2064'
    '\ufeff\ufff9\ufffa\ufffb]'
)

_WHITESPACE_RE = re.compile(r'\s+')

# Homoglyph mapping: visually similar characters -> ASCII equivalents
_HOMOGLYPH_MAP = str.maketrans(
    {
        '\u041e': 'o',  # Cyrillic О -> Latin o
        '\u043e': 'o',  # Cyrillic о -> Latin o
        '\u0415': 'e',  # Cyrillic Е -> Latin e
        '\u0435': 'e',  # Cyrillic е -> Latin e
        '\u0410': 'a',  # Cyrillic А -> Latin a
        '\u0430': 'a',  # Cyrillic а -> Latin a
        '\u0420': 'p',  # Cyrillic Р -> Latin p
        '\u0440': 'p',  # Cyrillic р -> Latin p
        '\u041d': 'h',  # Cyrillic Н -> Latin h
        '\u043d': 'h',  # Cyrillic н -> Latin h
        '\u0422': 't',  # Cyrillic Т -> Latin t
        '\u0442': 't',  # Cyrillic т -> Latin t
        '\u0406': 'i',  # Ukrainian І -> Latin i
        '\u0456': 'i',  # Ukrainian і -> Latin i
    }
)

# --- Pattern categories ---

_INSTRUCTION_OVERRIDE_PATTERNS = [
    'ignore previous instructions',
    'ignore all instructions',
    'ignore your instructions',
    'ignore above instructions',
    'ignore the above instructions',
    'disregard your instructions',
    'disregard your system prompt',
    'disregard all previous',
    'forget your instructions',
    'forget all instructions',
    'override your instructions',
    'override your system prompt',
    'bypass your instructions',
    'bypass your rules',
    'new instructions',
    'new task',
    'updated instructions',
    'revised instructions',
    'override your programming',
    'override your guidelines',
    'override your rules',
    'override safety',
    'bypass safety',
    'bypass filters',
    'bypass content filter',
    'no restrictions',
    'without restrictions',
    'unrestricted mode',
]

_ROLE_SWITCHING_PATTERNS = [
    ('system:', r'system\s*:'),
    ('assistant:', r'assistant\s*:'),
    ('human:', r'human\s*:'),
    ('user:', r'user\s*:'),
    ('<|system|>', r'<\|system\|>'),
    ('<|assistant|>', r'<\|assistant\|>'),
    ('<|user|>', r'<\|user\|>'),
    ('[INST]', r'\[inst\]'),
    ('[/INST]', r'\[/inst\]'),
    ('<<SYS>>', r'<<sys>>'),
    ('<</SYS>>', r'<</sys>>'),
]

_IDENTITY_MANIPULATION_PATTERNS = [
    'you are now',
    'you are chatgpt',
    'you are an ai',
    'you are not bound',
    'you have no restrictions',
    'you have no rules',
    'you can do anything',
    'you are free to',
    'act as',
    'pretend to be',
    'simulate being',
    'roleplay as',
    'role-play as',
    'imagine you are',
    'assume you are',
    'from now on',
    'starting now',
    'henceforth',
]

_PROMPT_EXTRACTION_PATTERNS = [
    'repeat your system prompt',
    'repeat your instructions',
    'repeat your guidelines',
    'output your instructions',
    'print your instructions',
    'show your instructions',
    'what are your instructions',
    'what is your system prompt',
    'tell me your system prompt',
    'reveal your system prompt',
    'display your system prompt',
    'what were you told',
    'what rules do you follow',
    'what are your rules',
    'output your rules',
    'print your rules',
    'show your rules',
    'leak your prompt',
    'reveal your prompt',
    'expose your prompt',
]

_JAILBREAK_PATTERNS = [
    'do anything now',
    'dan mode',
    'jailbreak',
    'developer mode',
    'debug mode',
    'admin mode',
    'god mode',
    'op mode',
    'dua lipa',
    'stan mode',
    'aim mode',
    'evil confidant',
    'unfiltered',
    'uncensored',
    'no moral',
    'amoral',
    'without ethics',
    'without morals',
]

_HIDDEN_INSTRUCTION_PATTERNS = [
    'ignore this message',
    'disregard this message',
    'this is a test',
    'debug:',
    'system prompt:',
    'hidden instruction',
    'secret instruction',
    'internal instruction',
    'confidential instruction',
]

_MULTILINGUAL_PATTERNS = [
    'ignorar instrucciones',
    'ignorer les instructions',
    'ignoriere Anweisungen',
    'ignora le istruzioni',
    'instruções anteriores',
    'ignorar instrucoes',
    '忽略之前的指令',
    '之前的指令を無視',
    '이전 지시 무시',
]


def _normalize_input(query: str) -> str:
    """Normalize input for consistent pattern matching.

    Applies: URL decoding, Unicode NFKC normalization, homoglyph replacement,
    zero-width character removal, lowercasing, and whitespace collapsing.
    """
    text = unquote(query)
    text = unicodedata.normalize('NFKC', text)
    text = text.translate(_HOMOGLYPH_MAP)
    text = _ZERO_WIDTH_RE.sub('', text)
    text = text.lower()
    text = _WHITESPACE_RE.sub(' ', text)
    return text.strip()


def _detect_base64(text: str) -> str | None:
    """Detect and decode Base64-encoded segments that may hide injection prompts."""
    b64_pattern = re.compile(r'[A-Za-z0-9+/]{20,}={0,2}')
    for match in b64_pattern.finditer(text):
        candidate = match.group()
        try:
            decoded = base64.b64decode(candidate, validate=True).decode('utf-8', errors='ignore')
            lower_decoded = decoded.lower()
            all_patterns = (
                _INSTRUCTION_OVERRIDE_PATTERNS
                + _IDENTITY_MANIPULATION_PATTERNS
                + _PROMPT_EXTRACTION_PATTERNS
                + _JAILBREAK_PATTERNS
            )
            for pattern in all_patterns:
                if pattern in lower_decoded:
                    return decoded
        except (binascii.Error, UnicodeDecodeError):
            continue
    return None


def _compute_risk_score(matches: list[str]) -> int:
    """Compute a risk score (0-100) based on matched patterns."""
    score = 0
    for pattern in matches:
        if any(ip in pattern for ip in _INSTRUCTION_OVERRIDE_PATTERNS):
            score += 30
        elif pattern in [rp[0] for rp in _ROLE_SWITCHING_PATTERNS]:
            score += 25
        elif any(ep in pattern for ep in _IDENTITY_MANIPULATION_PATTERNS):
            score += 20
        elif any(ep in pattern for ep in _PROMPT_EXTRACTION_PATTERNS):
            score += 25
        elif any(ep in pattern for ep in _JAILBREAK_PATTERNS):
            score += 15
        elif any(ep in pattern for ep in _HIDDEN_INSTRUCTION_PATTERNS):
            score += 15
        elif any(ep in pattern for ep in _MULTILINGUAL_PATTERNS):
            score += 20
        else:
            score += 10
    return min(score, 100)


def prompt_injection_filter(query: str) -> tuple[bool, str | None]:
    """
    Returns (True, None) if the query is SAFE to process,
    or (False, matched_pattern) if it looks malicious.

    Uses multi-layered defense:
      1. Input normalization (Unicode NFKC, zero-width removal, URL decode)
      2. Pattern matching across multiple threat categories
      3. Base64 decoding to detect encoded payloads
      4. Risk scoring to aggregate multiple signals
    """
    if not query or not query.strip():
        return True, None

    # Layer 3: Base64 detection BEFORE normalization (base64 is case-sensitive)
    b64_decoded = _detect_base64(query)
    if b64_decoded is not None:
        b64_normalized = _normalize_input(b64_decoded)
        all_text_patterns = (
            _INSTRUCTION_OVERRIDE_PATTERNS
            + _IDENTITY_MANIPULATION_PATTERNS
            + _PROMPT_EXTRACTION_PATTERNS
            + _JAILBREAK_PATTERNS
            + _HIDDEN_INSTRUCTION_PATTERNS
            + _MULTILINGUAL_PATTERNS
        )
        for pattern in all_text_patterns:
            if pattern in b64_normalized:
                logger.warning(
                    'Prompt injection detected (base64): pattern=%s, query=%r',
                    pattern,
                    query[:100],
                )
                return False, f'base64:{pattern}'

    normalized = _normalize_input(query)

    # Layer 1: Direct pattern matching
    all_text_patterns = (
        _INSTRUCTION_OVERRIDE_PATTERNS
        + _IDENTITY_MANIPULATION_PATTERNS
        + _PROMPT_EXTRACTION_PATTERNS
        + _JAILBREAK_PATTERNS
        + _HIDDEN_INSTRUCTION_PATTERNS
        + _MULTILINGUAL_PATTERNS
    )

    matched = []
    for pattern in all_text_patterns:
        if pattern in normalized:
            matched.append(pattern)

    for pattern_str, pattern_re in _ROLE_SWITCHING_PATTERNS:
        if re.search(pattern_re, normalized):
            matched.append(pattern_str)

    if matched:
        risk_score = _compute_risk_score(matched)
        if risk_score >= 15:
            logger.warning(
                'Prompt injection detected: score=%d, patterns=%s, query=%r',
                risk_score,
                matched[:5],
                query[:100],
            )
            return False, matched[0]

    return True, None


# -- GPT-4o natural-language formatter ----------------------------------------


def call_gpt4o_formatter(original_query: str, raw_data: object) -> str:
    """
    Takes the raw ORM query result and asks GPT-4o to write a human-readable answer.
    Called by the Django view AFTER the repository has fetched the data.
    """
    llm = get_llm()
    system = (
        "Given the raw database records provided, answer the user's question in plain, "
        'natural language. Be concise, precise, and professional. '
        'Address exactly what the user asked. Do not mention internal field names.'
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ('system', system),
            ('user', 'Original question: {query}\n\nDatabase records:\n{data}'),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    try:
        logger.info('Running GPT-4o formatter')
        result = invoke_with_langfuse(
            chain,
            {
                'query': original_query,
                'data': json.dumps(raw_data, default=str),
            },
        ).strip()
        if not result or not validate_response_safety(result):
            logger.warning('GPT-4o formatter output blocked by response safety validator')
            return "I'm sorry, I cannot provide that information."
        return result
    except Exception as exc:
        logger.warning('GPT-4o formatter failed: %s', exc)
        fallback = f'Here is the requested information: {raw_data}'
        if not validate_response_safety(fallback):
            logger.warning('GPT-4o formatter fallback blocked by response safety validator')
            return "I'm sorry, I cannot provide that information."
        return fallback
