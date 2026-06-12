import logging

from ai.agents.base_agent import BaseTool
from apps.purchasing.services import PurchasingService

logger = logging.getLogger(__name__)


class PODraftTool(BaseTool):
    name = 'po_draft_tool'
    description = 'Generates a formal Purchase Order for a given SKU and quantity.'

    def __init__(self, service=None):
        self.service = service or PurchasingService()

    def run(self, input: dict) -> dict:
        try:
            sku_id = int(input['sku_id'])
            quantity = int(input['quantity'])
            supplier_id = int(input['supplier_id'])
            user_id = input.get('user_id')
            agent_reasoning = input.get('agent_reasoning', '')
            total_cost = input.get('total_cost', '0.00')

            data = {
                'sku_id': sku_id,
                'quantity': quantity,
                'supplier_id': supplier_id,
                'total_cost': total_cost,
                'status': 'draft',
            }
            if user_id is not None:
                data['requested_by_id'] = int(user_id)
            if agent_reasoning:
                data['agent_reasoning'] = agent_reasoning

            po = self.service.repo.create(data)
            logger.info('Draft PO created: PO-%s for SKU %s', po.id, sku_id)
            return {
                'po_id': po.id,
                'status': po.status,
                'sku_id': po.sku_id,
                'supplier_id': po.supplier_id,
                'quantity': po.quantity,
            }
        except Exception as e:
            logger.exception('PODraftTool failed')
            return {'po_id': None, 'status': 'failed', 'error': str(e)}
