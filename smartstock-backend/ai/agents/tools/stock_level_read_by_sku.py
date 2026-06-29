from pydantic import BaseModel, Field

from ai.agents.base_agent import BaseTool
from apps.inventory.services import InventoryService


class StockLevelReadBySKUInput(BaseModel):
    sku_id: int = Field(..., description='SKU ID to inspect stock levels for.')


class StockLevelReadBySKUTool(BaseTool):
    name = 'stock_level_read_by_sku_tool'
    description = (
        'Reads current stock, reorder point, lead time, and safety stock for a specific SKU.'
    )
    args_schema = StockLevelReadBySKUInput

    def __init__(self, service=None):
        self.service = service or InventoryService()

    def run(self, input: dict) -> dict:
        sku_id = int(input['sku_id'])
        return self.service.get_decision_stock_data_by_sku(sku_id)
