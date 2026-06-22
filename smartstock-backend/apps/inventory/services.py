from decimal import Decimal, InvalidOperation

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models, transaction
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


_product_cache_version = 0


def _invalidate_product_cache():
    global _product_cache_version
    _product_cache_version += 1
    cache.delete_pattern('product_list_*')
    cache.delete('low_stock_items')


def get_product_cache_version() -> int:
    return _product_cache_version


class InventoryService:
    def __init__(
        self, repo=None, stock_repo=None, cat_repo=None, sku_repo=None, supplier_repo=None
    ):
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
        """Get low stock items (cached 5 min).

        Adds ``predicted_stockout_date`` — the estimated date when stock
        reaches zero based on trailing 30-day average daily demand.
        """
        from datetime import timedelta

        from django.utils import timezone

        from apps.inventory.models import SalesRecord

        cache_key = 'low_stock_items'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        low_stock = self.stock_repo.get_low_stock()
        sku_ids = [sl.sku_id for sl in low_stock]

        cutoff = timezone.localdate() - timedelta(days=30)
        demand_map = dict(
            SalesRecord.objects.filter(sku_id__in=sku_ids, date__gte=cutoff)
            .values('sku_id')
            .annotate(total=models.Sum('quantity_sold'))
            .values_list('sku_id', 'total')
        )

        result = []
        for sl in low_stock:
            total = demand_map.get(sl.sku_id, 0)
            avg_daily_demand = total / 30.0
            if avg_daily_demand > 0:
                days_left = sl.quantity_on_hand / avg_daily_demand
                predicted_stockout = timezone.localdate() + timedelta(days=int(days_left))
            else:
                predicted_stockout = None

            result.append(
                {
                    'id': sl.id,
                    'product_id': sl.sku.product.id,
                    'product_name': sl.sku.product.name,
                    'sku_code': sl.sku.code,
                    'quantity': sl.quantity_on_hand,
                    'reorder_point': sl.reorder_point,
                    'reorder_quantity': sl.reorder_quantity,
                    'supplier_name': (
                        sl.sku.product.supplier.name if sl.sku.product.supplier else None
                    ),
                    'predicted_stockout_date': (
                        predicted_stockout.isoformat() if predicted_stockout else None
                    ),
                }
            )
        cache.set(cache_key, result, timeout=300)
        return result

    @staticmethod
    def filter_by_stock_status(queryset, value):
        from django.db.models import F, IntegerField, Sum, Value
        from django.db.models.functions import Coalesce

        total_available = Coalesce(
            Sum(
                F('skus__stock_level__quantity_on_hand') - F('skus__stock_level__quantity_reserved')
            ),
            Value(0),
            output_field=IntegerField(),
        )
        queryset = queryset.annotate(_total_available=total_available)
        if value == 'in_stock':
            return queryset.filter(_total_available__gte=F('reorder_point'))
        if value == 'low_stock':
            return queryset.filter(_total_available__lt=F('reorder_point'), _total_available__gt=0)
        if value == 'out_of_stock':
            return queryset.filter(_total_available=0)
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

    @transaction.atomic
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

    @transaction.atomic
    def apply_confirmed_invoice_lines(self, header: dict, line_items: list, user=None) -> dict:
        """Apply every line item of a confirmed invoice, sharing one supplier header.

        Each line is delegated to the existing single-line ``apply_confirmed_invoice`` so
        behaviour stays identical. A line that fails validation is collected into
        ``lines_failed`` rather than aborting the whole batch; if every line fails the
        transaction is rolled back by re-raising.
        """
        supplier_name = str(header.get('supplier_name') or '').strip()
        lines = []
        lines_failed = []

        for line in line_items:
            single = {
                'product_name': line.get('item_name'),
                'sku_code': line.get('sku_code'),
                'quantity_received': line.get('quantity'),
                'unit_price': line.get('unit_price'),
                'supplier_name': supplier_name,
            }
            try:
                result = self.apply_confirmed_invoice(single, user=user)
            except ValidationError as exc:
                lines_failed.append(
                    {'sku_code': line.get('sku_code'), 'error': '; '.join(exc.messages)}
                )
                continue
            result['item_name'] = line.get('item_name')
            result['sku_code'] = line.get('sku_code')
            lines.append(result)

        if not lines and lines_failed:
            details = '; '.join(f'{item["sku_code"]}: {item["error"]}' for item in lines_failed)
            raise ValidationError(f'No invoice line items could be applied. {details}')

        return {
            'lines': lines,
            'lines_processed': len(lines),
            'lines_failed': lines_failed,
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
