from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.dispatch import Signal

from .repositories import (
    CategoryRepository,
    InventoryRepository,
    SalesRecordRepository,
    SKURepository,
    StockLevelRepository,
    SupplierRepository,
)

stock_adjusted = Signal()


def _invalidate_product_cache():
    cache.delete_pattern('product_list_*')
    cache.delete('low_stock_items')


class InventoryService:
    def __init__(self, repo=None, stock_repo=None, cat_repo=None):
        self.repo = repo or InventoryRepository()
        self.stock_repo = stock_repo or StockLevelRepository()
        self.cat_repo = cat_repo or CategoryRepository()

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

    def get_decision_stock_data(self, product_id: int) -> dict:
        stock = self.find_stock_for_product(product_id)
        if stock is None:
            from core.exceptions import StockNotFoundException

            raise StockNotFoundException(f'No stock level found for product {product_id}.')

        product = stock.sku.product
        supplier = product.supplier
        lead_time_days = getattr(supplier, 'default_lead_time_days', None) or 7
        reorder_point = stock.reorder_point or product.reorder_point
        return {
            'product_id': product.id,
            'sku_code': stock.sku.code,
            'quantity_available': stock.quantity_available,
            'reorder_point': reorder_point,
            'lead_time_days': lead_time_days,
            'safety_stock': product.safety_stock,
        }

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
                'supplier_name': sl.sku.product.supplier.name if sl.sku.product.supplier else None,
            }
            for sl in low_stock
        ]
        cache.set(cache_key, result, timeout=300)
        return result

    @staticmethod
    def filter_by_stock_status(queryset, value):
        from django.db.models import F, IntegerField
        from django.db.models.expressions import ExpressionWrapper

        available = ExpressionWrapper(
            F('skus__stock_level__quantity_on_hand') - F('skus__stock_level__quantity_reserved'),
            output_field=IntegerField(),
        )
        queryset = queryset.annotate(_available=available)
        if value == 'in_stock':
            return queryset.filter(_available__gte=F('skus__stock_level__reorder_point'))
        if value == 'low_stock':
            return queryset.filter(_available__lt=F('skus__stock_level__reorder_point'), _available__gt=0)
        if value == 'out_of_stock':
            return queryset.filter(_available=0)
        return queryset

    def adjust_stock(self, stock_level_id: int, quantity_delta: int, user=None, reason: str = ''):
        stock = self.repo.adjust_stock(stock_level_id, quantity_delta)
        _invalidate_product_cache()
        stock_adjusted.send(
            sender=self,
            stock_level=stock,
            delta=quantity_delta,
            user=user,
            reason=reason,
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
                'Cannot delete supplier with open purchase orders. Cancel or complete the pending POs first.'
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
        sku = self.repo.create(data)
        _invalidate_product_cache()
        return sku

    def update_sku(self, sku_id: int, data: dict):
        sku = self.repo.update(sku_id, data)
        _invalidate_product_cache()
        return sku

    def delete_sku(self, sku_id: int):
        self.repo.delete(sku_id)
        _invalidate_product_cache()


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
