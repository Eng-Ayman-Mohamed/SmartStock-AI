from ai.agents.base_agent import BaseTool
from apps.inventory.models import SKU
from apps.purchasing.po_number import generate_po_number
from apps.purchasing.services import PurchasingService


class PODraftTool(BaseTool):
    name = 'po_draft_tool'
    description = 'Creates a draft Purchase Order for a given product, quantity, and supplier.'

    def __init__(self, service=None):
        self.service = service or PurchasingService()

    def run(self, input: dict) -> dict:
        sku_id = int(input['sku_id'])
        quantity = int(input['quantity'])
        supplier_id = int(input['supplier_id'])
        po_number = generate_po_number()
        sku = SKU.objects.select_related('product').get(pk=sku_id)
        total_cost = round(quantity * sku.product.unit_price, 2)
        po = self.service.draft_po(
            sku_id=sku_id,
            quantity=quantity,
            supplier_id=supplier_id,
            user=None,
            po_number=po_number,
            total_cost=total_cost,
        )
        return {'po_id': po.id, 'po_number': po_number, 'status': 'draft'}
