from pydantic import BaseModel, Field

from ai.agents.base_agent import BaseTool
from apps.inventory.services import InventoryService


class StockLevelReadInput(BaseModel):
    product_id: int = Field(..., description='Product ID to inspect.')


class StockLevelReadTool(BaseTool):
    name = 'stock_level_read_tool'
    description = 'Reads current stock, reorder point, lead time, and safety stock for a product.'
    args_schema = StockLevelReadInput

    def __init__(self, service=None):
        self.service = service or InventoryService()

    def run(self, input: dict) -> dict:
        product_id = int(input['product_id'])
        return self.service.get_decision_stock_data(product_id)
