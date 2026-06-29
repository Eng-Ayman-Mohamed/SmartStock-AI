from pydantic import BaseModel, Field

from ai.agents.base_agent import BaseTool
from apps.purchasing.services import PurchasingService


class POStatusCheckBySKUInput(BaseModel):
    sku_id: int = Field(..., description='SKU ID to check for open purchase orders.')


class POStatusCheckBySKUTool(BaseTool):
    name = 'po_status_check_by_sku_tool'
    description = 'Checks for open duplicate POs for a specific SKU.'
    args_schema = POStatusCheckBySKUInput

    def __init__(self, service=None):
        self.service = service or PurchasingService()

    def run(self, input: dict) -> dict:
        sku_id = int(input['sku_id'])
        return self.service.get_open_po_status_by_sku(sku_id)
