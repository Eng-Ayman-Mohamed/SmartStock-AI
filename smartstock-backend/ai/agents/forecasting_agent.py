import concurrent.futures
import logging
import time

from django.db.models import QuerySet
from langchain_core.tools import StructuredTool

from ai.agents.tools.forecast_db_read import ForecastDBReadTool
from ai.agents.tools.forecast_db_write import ForecastDBWriteTool
from ai.agents.tools.prophet_run import ProphetRunTool
from ai.agents.tracking import complete_agent_run, create_agent_run
from ai.llm.chain import prompt_injection_filter
from ai.observability.langfuse import (
    get_langchain_callbacks,
    trace_agent_run,
)
from apps.audit.models import AgentRun
from apps.forecasting.repositories import ForecastingRepository
from apps.monitoring.tasks import record_agent_run_task

try:
    from langchain.agents import create_react_agent as create_agent
except ImportError:
    try:
        from langchain.agents import create_agent
    except ImportError:
        create_agent = None

logger = logging.getLogger(__name__)

FORECASTING_AGENT_SYSTEM_PROMPT = """You are SmartStock AI's forecasting agent.
Your job is to generate 30-day demand forecasts for inventory SKUs.

For each SKU, follow this exact process:
1. Call forecast_db_read_tool with the sku_id to load historical sales.
2. Pass the returned data to prophet_run_tool with the same sku_id and periods=30.
3. Call forecast_db_write_tool with the sku_id and the forecast results to persist them.

Constraints:
- Only process the SKU ID provided in your instructions.
- Do not invent or modify data between tool calls — pass data as returned.
- If forecast_db_read_tool returns has_data=false, still call prophet_run_tool
  with an empty data list so it can produce a moving average fallback.
- Stop after the write step is complete.
"""


class ForecastingAgentExecutionError(Exception):
    pass


class ForecastingAgent:
    def __init__(
        self,
        read_tool=None,
        prophet_tool=None,
        write_tool=None,
        repo=None,
        llm=None,
        agent_factory=None,
        max_iterations: int = 8,
        tool_retries: int = 1,
        tool_timeout: int = 120,
        executor=None,
    ):
        self.read_tool = read_tool or ForecastDBReadTool()
        self.prophet_tool = prophet_tool or ProphetRunTool()
        self.write_tool = write_tool or ForecastDBWriteTool()
        self.repo = repo or ForecastingRepository()
        self.llm = llm
        self.agent_factory = agent_factory
        self.max_iterations = max_iterations
        self.tool_retries = tool_retries
        self.tool_timeout = tool_timeout
        self.executor = executor or concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def run(self, context: dict | None = None) -> dict:
        payload = context or {}
        # Prompt injection guard — reject malicious context before execution
        for _key, _val in payload.items():
            if isinstance(_val, str):
                _is_safe, _ = prompt_injection_filter(_val)
                if not _is_safe:
                    raise ValueError('Request blocked: prompt injection detected in input payload')
        agent_run = create_agent_run('forecasting_agent')
        _started_at = time.time()
        trace_spans = []
        results = []
        status = AgentRun.Status.COMPLETED
        error = ''

        output = {
            'agent': 'forecasting_agent',
            'status': 'completed',
            'total_skus': 0,
            'processed': 0,
            'skipped': 0,
            'failed': 0,
            'results': [],
        }

        try:
            sku_ids = self._extract_sku_ids(payload)
        except Exception as exc:
            logger.exception('ForecastingAgent.run failed extracting SKU IDs')
            output['status'] = 'failed'
            output['error'] = str(exc)
            error = str(exc)
            status = AgentRun.Status.FAILED
        else:
            try:
                sku_map = {s.id: s.code for s in self.repo.get_skus_by_ids(sku_ids)}

                for sku_id in sku_ids:
                    sku_code = sku_map.get(sku_id, '')
                    try:
                        if self.repo.has_todays_forecast(sku_id):
                            logger.info(
                                'Skipping SKU %s (ID %d) — forecast exists for today',
                                sku_code,
                                sku_id,
                            )
                            results.append(
                                {
                                    'sku_id': sku_id,
                                    'sku_code': sku_code,
                                    'status': 'skipped',
                                    'reason': 'todays_forecast_exists',
                                }
                            )
                            continue
                        result = self._forecast_for_sku(sku_id, sku_code, trace_spans)
                        results.append(result)
                    except Exception as exc:
                        logger.exception('Forecasting agent failed for SKU ID %d: %s', sku_id, exc)
                        results.append(
                            {
                                'sku_id': sku_id,
                                'sku_code': sku_code,
                                'status': 'failed',
                                'error': str(exc),
                            }
                        )

                output['status'] = 'completed'
                output['total_skus'] = len(sku_ids)
                output['processed'] = sum(1 for r in results if r.get('status') == 'success')
                output['skipped'] = sum(1 for r in results if r.get('status') == 'skipped')
                output['failed'] = sum(1 for r in results if r.get('status') == 'failed')
                output['results'] = results
                if output['failed'] > 0:
                    status = AgentRun.Status.FAILED
                    error = f'{output["failed"]} SKU(s) failed'
            except Exception as exc:
                logger.exception('ForecastingAgent.run failed processing SKUs')
                output['status'] = 'failed'
                output['error'] = str(exc)
                error = str(exc)
                status = AgentRun.Status.FAILED
        finally:
            complete_agent_run(
                agent_run.id,
                status=status,
                error_message=error,
            )
            trace_agent_run('forecasting_agent', payload, output, trace_spans)
            _duration = round((time.time() - _started_at) * 1000)
            _outcome = (
                'failure' if output.get('failed', 0) > 0 or output.get('error') else 'success'
            )
            record_agent_run_task.delay(
                agent_name='forecasting_agent',
                outcome=_outcome,
                duration_ms=_duration,
                error_message=output.get('error', ''),
            )
        return output

    def _forecast_for_sku(self, sku_id: int, sku_code: str, trace_spans: list) -> dict:
        observations = {}
        tools = self._build_langchain_tools(sku_id, sku_code, trace_spans, observations)
        agent = self._create_agent(tools)
        agent_input = {
            'messages': [
                {
                    'role': 'user',
                    'content': (
                        f'Generate a 30-day forecast for SKU ID {sku_id} '
                        f'(code: {sku_code}). Use the available tools in order: '
                        'read historical data, run the forecast, then write results.'
                    ),
                }
            ]
        }
        config = {'recursion_limit': max(2, self.max_iterations * 2)}
        callbacks = get_langchain_callbacks()
        if callbacks:
            config['callbacks'] = callbacks

        agent_result = None
        started_at = time.time()
        try:
            agent_result = agent.invoke(agent_input, config=config)
        except Exception as exc:
            raise ForecastingAgentExecutionError(
                f'Forecasting agent failed for SKU {sku_code} (ID {sku_id}): {exc}'
            ) from exc
        finally:
            if trace_spans is not None:
                trace_spans.append(
                    {
                        'name': 'forecasting_agent_loop',
                        'input': agent_input,
                        'output': {
                            'observed_tools': sorted(observations.keys()),
                            'agent_result': agent_result,
                        },
                        'duration_ms': round((time.time() - started_at) * 1000),
                    }
                )

        write_key = self._tool_name(self.write_tool, 'forecast_db_write_tool')
        write_obs = observations.get(write_key, {})
        write_status = write_obs.get('status', 'success')

        return {
            'sku_id': sku_id,
            'sku_code': sku_code,
            'status': 'skipped' if write_status == 'skipped' else 'success',
            'observations': {k: self._summarize_observation(k, v) for k, v in observations.items()},
        }

    def _build_langchain_tools(
        self,
        sku_id: int,
        sku_code: str,
        trace_spans: list,
        observations: dict,
    ):
        def forecast_db_read_tool(sku_id: int, sku_code: str = '') -> dict:
            output = self._run_tool(
                self.read_tool, {'sku_id': sku_id, 'sku_code': sku_code or ''}, trace_spans
            )
            observations[self._tool_name(self.read_tool, 'forecast_db_read_tool')] = output
            return output

        def prophet_run_tool(sku_id: int, sku_code: str, data: list, periods: int = 30) -> dict:
            output = self._run_tool(
                self.prophet_tool,
                {'sku_id': sku_id, 'sku_code': sku_code or '', 'data': data, 'periods': periods},
                trace_spans,
            )
            observations[self._tool_name(self.prophet_tool, 'prophet_run_tool')] = output
            return output

        def forecast_db_write_tool(
            sku_id: int,
            sku_code: str,
            results: list,
            model_version: str,
            mae: float | None = None,
            mape: float | None = None,
        ) -> dict:
            output = self._run_tool(
                self.write_tool,
                {
                    'sku_id': sku_id,
                    'sku_code': sku_code or '',
                    'results': results,
                    'model_version': model_version or '',
                    'mae': mae,
                    'mape': mape,
                },
                trace_spans,
            )
            observations[self._tool_name(self.write_tool, 'forecast_db_write_tool')] = output
            return output

        return [
            StructuredTool.from_function(
                func=forecast_db_read_tool,
                name=self._tool_name(self.read_tool, 'forecast_db_read_tool'),
                description=getattr(self.read_tool, 'description', ''),
                args_schema=getattr(self.read_tool, 'args_schema', None),
            ),
            StructuredTool.from_function(
                func=prophet_run_tool,
                name=self._tool_name(self.prophet_tool, 'prophet_run_tool'),
                description=getattr(self.prophet_tool, 'description', ''),
                args_schema=getattr(self.prophet_tool, 'args_schema', None),
            ),
            StructuredTool.from_function(
                func=forecast_db_write_tool,
                name=self._tool_name(self.write_tool, 'forecast_db_write_tool'),
                description=getattr(self.write_tool, 'description', ''),
                args_schema=getattr(self.write_tool, 'args_schema', None),
            ),
        ]

    def _create_agent(self, tools):
        if self.agent_factory is not None:
            return self.agent_factory(
                model=self.llm,
                tools=tools,
                system_prompt=FORECASTING_AGENT_SYSTEM_PROMPT,
            )
        if create_agent is None:
            raise ForecastingAgentExecutionError('langchain.agents.create_agent is unavailable.')
        return create_agent(
            model=self._get_agent_model(),
            tools=tools,
            system_prompt=FORECASTING_AGENT_SYSTEM_PROMPT,
            name='forecasting_agent',
        )

    def _get_agent_model(self):
        if self.llm is not None:
            return self.llm
        from ai.llm.chain import get_llm

        self.llm = get_llm()
        return self.llm

    def _extract_sku_ids(self, context: dict) -> list[int]:
        if 'sku_id' in context:
            sid = context['sku_id']
            if sid is not None:
                return [int(sid)]
        if 'sku_ids' in context:
            sids = context['sku_ids']
            if sids is not None:
                return [int(sid) for sid in sids if sid is not None]
        skus = self.repo.get_all_skus()
        if isinstance(skus, QuerySet):
            return list(skus.values_list('id', flat=True))
        return [s.id for s in skus]

    @staticmethod
    def _tool_name(tool, fallback: str) -> str:
        return getattr(tool, 'name', fallback)

    @staticmethod
    def _summarize_observation(key: str, value: dict) -> dict:
        if not isinstance(value, dict):
            return {'raw': str(value)}
        summary = {
            k: v
            for k, v in value.items()
            if k
            in (
                'status',
                'has_data',
                'record_count',
                'model_version',
                'forecast_method',
                'records_written',
                'reason',
            )
        }
        if 'data' in value:
            summary['data_length'] = len(value['data'])
        if 'results' in value:
            summary['results_length'] = len(value['results'])
        return summary

    def _run_tool(self, tool, tool_input: dict, trace_spans: list):
        last_error = None
        for attempt in range(self.tool_retries + 1):
            started_at = time.time()
            try:
                fn = tool.invoke if hasattr(tool, 'invoke') else tool.run
                future = self.executor.submit(fn, tool_input)
                output = future.result(timeout=self.tool_timeout)
                if trace_spans is not None:
                    trace_spans.append(
                        {
                            'name': getattr(tool, 'name', tool.__class__.__name__),
                            'input': tool_input,
                            'output': output,
                            'attempt': attempt + 1,
                            'duration_ms': round((time.time() - started_at) * 1000),
                        }
                    )
                return output
            except Exception as exc:
                last_error = exc
                if trace_spans is not None:
                    trace_spans.append(
                        {
                            'name': getattr(tool, 'name', tool.__class__.__name__),
                            'input': tool_input,
                            'error': str(exc),
                            'attempt': attempt + 1,
                            'duration_ms': round((time.time() - started_at) * 1000),
                        }
                    )
                logger.warning(
                    'Forecasting tool %s failed on attempt %s: %s',
                    getattr(tool, 'name', tool.__class__.__name__),
                    attempt + 1,
                    exc,
                )
        raise ForecastingAgentExecutionError(
            f'Tool {getattr(tool, "name", tool.__class__.__name__)} failed after retries.'
        ) from last_error
