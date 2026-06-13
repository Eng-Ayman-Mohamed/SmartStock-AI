from types import SimpleNamespace
from uuid import uuid4

from django.test import override_settings

from ai.observability import langfuse


def reset_langfuse_globals():
    langfuse._langfuse_client = None
    langfuse._langfuse_handler = None


@override_settings(LANGFUSE_PUBLIC_KEY='', LANGFUSE_SECRET_KEY='')
def test_get_langfuse_client_returns_none_without_credentials():
    reset_langfuse_globals()

    assert langfuse.get_langfuse_client() is None


@override_settings(LANGFUSE_PUBLIC_KEY='', LANGFUSE_SECRET_KEY='')
def test_get_langfuse_callback_handler_returns_none_without_credentials():
    reset_langfuse_globals()

    assert langfuse.get_langfuse_callback_handler() is None
    assert langfuse.get_langchain_callbacks() == []


def test_invoke_with_langfuse_can_return_token_usage(monkeypatch):
    reset_langfuse_globals()
    monkeypatch.setattr(langfuse, 'get_langchain_callbacks', lambda: [])

    class FakeChain:
        def invoke(self, payload, config=None):
            assert payload == {'query': 'stock'}
            assert config is None
            return SimpleNamespace(
                content='answer',
                usage_metadata={'input_tokens': 10, 'output_tokens': 4},
            )

    result, token_usage = langfuse.invoke_with_langfuse(
        FakeChain(),
        {'query': 'stock'},
        include_token_usage=True,
    )

    assert result.content == 'answer'
    assert token_usage == {'input_tokens': 10, 'output_tokens': 4}


@override_settings(
    LANGFUSE_ALERT_THRESHOLDS={
        'llm_latency_p95_ms_warning': 3000,
        'agent_success_rate_minimum': 0.8,
    }
)
def test_trace_agent_run_sends_alert_thresholds(monkeypatch):
    reset_langfuse_globals()
    trace = SimpleNamespace(spans=[], span=lambda **kwargs: trace.spans.append(kwargs))
    client = SimpleNamespace(
        traces=[],
        flushed=False,
        trace=lambda **kwargs: client.traces.append(kwargs) or trace,
        flush=lambda: setattr(client, 'flushed', True),
    )
    monkeypatch.setattr(langfuse, 'get_langfuse_client', lambda: client)

    langfuse.trace_agent_run('decision_agent', {'in': 1}, {'out': 2}, spans=[])

    assert client.traces[0]['metadata']['alert_thresholds']['agent_success_rate_minimum'] == 0.8
    assert client.flushed is True


def test_core_callback_handler_extracts_llm_token_usage():
    reset_langfuse_globals()
    spans = []
    trace = SimpleNamespace(span=lambda **kwargs: spans.append(kwargs))
    client = SimpleNamespace(trace=lambda **kwargs: trace, flush=lambda: None)
    handler = langfuse._LangfuseCoreCallbackHandler(client)
    run_id = uuid4()

    handler.on_llm_start({'name': 'fake-model'}, ['prompt'], run_id=run_id)
    handler.on_llm_end(
        SimpleNamespace(llm_output={'token_usage': {'prompt_tokens': 12}}),
        run_id=run_id,
    )

    assert spans[0]['metadata']['token_usage'] == {'prompt_tokens': 12}
