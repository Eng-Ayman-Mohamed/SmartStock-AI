from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.dispatch import Signal

from .repositories import (
    InventoryRepository,
    SKURepository,
    StockLevelRepository,
    SalesRecordRepository,
    SupplierRepository,
    CategoryRepository,
)

stock_adjusted = Signal()


def _invalidate_product_cache():
    cache.delete_pattern('product_list_*')
    cache.delete('low_stock_items')


class InventoryService:
    def __init__(self):
        self.repo = InventoryRepository()
        self.stock_repo = StockLevelRepository()
        self.cat_repo = CategoryRepository()

    def get_all_products(self, include_inactive: bool = False):
        return self.repo.get_all(include_inactive=include_inactive)

    def get_product(self, product_id: int):
        return self.repo.get_by_id(product_id)

    def create_product(self, data: dict):
        product = self.repo.create(data)
        _invalidate_product_cache()
        return product

    def update_product(self, product_id: int, data: dict):
        product = self.repo.update(product_id, data)
        _invalidate_product_cache()
        return product

    def delete_product(self, product_id: int):
        self.repo.soft_delete(product_id)
        _invalidate_product_cache()

    def find_stock_for_product(self, product_id: int):
        return self.stock_repo.get_by_product_id(product_id)

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
                'quantity': sl.quantity_on_hand,
                'reorder_point': sl.reorder_point,
                'reorder_quantity': sl.reorder_quantity,
            }
            for sl in low_stock
        ]
        cache.set(cache_key, result, timeout=300)
        return result

    @staticmethod
    def filter_by_stock_status(queryset, value):
        from django.db.models import F, Q
        if value == 'in_stock':
            return queryset.filter(
                skus__stock_level__quantity_on_hand__gte=F('skus__stock_level__reorder_point')
            )
        if value == 'low_stock':
            return queryset.filter(
                skus__stock_level__quantity_on_hand__lt=F('skus__stock_level__reorder_point'),
                skus__stock_level__quantity_on_hand__gt=0,
            )
        if value == 'out_of_stock':
            return queryset.filter(skus__stock_level__quantity_on_hand=0)
        return queryset

    def adjust_stock(self, stock_level_id: int, quantity_delta: int, user=None, reason: str = ''):
        stock = self.repo.adjust_stock(stock_level_id, quantity_delta)
        cache.delete('low_stock_items')
        stock_adjusted.send(
            sender=self, stock_level=stock, delta=quantity_delta,
            user=user, reason=reason,
        )
        return stock

    def get_all_categories(self):
        return self.cat_repo.get_all()

    def get_category(self, category_id: int):
        return self.cat_repo.get_by_id(category_id)

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

    def get_all_suppliers(self):
        return SupplierRepository().get_all()

    def get_supplier(self, supplier_id: int):
        return SupplierRepository().get_by_id(supplier_id)

    def create_supplier(self, data: dict):
        return SupplierRepository().create(data)

    def update_supplier(self, supplier_id: int, data: dict):
        return SupplierRepository().update(supplier_id, data)

    def delete_supplier(self, supplier_id: int):
        from apps.purchasing.models import PurchaseOrder
        open_statuses = [
            PurchaseOrder.Status.DRAFT,
            PurchaseOrder.Status.PENDING_APPROVAL,
            PurchaseOrder.Status.APPROVED,
            PurchaseOrder.Status.SENT,
        ]
        if PurchaseOrder.objects.filter(supplier_id=supplier_id, status__in=open_statuses).exists():
            raise ValidationError(
                "Cannot delete supplier with open purchase orders. "
                "Cancel or complete the pending POs first."
            )
        SupplierRepository().soft_delete(supplier_id)


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
