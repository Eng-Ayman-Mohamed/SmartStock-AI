import datetime
from decimal import Decimal

from django.test import TestCase

from apps.forecasting.models import ForecastResult, ReorderFlag
from apps.inventory.models import SKU, Category, Product, SalesRecord, StockLevel, Supplier
from apps.purchasing.models import PurchaseOrder
from apps.purchasing.workflow_models import PurchaseOrderWorkflow
from core.exceptions import (
    DuplicatePOError,
    ForecastingModelError,
    InsufficientStockError,
    StockNotFoundException,
    SupplierNotFoundException,
)


class EmptyDatabaseTests(TestCase):
    def test_empty_product_list(self):
        from apps.inventory.services import InventoryService

        result = InventoryService().get_all_products()
        self.assertEqual(result.count(), 0)

    def test_empty_sku_list(self):
        from apps.inventory.services import SKUService

        result = SKUService().get_all_skus()
        self.assertEqual(result.count(), 0)

    def test_empty_category_list(self):
        from apps.inventory.services import InventoryService

        result = InventoryService().get_all_categories()
        self.assertEqual(result.count(), 0)

    def test_empty_stock_levels(self):
        from apps.inventory.services import InventoryService

        result = InventoryService().get_all_stock_levels()
        self.assertEqual(result.count(), 0)

    def test_empty_forecast_results(self):
        from apps.forecasting.repositories import ForecastingRepository

        result = ForecastingRepository().get_all()
        self.assertEqual(result.count(), 0)


class UnicodeInputTests(TestCase):
    def test_unicode_category_name(self):
        cat = Category.objects.create(name='إلكترونيات')
        self.assertEqual(cat.name, 'إلكترونيات')

    def test_unicode_product_name(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='منتج اختباري', category=cat)
        self.assertEqual(product.name, 'منتج اختباري')
        self.assertEqual(Product.objects.get(pk=product.id).name, 'منتج اختباري')

    def test_unicode_supplier_name(self):
        supplier = Supplier.objects.create(
            name='Proveedor de prueba',
            contact_email='unicode@test.com',
        )
        self.assertEqual(supplier.name, 'Proveedor de prueba')

    def test_sku_code_ascii(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        sku = SKU.objects.create(product=product, code='UNI-001')
        self.assertEqual(sku.code, 'UNI-001')
        self.assertTrue(sku.code.isascii())

    def test_unicode_special_characters(self):
        supplier = Supplier.objects.create(
            name='Supplier <>&"\'',
            contact_email='special@test.com',
        )
        self.assertEqual(supplier.name, 'Supplier <>&"\'')


class SpecialCharacterTests(TestCase):
    def test_product_name_with_special_chars(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(
            name='Product @#$%^&*()_+',
            category=cat,
        )
        self.assertEqual(product.name, 'Product @#$%^&*()_+')

    def test_supplier_address_special_chars(self):
        supplier = Supplier.objects.create(
            name='Special',
            contact_email='spec@test.com',
            address='123 Main St, Suite #4\nNew York, NY 10001',
        )
        self.assertIn('Suite #4', supplier.address)


class NullValueTests(TestCase):
    def test_product_null_category(self):
        product = Product.objects.create(name='No Category')
        self.assertIsNone(product.category)
        self.assertEqual(product.category_id, None)

    def test_product_null_supplier(self):
        product = Product.objects.create(name='No Supplier')
        self.assertIsNone(product.supplier)
        self.assertEqual(product.supplier_id, None)

    def test_stock_level_quantity_reserved_default(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        sku = SKU.objects.create(product=product, code='NR-001')
        stock = StockLevel.objects.create(sku=sku)
        self.assertEqual(stock.quantity_reserved, 0)

    def test_product_unit_price_none(self):
        product = Product.objects.create(name='No Price')
        self.assertIsNone(product.unit_price)

    def test_purchase_order_null_fields(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        sku = SKU.objects.create(product=product, code='NF-001')
        supplier = Supplier.objects.create(name='Sup', contact_email='sup@test.com')
        po = PurchaseOrder.objects.create(
            sku=sku,
            supplier=supplier,
            quantity=10,
            total_cost=Decimal('100.00'),
            status='draft',
        )
        self.assertIsNone(po.approved_by)
        self.assertFalse(po.notes)
        self.assertIsNone(po.sent_at)


class InvalidIdTests(TestCase):
    def test_get_nonexistent_product(self):
        from apps.inventory.services import InventoryService

        with self.assertRaises(Product.DoesNotExist):
            InventoryService().get_product(999999)

    def test_get_nonexistent_stock_level(self):
        from apps.inventory.services import InventoryService

        with self.assertRaises(StockLevel.DoesNotExist):
            InventoryService().get_stock_level(999999)

    def test_get_nonexistent_supplier(self):
        from apps.inventory.services import InventoryService

        with self.assertRaises(Supplier.DoesNotExist):
            InventoryService().get_supplier(999999)

    def test_get_nonexistent_forecast(self):
        from apps.forecasting.repositories import ForecastingRepository

        with self.assertRaises(ForecastResult.DoesNotExist):
            ForecastingRepository().get_by_id(999999)


class TimezoneAwareDatetimeTests(TestCase):
    def test_forecast_result_created_at(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        sku = SKU.objects.create(product=product, code='TZ-001')
        fr = ForecastResult.objects.create(
            sku=sku,
            forecast_date=datetime.date.today(),
            predicted_quantity=10.0,
        )
        self.assertIsNotNone(fr.created_at)

    def test_reorder_flag_created_at(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        sku = SKU.objects.create(product=product, code='TZ-002')
        flag = ReorderFlag.objects.create(
            sku=sku,
            quantity_available=10,
            total_predicted_demand=50,
            reasoning='test',
            status='open',
        )
        self.assertIsNotNone(flag.created_at)

    def test_purchase_order_created_at(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        sku = SKU.objects.create(product=product, code='TZ-003')
        supplier = Supplier.objects.create(name='Sup', contact_email='sup@test.com')
        po = PurchaseOrder.objects.create(
            sku=sku,
            supplier=supplier,
            quantity=10,
            total_cost=Decimal('100.00'),
            status='draft',
        )
        self.assertIsNotNone(po.created_at)

    def test_workflow_created_at(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        sku = SKU.objects.create(product=product, code='TZ-004')
        supplier = Supplier.objects.create(name='Sup', contact_email='sup@test.com')
        po = PurchaseOrder.objects.create(
            sku=sku,
            supplier=supplier,
            quantity=10,
            total_cost=Decimal('100.00'),
            status='draft',
        )
        wf = PurchaseOrderWorkflow.objects.create(purchase_order=po)
        self.assertIsNotNone(wf.created_at)


class DecimalPrecisionTests(TestCase):
    def test_product_unit_price_precision(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(
            name='Precision',
            category=cat,
            unit_price=Decimal('19.99'),
        )
        product.refresh_from_db()
        self.assertEqual(product.unit_price, Decimal('19.99'))

    def test_purchase_order_total_cost_precision(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        sku = SKU.objects.create(product=product, code='DEC-001')
        supplier = Supplier.objects.create(name='Sup', contact_email='sup@test.com')
        po = PurchaseOrder.objects.create(
            sku=sku,
            supplier=supplier,
            quantity=10,
            total_cost=Decimal('1234.56'),
        )
        po.refresh_from_db()
        self.assertEqual(po.total_cost, Decimal('1234.56'))


class DuplicateRecordTests(TestCase):
    def test_duplicate_category_name_raises(self):
        Category.objects.create(name='Duplicate')
        with self.assertRaises(Exception):
            Category.objects.create(name='Duplicate')

    def test_duplicate_sku_code_raises(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        SKU.objects.create(product=product, code='DUP-001')
        with self.assertRaises(Exception):
            SKU.objects.create(product=product, code='DUP-001')

    def test_duplicate_sales_record_raises(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        sku = SKU.objects.create(product=product, code='DUP-SR-001')
        SalesRecord.objects.create(sku=sku, date=datetime.date.today(), quantity_sold=10)
        with self.assertRaises(Exception):
            SalesRecord.objects.create(sku=sku, date=datetime.date.today(), quantity_sold=20)


class LargeDatasetTests(TestCase):
    def test_bulk_create_sales_records(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        sku = SKU.objects.create(product=product, code='BULK-001')
        records = [
            {
                'sku': sku,
                'date': datetime.date(2025, 1, 1) + datetime.timedelta(days=i),
                'quantity_sold': i,
            }
            for i in range(100)
        ]
        SalesRecord.objects.bulk_create(
            [SalesRecord(**r) for r in records],
            ignore_conflicts=True,
        )
        self.assertEqual(SalesRecord.objects.filter(sku=sku).count(), 100)

    def test_many_products(self):
        cat = Category.objects.create(name='Bulk Test')
        for i in range(50):
            Product.objects.create(name=f'Product {i}', category=cat)
        self.assertEqual(Product.objects.filter(category=cat).count(), 50)


class CoreExceptionTests(TestCase):
    def test_stock_not_found_exception(self):
        exc = StockNotFoundException('test')
        self.assertEqual(str(exc), 'test')

    def test_insufficient_stock_error(self):
        exc = InsufficientStockError('not enough')
        self.assertEqual(str(exc), 'not enough')

    def test_duplicate_po_error(self):
        exc = DuplicatePOError('dup')
        self.assertEqual(str(exc), 'dup')

    def test_forecasting_model_error(self):
        exc = ForecastingModelError('model failed')
        self.assertEqual(str(exc), 'model failed')

    def test_supplier_not_found_exception(self):
        exc = SupplierNotFoundException('not found')
        self.assertEqual(str(exc), 'not found')


class ModelStringRepresentationTests(TestCase):
    def test_category_str(self):
        cat = Category.objects.create(name='Electronics')
        self.assertEqual(str(cat), 'Electronics')

    def test_product_str(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Widget', category=cat)
        self.assertEqual(str(product), 'Widget')

    def test_sku_str(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Widget', category=cat)
        sku = SKU.objects.create(product=product, code='SKU-001')
        self.assertEqual(str(sku), 'Widget - SKU-001')

    def test_stock_level_str(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Widget', category=cat)
        sku = SKU.objects.create(product=product, code='SKU-002')
        stock = StockLevel.objects.create(sku=sku, quantity_on_hand=50)
        self.assertEqual(str(stock), 'SKU-002: 50')

    def test_sales_record_str(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Widget', category=cat)
        sku = SKU.objects.create(product=product, code='SKU-003')
        sr = SalesRecord.objects.create(sku=sku, date=datetime.date.today(), quantity_sold=10)
        self.assertIn('SKU-003', str(sr))

    def test_supplier_str(self):
        supplier = Supplier.objects.create(name='Acme', contact_email='acme@test.com')
        self.assertEqual(str(supplier), 'Acme')

    def test_forecast_result_str(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Widget', category=cat)
        sku = SKU.objects.create(product=product, code='SKU-004')
        fr = ForecastResult.objects.create(
            sku=sku,
            forecast_date=datetime.date.today(),
            predicted_quantity=42.5,
        )
        self.assertIn('SKU-004', str(fr))
        self.assertIn('42.5', str(fr))

    def test_reorder_flag_str(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Widget', category=cat)
        sku = SKU.objects.create(product=product, code='SKU-005')
        flag = ReorderFlag.objects.create(
            sku=sku,
            quantity_available=10,
            total_predicted_demand=50,
            reasoning='test',
            status='open',
        )
        self.assertIn('SKU-005', str(flag))
        self.assertIn('open', str(flag))

    def test_purchase_order_str(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Widget', category=cat)
        sku = SKU.objects.create(product=product, code='SKU-006')
        supplier = Supplier.objects.create(name='Sup', contact_email='sup@test.com')
        po = PurchaseOrder.objects.create(
            sku=sku,
            supplier=supplier,
            quantity=10,
            total_cost=Decimal('100.00'),
            status='draft',
        )
        self.assertIn('PO-', str(po))
        self.assertIn('SKU-006', str(po))

    def test_workflow_str(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Widget', category=cat)
        sku = SKU.objects.create(product=product, code='SKU-007')
        supplier = Supplier.objects.create(name='Sup', contact_email='sup@test.com')
        po = PurchaseOrder.objects.create(
            sku=sku,
            supplier=supplier,
            quantity=10,
            total_cost=Decimal('100.00'),
            status='draft',
        )
        wf = PurchaseOrderWorkflow.objects.create(purchase_order=po)
        self.assertIn('Workflow for PO-', str(wf))


class StockLevelPropertyTests(TestCase):
    def test_quantity_available(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        sku = SKU.objects.create(product=product, code='PROP-001')
        stock = StockLevel.objects.create(
            sku=sku,
            quantity_on_hand=100,
            quantity_reserved=30,
        )
        self.assertEqual(stock.quantity_available, 70)

    def test_quantity_available_zero_reserved(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        sku = SKU.objects.create(product=product, code='PROP-002')
        stock = StockLevel.objects.create(sku=sku, quantity_on_hand=50)
        self.assertEqual(stock.quantity_available, 50)

    def test_quantity_available_over_reserved(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        sku = SKU.objects.create(product=product, code='PROP-003')
        stock = StockLevel.objects.create(
            sku=sku,
            quantity_on_hand=10,
            quantity_reserved=20,
        )
        self.assertEqual(stock.quantity_available, -10)


class InventoryRepositoryTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Test')
        self.supplier = Supplier.objects.create(
            name='Sup',
            contact_email='sup@test.com',
        )
        self.product = Product.objects.create(
            name='Widget',
            category=self.cat,
            supplier=self.supplier,
        )
        self.sku = SKU.objects.create(product=self.product, code='REP-001')
        self.stock = StockLevel.objects.create(
            sku=self.sku,
            quantity_on_hand=5,
            reorder_point=10,
        )

    def test_get_low_stock(self):
        from apps.inventory.repositories import StockLevelRepository

        low = StockLevelRepository().get_low_stock()
        self.assertIn(self.stock, low)

    def test_get_by_product_id(self):
        from apps.inventory.repositories import StockLevelRepository

        result = StockLevelRepository().get_by_product_id(self.product.id)
        self.assertEqual(result.id, self.stock.id)

    def test_get_by_product_id_no_sku(self):
        from apps.inventory.repositories import StockLevelRepository

        p = Product.objects.create(name='No SKU', category=self.cat)
        result = StockLevelRepository().get_by_product_id(p.id)
        self.assertIsNone(result)

    def test_adjust_stock_success(self):
        from apps.inventory.repositories import InventoryRepository

        result = InventoryRepository().adjust_stock(self.stock.id, 10)
        result.refresh_from_db()
        self.assertEqual(result.quantity_on_hand, 15)

    def test_adjust_stock_below_reserved(self):
        from apps.inventory.repositories import InventoryRepository

        self.stock.quantity_reserved = 100
        self.stock.save()
        with self.assertRaises(ValueError):
            InventoryRepository().adjust_stock(self.stock.id, -10)

    def test_soft_delete_product(self):
        from apps.inventory.repositories import InventoryRepository

        InventoryRepository().soft_delete(self.product.id)
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)

    def test_soft_delete_supplier(self):
        from apps.inventory.repositories import SupplierRepository

        SupplierRepository().soft_delete(self.supplier.id)
        self.supplier.refresh_from_db()
        self.assertFalse(self.supplier.is_active)

    def test_sales_record_bulk_create(self):
        from apps.inventory.repositories import SalesRecordRepository

        records = [
            {'sku': self.sku, 'date': datetime.date(2025, 1, 1), 'quantity_sold': 10},
        ]
        result = SalesRecordRepository().bulk_create(records)
        self.assertEqual(len(result), 1)


class ForecastingServiceEdgeTests(TestCase):
    def test_calculate_stockout_risk_no_stock(self):
        from apps.forecasting.services import ForecastingService

        result = ForecastingService().calculate_stockout_risk('NONEXISTENT')
        self.assertFalse(result)

    def test_get_dashboard_data_empty(self):
        from apps.forecasting.services import ForecastingService

        result = ForecastingService().get_dashboard_data()
        self.assertIn('skus', result)
        self.assertEqual(len(result['skus']), 0)


class PurchasingServiceEdgeTests(TestCase):
    def test_get_overdue_suppliers_none(self):
        from apps.purchasing.services import PurchasingService

        result = PurchasingService().get_overdue_suppliers()
        self.assertEqual(result, [])

    def test_mark_failed(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        sku = SKU.objects.create(product=product, code='FAIL-001')
        supplier = Supplier.objects.create(name='Sup', contact_email='sup@test.com')
        po = PurchaseOrder.objects.create(
            sku=sku,
            supplier=supplier,
            quantity=10,
            total_cost=Decimal('100.00'),
            status='sent',
        )
        from apps.purchasing.services import PurchasingService

        PurchasingService().mark_failed(po.id, 'test error')
        po.refresh_from_db()
        self.assertEqual(po.status, 'failed')

    def test_mark_timeout(self):
        cat = Category.objects.create(name='Test')
        product = Product.objects.create(name='Test', category=cat)
        sku = SKU.objects.create(product=product, code='TOUT-001')
        supplier = Supplier.objects.create(name='Sup', contact_email='sup@test.com')
        po = PurchaseOrder.objects.create(
            sku=sku,
            supplier=supplier,
            quantity=10,
            total_cost=Decimal('100.00'),
            status='sent',
        )
        from apps.purchasing.services import PurchasingService

        PurchasingService().mark_timeout(po.id)
        po.refresh_from_db()
        self.assertEqual(po.status, 'timeout')
