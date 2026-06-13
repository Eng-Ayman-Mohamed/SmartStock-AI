import logging

from ai.agents.base_agent import BaseTool
from apps.purchasing.services import PurchasingService

logger = logging.getLogger(__name__)


class ConfirmationListenerTool(BaseTool):
    name = 'confirmation_listener_tool'
    description = 'Polls for supplier confirmation of a sent Purchase Order.'

    def __init__(self, purchasing_service=None):
        self.purchasing_service = purchasing_service or PurchasingService()

    def run(self, input: dict) -> dict:
        try:
            po_id = int(input['po_id'])
            po = self.purchasing_service.repo.get_by_id(po_id)

            if po.status == 'confirmed':
                logger.info('PO-%s confirmed', po_id)
                return {'confirmed': True, 'po_id': po_id, 'status': 'confirmed'}

            if po.status in ('rejected', 'cancelled', 'failed', 'timeout'):
                logger.info('PO-%s in terminal status: %s', po_id, po.status)
                return {'confirmed': False, 'po_id': po_id, 'status': po.status, 'terminal': True}

            logger.info('PO-%s not yet confirmed (status=%s)', po_id, po.status)
            return {'confirmed': False, 'po_id': po_id, 'status': po.status}
        except Exception as e:
            logger.exception('ConfirmationListenerTool failed for PO-%s', input.get('po_id'))
            return {'confirmed': False, 'error': str(e)}
