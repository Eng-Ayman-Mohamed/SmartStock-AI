import json
import logging
import time

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ai.agents.tools.forecast_read import ForecastReadTool
from ai.agents.tools.po_status_check import POStatusCheckTool
from ai.agents.tools.stock_level_read import StockLevelReadTool
from ai.llm.chain import get_llm
from ai.observability.langfuse import invoke_with_langfuse, trace_agent_run
from apps.forecasting.services import ForecastingService

logger = logging.getLogger(__name__)


class DecisionReasoner:
    """LLM-backed explanation generator for reorder decisions."""

    def __init__(self, llm=None):
        self.llm = llm

    def generate(self, payload: dict) -> str:
        try:
            llm = self.llm
            if llm is None:
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
    ):
        self.stock_tool = stock_tool or StockLevelReadTool()
        self.forecast_tool = forecast_tool or ForecastReadTool()
        self.po_status_tool = po_status_tool or POStatusCheckTool()
        self.forecasting_service = forecasting_service or ForecastingService()
        self.reasoner = reasoner or DecisionReasoner()

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
        plan = f'Read stock, forecast demand, and open PO status for product {product_id}.'
        stock = self._run_tool(
            self.stock_tool,
            {'product_id': product_id},
            trace_spans,
        )
        lead_time_days = stock.get('lead_time_days') or 7
        forecast = self._run_tool(
            self.forecast_tool,
            {
                'product_id': product_id,
                'forecast_days': lead_time_days,
            },
            trace_spans,
        )
        po_status = self._run_tool(self.po_status_tool, {'product_id': product_id}, trace_spans)

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
                'plan': plan,
                'execute': 'Called stock level and forecast read tools.',
                'verify': 'Checked for open non-terminal purchase orders.',
                'decide': 'Applied quantity_available < total_predicted_demand + safety_stock.',
            },
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

    def _run_tool(self, tool, tool_input: dict, trace_spans: list | None):
        started_at = time.time()
        output = tool.run(tool_input)
        if trace_spans is not None:
            trace_spans.append(
                {
                    'name': getattr(tool, 'name', tool.__class__.__name__),
                    'input': tool_input,
                    'output': output,
                    'duration_ms': round((time.time() - started_at) * 1000),
                }
            )
        return output
