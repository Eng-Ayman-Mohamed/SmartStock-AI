import logging
import os
import time

try:
    from langchain_core.callbacks import BaseCallbackHandler
except Exception:

    class BaseCallbackHandler:
        pass


logger = logging.getLogger(__name__)

_langfuse_client = None
_langfuse_handler = None


def _setting(name: str, default=None):
    try:
        from django.conf import settings

        return getattr(settings, name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)


def get_langfuse_client():
    global _langfuse_client
    if _langfuse_client is not None:
        return _langfuse_client

    public_key = _setting('LANGFUSE_PUBLIC_KEY')
    secret_key = _setting('LANGFUSE_SECRET_KEY')
    if not public_key or not secret_key:
        return None

    try:
        from langfuse import Langfuse

        _langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=_setting('LANGFUSE_HOST', 'https://cloud.langfuse.com'),
        )
    except Exception as exc:
        logger.debug('Langfuse client unavailable: %s', exc)
        _langfuse_client = None
    return _langfuse_client


def get_langfuse_callback_handler():
    global _langfuse_handler
    if _langfuse_handler is not None:
        return _langfuse_handler

    public_key = _setting('LANGFUSE_PUBLIC_KEY')
    secret_key = _setting('LANGFUSE_SECRET_KEY')
    if not public_key or not secret_key:
        return None

    try:
        from langfuse.callback import CallbackHandler

        _langfuse_handler = CallbackHandler(
            public_key=public_key,
            secret_key=secret_key,
            host=_setting('LANGFUSE_HOST', 'https://cloud.langfuse.com'),
        )
    except Exception as exc:
        logger.debug('Official Langfuse callback unavailable: %s', exc)
        client = get_langfuse_client()
        if client is not None:
            _langfuse_handler = _LangfuseCoreCallbackHandler(client)
    return _langfuse_handler


def get_langchain_callbacks() -> list:
    handler = get_langfuse_callback_handler()
    return [handler] if handler is not None else []


def extract_token_usage(response) -> dict:
    if response is None:
        return {}

    llm_output = getattr(response, 'llm_output', None)
    if isinstance(llm_output, dict):
        usage = llm_output.get('token_usage') or llm_output.get('usage')
        if isinstance(usage, dict):
            return usage

    usage_metadata = getattr(response, 'usage_metadata', None)
    if isinstance(usage_metadata, dict):
        return usage_metadata

    response_metadata = getattr(response, 'response_metadata', None)
    if isinstance(response_metadata, dict):
        usage = response_metadata.get('token_usage') or response_metadata.get('usage')
        if isinstance(usage, dict):
            return usage

    if isinstance(response, dict):
        usage = response.get('token_usage') or response.get('usage') or response.get('usage_metadata')
        if isinstance(usage, dict):
            return usage

    return {}


def get_langfuse_alert_thresholds() -> dict:
    thresholds = _setting('LANGFUSE_ALERT_THRESHOLDS', {})
    return thresholds if isinstance(thresholds, dict) else {}


def invoke_with_langfuse(chain, payload: dict, include_token_usage: bool = False):
    callbacks = get_langchain_callbacks()
    if callbacks:
        result = chain.invoke(payload, config={'callbacks': callbacks})
    else:
        result = chain.invoke(payload)
    if include_token_usage:
        return result, extract_token_usage(result)
    return result


def trace_agent_run(
    agent_name: str, input_data: dict, output_data: dict, spans: list[dict] | None = None
):
    client = get_langfuse_client()
    if client is None:
        return
    try:
        trace = client.trace(
            name=agent_name,
            input=input_data,
            output=output_data,
            metadata={
                'span_count': len(spans or []),
                'alert_thresholds': get_langfuse_alert_thresholds(),
            },
        )
        for span in spans or []:
            trace.span(
                name=span['name'],
                input=span.get('input'),
                output=span.get('output'),
                metadata={'duration_ms': span.get('duration_ms')},
            )
        client.flush()
    except Exception as exc:
        logger.debug('Langfuse agent trace skipped: %s', exc)


class _LangfuseCoreCallbackHandler(BaseCallbackHandler):
    """Small langchain-core-compatible fallback when langfuse.callback cannot import."""

    def __init__(self, client):
        self.client = client
        self.runs = {}

    def on_llm_start(self, serialized, prompts, *, run_id, parent_run_id=None, **kwargs):
        try:
            self.runs[str(run_id)] = {
                'trace': self.client.trace(
                    name='llm_call',
                    input=prompts,
                    metadata={
                        'run_id': str(run_id),
                        'parent_run_id': str(parent_run_id) if parent_run_id else None,
                        'model': serialized.get('name') if isinstance(serialized, dict) else None,
                    },
                ),
                'started_at': time.time(),
            }
        except Exception as exc:
            logger.debug('Langfuse llm start skipped: %s', exc)

    def on_llm_end(self, response, *, run_id, **kwargs):
        run = self.runs.pop(str(run_id), None)
        if not run:
            return
        try:
            run['trace'].span(
                name='llm_generation',
                output=str(response),
                metadata={
                    'duration_ms': round((time.time() - run['started_at']) * 1000),
                    'token_usage': extract_token_usage(response),
                },
            )
            self.client.flush()
        except Exception as exc:
            logger.debug('Langfuse llm end skipped: %s', exc)

    def on_llm_error(self, error, *, run_id, **kwargs):
        run = self.runs.pop(str(run_id), None)
        if not run:
            return
        try:
            run['trace'].span(
                name='llm_error',
                output={'error': str(error)},
                metadata={'duration_ms': round((time.time() - run['started_at']) * 1000)},
            )
            self.client.flush()
        except Exception as exc:
            logger.debug('Langfuse llm error skipped: %s', exc)
