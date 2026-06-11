from decimal import Decimal, InvalidOperation

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
    def __init__(self, repo=None, stock_repo=None, cat_repo=None, sku_repo=None, supplier_repo=None):
        self.repo = repo or InventoryRepository()
        self.stock_repo = stock_repo or StockLevelRepository()
        self.cat_repo = cat_repo or CategoryRepository()
        self.sku_repo = sku_repo or SKURepository()
        self.supplier_repo = supplier_repo or SupplierRepository()

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
            return queryset.filter(
                _available__lt=F('skus__stock_level__reorder_point'), _available__gt=0
            )
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

    def apply_confirmed_invoice(self, confirmed_data: dict, user=None) -> dict:
        sku_code = str(confirmed_data['sku_code']).strip().upper()
        product_name = str(confirmed_data['product_name']).strip()
        supplier_name = str(confirmed_data.get('supplier_name') or '').strip()
        quantity = self._parse_invoice_quantity(confirmed_data)
        unit_price = self._parse_invoice_price(confirmed_data.get('unit_price'))

        supplier = self.supplier_repo.get_by_name(supplier_name) if supplier_name else None
        sku = self.sku_repo.get_by_code(sku_code)

        if sku:
            product = sku.product
            stock = self.stock_repo.get_by_sku_id(sku.id)
            if stock:
                stock = self.stock_repo.update(
                    stock.id,
                    {'quantity_on_hand': stock.quantity_on_hand + quantity},
                )
            else:
                stock = self.stock_repo.create({'sku': sku, 'quantity_on_hand': quantity})
            updates = {}
            if unit_price is not None:
                updates['unit_price'] = unit_price
            if supplier is not None:
                updates['supplier'] = supplier
            if updates:
                product = self.repo.update(product.id, updates)
        else:
            product = self.repo.create(
                {
                    'name': product_name,
                    'supplier': supplier,
                    'unit_price': unit_price,
                }
            )
            sku = self.sku_repo.create({'product': product, 'code': sku_code})
            stock = self.stock_repo.create({'sku': sku, 'quantity_on_hand': quantity})

        _invalidate_product_cache()
        return {
            'product_id': product.id,
            'sku_id': sku.id,
            'stock_level_id': stock.id,
            'quantity_added': quantity,
            'quantity_on_hand': stock.quantity_on_hand,
        }

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
        return self.supplier_repo.get_all()

    def get_supplier(self, supplier_id: int):
        return self.supplier_repo.get_by_id(supplier_id)

    def create_supplier(self, data: dict):
        return self.supplier_repo.create(data)

    def update_supplier(self, supplier_id: int, data: dict):
        return self.supplier_repo.update(supplier_id, data)

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
        self.supplier_repo.soft_delete(supplier_id)

    def _parse_invoice_quantity(self, confirmed_data: dict) -> int:
        raw = confirmed_data.get('quantity_received', confirmed_data.get('quantity'))
        quantity = int(raw)
        if quantity < 1:
            raise ValidationError('Quantity received must be at least 1.')
        return quantity

    def _parse_invoice_price(self, raw):
        if raw in (None, ''):
            return None
        cleaned = str(raw).replace('$', '').replace(',', '').strip()
        try:
            value = Decimal(cleaned)
        except (InvalidOperation, ValueError) as exc:
            raise ValidationError('Unit price must be a valid decimal.') from exc
        if value < 0:
            raise ValidationError('Unit price cannot be negative.')
        return value.quantize(Decimal('0.01'))


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
