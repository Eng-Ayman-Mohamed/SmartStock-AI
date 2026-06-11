from ai.agents.base_agent import BaseTool
from apps.purchasing.services import PurchasingService


class POStatusCheckTool(BaseTool):
    name = 'po_status_check_tool'
    description = 'Checks for open duplicate POs.'

    def __init__(self, service=None):
        self.service = service or PurchasingService()

    def run(self, input: dict) -> dict:
        product_id = int(input['product_id'])
        return self.service.get_open_po_status(product_id)
