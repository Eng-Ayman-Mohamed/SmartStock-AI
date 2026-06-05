from django.core.cache import cache

from .repositories import InventoryRepository, StockLevelRepository


class InventoryService:
    def __init__(self):
        self.repo = InventoryRepository()
        self.stock_repo = StockLevelRepository()

    def get_low_stock_items(self):
        """Get low stock items (cached 5 min)."""
        cache_key = 'low_stock_items'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        low_stock = self.stock_repo.get_low_stock()
        result = [
            {
                'id': sl.id,
                'product_id': sl.sku.product.id,
                'product_name': sl.sku.product.name,
                'sku_code': sl.sku.code,
                'quantity': sl.quantity,
                'reorder_point': sl.reorder_point,
                'reorder_quantity': sl.reorder_quantity,
            }
            for sl in low_stock
        ]
        cache.set(cache_key, result, timeout=300)
        return result

    def adjust_stock(self, stock_level_id: int, quantity: int):
        """Update stock quantity and invalidate cache."""
        stock = self.stock_repo.update(stock_level_id, {'quantity': quantity})
        cache.delete('low_stock_items')
        return stock

    def create_product(self, data: dict):
        return self.repo.create(data)

    def update_product(self, product_id: int, data: dict):
        return self.repo.update(product_id, data)

    def delete_product(self, product_id: int):
        return self.repo.delete(product_id)
