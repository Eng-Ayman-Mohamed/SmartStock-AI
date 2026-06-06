from django.core.cache import cache

from .repositories import (
    InventoryRepository,
    SKURepository,
    StockLevelRepository,
    SalesRecordRepository,
)


PRODUCT_LIST_CACHE_KEY = 'product_list_{page}_{search}_{ordering}'


class InventoryService:
    def __init__(self):
        self.repo = InventoryRepository()
        self.stock_repo = StockLevelRepository()

    def get_all_products(self, request=None):
        if request:
            page = request.query_params.get('page', '1')
            search = request.query_params.get('search', '')
            ordering = request.query_params.get('ordering', '-created_at')
            cache_key = PRODUCT_LIST_CACHE_KEY.format(page=page, search=search, ordering=ordering)
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
        result = self.repo.get_all()
        if request:
            cache.set(cache_key, list(result), timeout=300)
        return result

    def get_product(self, product_id: int):
        return self.repo.get_by_id(product_id)

    def create_product(self, data: dict):
        result = self.repo.create(data)
        self._invalidate_product_cache()
        return result

    def update_product(self, product_id: int, data: dict):
        result = self.repo.update(product_id, data)
        self._invalidate_product_cache()
        return result

    def delete_product(self, product_id: int):
        self.repo.delete(product_id)
        self._invalidate_product_cache()

    def _invalidate_product_cache(self):
        cache.delete_pattern('product_list_*')

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

    def get_all_stock_levels(self):
        return self.stock_repo.get_all()

    def get_stock_level(self, stock_level_id: int):
        return self.stock_repo.get_by_id(stock_level_id)

    def create_stock_level(self, data: dict):
        return self.stock_repo.create(data)

    def update_stock_level(self, stock_level_id: int, data: dict):
        return self.stock_repo.update(stock_level_id, data)

    def delete_stock_level(self, stock_level_id: int):
        self.stock_repo.delete(stock_level_id)


class SKUService:
    def __init__(self):
        self.repo = SKURepository()

    def get_all_skus(self):
        return self.repo.get_all()

    def get_sku(self, sku_id: int):
        return self.repo.get_by_id(sku_id)

    def create_sku(self, data: dict):
        return self.repo.create(data)

    def update_sku(self, sku_id: int, data: dict):
        return self.repo.update(sku_id, data)

    def delete_sku(self, sku_id: int):
        self.repo.delete(sku_id)


class SalesRecordService:
    def __init__(self):
        self.repo = SalesRecordRepository()

    def get_all_sales_records(self):
        return self.repo.get_all()

    def get_sales_record(self, record_id: int):
        return self.repo.get_by_id(record_id)

    def create_sales_record(self, data: dict):
        return self.repo.create(data)

    def update_sales_record(self, record_id: int, data: dict):
        return self.repo.update(record_id, data)

    def delete_sales_record(self, record_id: int):
        self.repo.delete(record_id)
