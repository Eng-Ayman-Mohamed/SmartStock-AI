import json
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ai.agents.purchasing_agent import PurchasingAgent
from ai.llm.chain import get_llm
from apps.forecasting.models import ReorderFlag
from apps.inventory.models import SKU

logger = logging.getLogger(__name__)

PO_CREATOR_PROMPT = """You are SmartStock AI's purchase order creator.

A reorder flag exists:
- SKU: {sku_code}
- Current stock: {quantity_available}
- Predicted demand (next {forecast_days}d): {total_predicted_demand}
- Safety stock: {safety_stock}
- Lead time: {lead_time_days}d
- Reasoning: {reasoning}

Available supplier(s):
{suppliers}

Choose the best supplier and the quantity to order.
Respond with valid JSON only (no markdown, no extra text):
{{"supplier_id": int, "quantity": int, "reasoning": "..."}}
"""


class POFromFlagCreator:
    def __init__(self, llm=None, purchasing_agent=None, system_user_id: int | None = None):
        self.llm = llm or get_llm()
        self.purchasing_agent = purchasing_agent or PurchasingAgent()
        self.system_user_id = system_user_id

    def process_flags(self, flags):
        results = {'created': 0, 'skipped_no_supplier': 0, 'failed': 0, 'errors': []}

        for flag in flags:
            try:
                result = self._process_single_flag(flag)
                if result['status'] == 'created':
                    results['created'] += 1
                elif result['status'] == 'skipped_no_supplier':
                    results['skipped_no_supplier'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(result.get('error', 'Unknown failure'))
            except Exception as e:
                logger.exception('Failed to process flag %s', flag.id)
                results['failed'] += 1
                results['errors'].append(str(e))

        return results

    def _process_single_flag(self, flag: ReorderFlag) -> dict:
        sku = SKU.objects.select_related('product__supplier').get(pk=flag.sku_id)
        supplier = sku.product.supplier

        if not supplier:
            logger.warning(
                'No supplier configured for SKU %s (flag id=%s), skipping',
                sku.code,
                flag.id,
            )
            return {'status': 'skipped_no_supplier', 'flag_id': flag.id}

        supplier_info = (
            f'- id={supplier.id}, name={supplier.name}, '
            f'lead_time={getattr(supplier, "default_lead_time_days", 7)}d'
        )
        if hasattr(supplier, 'contact_email') and supplier.contact_email:
            supplier_info += f', email={supplier.contact_email}'

        prompt = ChatPromptTemplate.from_messages(
            [
                ('system', PO_CREATOR_PROMPT),
                (
                    'user',
                    'Select supplier and quantity for SKU {sku_code} based on the flag data.',
                ),
            ]
        )
        chain = prompt | self.llm | StrOutputParser()

        raw = chain.invoke(
            {
                'sku_code': sku.code,
                'quantity_available': flag.quantity_available,
                'total_predicted_demand': flag.total_predicted_demand,
                'safety_stock': flag.safety_stock,
                'lead_time_days': flag.lead_time_days,
                'forecast_days': flag.forecast_days,
                'reasoning': flag.reasoning,
                'suppliers': supplier_info,
            }
        )

        try:
            decision = json.loads(raw)
        except json.JSONDecodeError:
            logger.error('PO creator LLM returned invalid JSON for flag %s: %s', flag.id, raw)
            return {'status': 'failed', 'flag_id': flag.id, 'error': 'LLM returned invalid JSON'}

        supplier_id = decision.get('supplier_id')
        quantity = decision.get('quantity')

        if not supplier_id or not quantity:
            logger.error('PO creator LLM missing supplier_id or quantity for flag %s', flag.id)
            return {
                'status': 'failed',
                'flag_id': flag.id,
                'error': 'LLM response missing supplier_id or quantity',
            }

        from decimal import Decimal

        from django.db import IntegrityError

        unit_price = sku.product.unit_price
        if unit_price is not None:
            total_cost = str(Decimal(int(quantity)) * unit_price)
        else:
            total_cost = '0.00'

        try:
            po_result = self.purchasing_agent.run(
                {
                    'sku_id': flag.sku_id,
                    'quantity': int(quantity),
                    'supplier_id': int(supplier_id),
                    'user_id': self.system_user_id,
                    'agent_reasoning': decision.get('reasoning', flag.reasoning),
                    'total_cost': total_cost,
                }
            )

            if po_result.get('status') == 'failed':
                logger.error(
                    'PurchasingAgent failed for flag %s: %s', flag.id, po_result.get('error')
                )
                return {
                    'status': 'failed',
                    'flag_id': flag.id,
                    'error': po_result.get('error', 'PurchasingAgent failed'),
                }

            flag.status = ReorderFlag.Status.CONSUMED
            flag.save(update_fields=['status'])
            logger.info(
                'PO created for flag %s (SKU %s), flag marked CONSUMED',
                flag.id,
                flag.sku_id,
            )
            return {
                'status': 'created',
                'flag_id': flag.id,
                'po_id': po_result.get('po_id'),
                'workflow_status': po_result.get('status'),
            }

        except IntegrityError:
            logger.warning('Duplicate PO for flag %s (SKU %s), skipping', flag.id, flag.sku_id)
            return {
                'status': 'failed',
                'flag_id': flag.id,
                'error': 'duplicate PO (IntegrityError)',
            }
        except Exception:
            logger.exception('Unexpected error processing flag %s', flag.id)
            return {'status': 'failed', 'flag_id': flag.id, 'error': 'unexpected error'}
