from ai.agents.base_agent import BaseTool
from apps.inventory.services import InventoryService


class StockLevelReadTool(BaseTool):
    name = 'stock_level_read_tool'
    description = 'Reads current stock, reorder point, lead time, and safety stock for a product.'

    def __init__(self, service=None):
        self.service = service or InventoryService()

    def run(self, input: dict) -> dict:
        product_id = int(input['product_id'])
        return self.service.get_decision_stock_data(product_id)
