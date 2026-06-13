from pydantic import BaseModel, Field

from ai.agents.base_agent import BaseTool
from apps.purchasing.services import PurchasingService


class POStatusCheckInput(BaseModel):
    product_id: int = Field(..., description='Product ID to check for open purchase orders.')


class POStatusCheckTool(BaseTool):
    name = 'po_status_check_tool'
    description = 'Checks for open duplicate POs.'
    args_schema = POStatusCheckInput

    def __init__(self, service=None):
        self.service = service or PurchasingService()

    def run(self, input: dict) -> dict:
        product_id = int(input['product_id'])
        return self.service.get_open_po_status(product_id)
