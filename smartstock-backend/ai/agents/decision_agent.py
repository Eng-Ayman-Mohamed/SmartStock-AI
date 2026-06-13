import json
import logging
import time

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool

from ai.agents.tools.forecast_read import ForecastReadTool
from ai.agents.tools.po_status_check import POStatusCheckTool
from ai.agents.tools.stock_level_read import StockLevelReadTool
from ai.observability.langfuse import (
    get_langchain_callbacks,
    invoke_with_langfuse,
    trace_agent_run,
)
from apps.forecasting.services import ForecastingService

try:
    from langchain.agents import create_agent
except Exception:
    create_agent = None

logger = logging.getLogger(__name__)

DECISION_AGENT_SYSTEM_PROMPT = """You are SmartStock AI's reorder decision agent.
Use the available tools to observe inventory state before deciding.

Process:
1. Read stock for the product with stock_level_read_tool.
2. Use the observed lead_time_days as forecast_days when calling forecast_read_tool.
3. Check open purchase orders with po_status_check_tool.
4. Stop after the required observations are gathered. Do not invent tool data.
"""


class DecisionAgentExecutionError(Exception):
    pass


class DecisionReasoner:
    """LLM-backed explanation generator for reorder decisions."""

    def __init__(self, llm=None):
        self.llm = llm

    def generate(self, payload: dict) -> str:
        try:
            llm = self.llm
            if llm is None:
                from ai.llm.chain import get_llm

                llm = get_llm()

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        'system',
                        'You explain warehouse reorder decisions in one concise sentence. '
                        'Use the exact numbers provided. Do not invent data.',
                    ),
                    (
                        'user',
                        'Decision data:\n{payload}\n\nExplain why reorder_required is true or false.',
                    ),
                ]
            )
            chain = prompt | llm | StrOutputParser()
            return invoke_with_langfuse(
                chain, {'payload': json.dumps(payload, default=str)}
            ).strip()
        except Exception:
            logger.exception('Decision reasoning generation failed')
            return (
                f'Current stock of {payload["quantity_available"]} units was compared with '
                f'predicted demand of {payload["total_predicted_demand"]} units over '
                f'{payload["lead_time_days"]} days plus safety stock of {payload["safety_stock"]} units.'
            )


class DecisionAgent:
    def __init__(
        self,
        stock_tool=None,
        forecast_tool=None,
        po_status_tool=None,
        forecasting_service=None,
        reasoner=None,
        llm=None,
        agent_factory=None,
        max_iterations: int = 8,
        tool_retries: int = 1,
    ):
        self.stock_tool = stock_tool or StockLevelReadTool()
        self.forecast_tool = forecast_tool or ForecastReadTool()
        self.po_status_tool = po_status_tool or POStatusCheckTool()
        self.forecasting_service = forecasting_service or ForecastingService()
        self.reasoner = reasoner or DecisionReasoner()
        self.llm = llm
        self.agent_factory = agent_factory
        self.max_iterations = max_iterations
        self.tool_retries = tool_retries

    def run(self, context: dict) -> dict:
        product_ids = self._extract_product_ids(context)
        trace_spans = []
        results = [
            self.evaluate_product(product_id, trace_spans=trace_spans) for product_id in product_ids
        ]
        output = {
            'agent': 'decision_agent',
            'results': results,
            'flags_created': sum(1 for item in results if item.get('reorder_flag_id')),
        }
        trace_agent_run('decision_agent', context, output, trace_spans)
        return output

    def evaluate_product(self, product_id: int, trace_spans: list | None = None) -> dict:
        observations, agent_result = self._observe_product(product_id, trace_spans)
        stock = observations[self._tool_name(self.stock_tool, 'stock_level_read_tool')]
        lead_time_days = stock.get('lead_time_days') or 7
        forecast = observations[self._tool_name(self.forecast_tool, 'forecast_read_tool')]
        po_status = observations[self._tool_name(self.po_status_tool, 'po_status_check_tool')]

        total_predicted = float(forecast.get('total_predicted_demand') or 0)
        safety_stock = int(stock.get('safety_stock') or 0)
        threshold = total_predicted + safety_stock
        formula_requires_reorder = stock['quantity_available'] < threshold
        has_open_po = bool(po_status['has_open_po'])
        reorder_required = formula_requires_reorder and not has_open_po

        decision = {
            'product_id': product_id,
            'sku_code': stock['sku_code'] or forecast.get('sku_code', ''),
            'quantity_available': stock['quantity_available'],
            'reorder_point': stock['reorder_point'],
            'lead_time_days': lead_time_days,
            'forecast_days': forecast.get('forecast_days') or lead_time_days,
            'total_predicted_demand': total_predicted,
            'safety_stock': safety_stock,
            'threshold': threshold,
            'has_open_po': has_open_po,
            'open_po_id': po_status.get('open_po_id'),
            'formula_requires_reorder': formula_requires_reorder,
            'reorder_required': reorder_required,
            'steps': {
                'plan': f'LangChain agent observed product {product_id} with inventory tools.',
                'execute': 'Agent selected stock, forecast, and purchase-order tools.',
                'verify': 'Tool observations were validated before computing the decision.',
                'decide': 'Applied quantity_available < total_predicted_demand + safety_stock.',
            },
            'agent_result': self._summarize_agent_result(agent_result),
        }
        decision['reasoning'] = self.reasoner.generate(decision)

        if reorder_required:
            flag = self.forecasting_service.persist_reorder_flag(decision)
            decision['reorder_flag_id'] = flag.id

        return {
            'sku_code': decision['sku_code'],
            'reorder_required': reorder_required,
            'reasoning': decision['reasoning'],
            **decision,
        }

    def _extract_product_ids(self, context: dict) -> list[int]:
        if 'product_id' in context:
            return [int(context['product_id'])]
        if 'product_ids' in context:
            return [int(product_id) for product_id in context['product_ids']]
        products = context.get('products') or []
        product_ids = []
        for product in products:
            if isinstance(product, dict) and 'product_id' in product:
                product_ids.append(int(product['product_id']))
        return product_ids

    def _observe_product(self, product_id: int, trace_spans: list | None):
        observations = {}
        tools = self._build_langchain_tools(product_id, trace_spans, observations)
        agent = self._create_agent(tools)
        agent_input = {
            'messages': [
                {
                    'role': 'user',
                    'content': (
                        f'Evaluate product_id={product_id}. Gather stock, demand forecast, '
                        'and open purchase order status using the available tools.'
                    ),
                }
            ]
        }
        config = {'recursion_limit': max(2, self.max_iterations * 2)}
        callbacks = get_langchain_callbacks()
        if callbacks:
            config['callbacks'] = callbacks

        started_at = time.time()
        try:
            result = agent.invoke(agent_input, config=config)
        except Exception as exc:
            raise DecisionAgentExecutionError(
                f'Decision agent failed for product {product_id}: {exc}'
            ) from exc
        finally:
            if trace_spans is not None:
                trace_spans.append(
                    {
                        'name': 'decision_agent_loop',
                        'input': agent_input,
                        'output': {'observed_tools': sorted(observations.keys())},
                        'duration_ms': round((time.time() - started_at) * 1000),
                    }
                )

        self._require_observations(observations)
        return observations, result

    def _build_langchain_tools(
        self,
        product_id: int,
        trace_spans: list | None,
        observations: dict,
    ):
        def stock_level_read_tool(product_id: int) -> dict:
            output = self._run_tool(self.stock_tool, {'product_id': product_id}, trace_spans)
            observations[self._tool_name(self.stock_tool, 'stock_level_read_tool')] = output
            return output

        def forecast_read_tool(product_id: int, forecast_days: int = 7) -> dict:
            output = self._run_tool(
                self.forecast_tool,
                {'product_id': product_id, 'forecast_days': forecast_days},
                trace_spans,
            )
            observations[self._tool_name(self.forecast_tool, 'forecast_read_tool')] = output
            return output

        def po_status_check_tool(product_id: int) -> dict:
            output = self._run_tool(
                self.po_status_tool,
                {'product_id': product_id},
                trace_spans,
            )
            observations[self._tool_name(self.po_status_tool, 'po_status_check_tool')] = output
            return output

        return [
            StructuredTool.from_function(
                func=stock_level_read_tool,
                name=self._tool_name(self.stock_tool, 'stock_level_read_tool'),
                description=getattr(self.stock_tool, 'description', ''),
                args_schema=getattr(self.stock_tool, 'args_schema', None),
            ),
            StructuredTool.from_function(
                func=forecast_read_tool,
                name=self._tool_name(self.forecast_tool, 'forecast_read_tool'),
                description=getattr(self.forecast_tool, 'description', ''),
                args_schema=getattr(self.forecast_tool, 'args_schema', None),
            ),
            StructuredTool.from_function(
                func=po_status_check_tool,
                name=self._tool_name(self.po_status_tool, 'po_status_check_tool'),
                description=getattr(self.po_status_tool, 'description', ''),
                args_schema=getattr(self.po_status_tool, 'args_schema', None),
            ),
        ]

    def _create_agent(self, tools):
        if self.agent_factory is not None:
            return self.agent_factory(
                model=self._get_agent_model(),
                tools=tools,
                system_prompt=DECISION_AGENT_SYSTEM_PROMPT,
            )
        if create_agent is None:
            raise DecisionAgentExecutionError('langchain.agents.create_agent is unavailable.')
        return create_agent(
            model=self._get_agent_model(),
            tools=tools,
            system_prompt=DECISION_AGENT_SYSTEM_PROMPT,
            name='decision_agent',
        )

    def _get_agent_model(self):
        if self.llm is not None:
            return self.llm
        from ai.llm.chain import get_llm

        self.llm = get_llm()
        return self.llm

    def _require_observations(self, observations: dict):
        missing = [
            name
            for name in (
                self._tool_name(self.stock_tool, 'stock_level_read_tool'),
                self._tool_name(self.forecast_tool, 'forecast_read_tool'),
                self._tool_name(self.po_status_tool, 'po_status_check_tool'),
            )
            if name not in observations
        ]
        if missing:
            raise DecisionAgentExecutionError(
                f'Decision agent did not collect required observations: {", ".join(missing)}'
            )

    def _tool_name(self, tool, fallback: str) -> str:
        return getattr(tool, 'name', fallback)

    def _summarize_agent_result(self, agent_result):
        if isinstance(agent_result, dict):
            if 'structured_response' in agent_result:
                return agent_result['structured_response']
            messages = agent_result.get('messages')
            if messages:
                last = messages[-1]
                return getattr(last, 'content', str(last))
        return str(agent_result)

    def _run_tool(self, tool, tool_input: dict, trace_spans: list | None):
        started_at = time.time()
        last_error = None
        for attempt in range(self.tool_retries + 1):
            try:
                output = (
                    tool.invoke(tool_input) if hasattr(tool, 'invoke') else tool.run(tool_input)
                )
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
                logger.warning(
                    'Decision tool %s failed on attempt %s: %s',
                    getattr(tool, 'name', tool.__class__.__name__),
                    attempt + 1,
                    exc,
                )
        if trace_spans is not None:
            trace_spans.append(
                {
                    'name': getattr(tool, 'name', tool.__class__.__name__),
                    'input': tool_input,
                    'error': str(last_error),
                    'duration_ms': round((time.time() - started_at) * 1000),
                }
            )
        raise DecisionAgentExecutionError(
            f'Tool {getattr(tool, "name", tool.__class__.__name__)} failed after retries.'
        ) from last_error
