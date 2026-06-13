from ai.agents.base_agent import BaseTool
from apps.purchasing.services import PurchasingService


class DBUpdateTool(BaseTool):
    name = 'db_update_tool'
    description = 'Transitions a Purchase Order to a new status. Validates legal transitions.'

    def __init__(self, service=None):
        self.service = service or PurchasingService()

    def run(self, input: dict) -> dict:
        po_id = int(input['po_id'])
        new_status = input['status']
        po = self.service.transition_po_status(po_id, new_status)
        return {'po_id': po.id, 'status': po.status}
