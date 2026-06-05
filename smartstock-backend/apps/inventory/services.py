from .repositories import InventoryRepository
from .models import StockLevel


class InventoryService:
    def __init__(self):
        self.repo = InventoryRepository()

    def get_low_stock_items(self):
        stock_levels = StockLevel.objects.select_related('sku__product').all()
        return [
            {
                'product_id': sl.sku.product.id,
                'product_name': sl.sku.product.name,
                'sku_code': sl.sku.code,
                'quantity': sl.quantity,
                'reorder_point': sl.reorder_point,
                'reorder_quantity': sl.reorder_quantity,
            }
            for sl in stock_levels
            if sl.quantity < sl.reorder_point
        ]

    def update_stock(self, sku_id: int, quantity: int):
        stock, _ = StockLevel.objects.get_or_create(sku_id=sku_id)
        stock.quantity = quantity
        stock.save()
        return stock
