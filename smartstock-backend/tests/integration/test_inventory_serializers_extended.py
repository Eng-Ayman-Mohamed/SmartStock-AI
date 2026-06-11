from decimal import Decimal

from django.test import TestCase

from apps.inventory.models import SKU, Category, Product, Supplier
from apps.inventory.serializers import (
    ProductWriteSerializer,
    SalesRecordSerializer,
    SKUSerializer,
    StockLevelSerializer,
    SupplierSerializer,
)


class ProductWriteSerializerTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test Cat')
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            contact_email='test@supplier.com',
            default_lead_time_days=5,
        )

    def test_valid_product_data(self):
        data = {
            'name': 'Good Product',
            'category': self.category.id,
            'supplier': self.supplier.id,
            'unit_price': Decimal('19.99'),
            'unit_of_measure': 'pcs',
            'reorder_point': 10,
            'safety_stock': 5,
        }
        s = ProductWriteSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_missing_name(self):
        data = {'category': self.category.id}
        s = ProductWriteSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('name', s.errors)

    def test_name_too_short(self):
        data = {'name': 'A', 'category': self.category.id}
        s = ProductWriteSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('name', s.errors)

    def test_name_too_long(self):
        data = {'name': 'x' * 256, 'category': self.category.id}
        s = ProductWriteSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('name', s.errors)

    def test_name_stripped(self):
        data = {'name': '  Clean Name  ', 'category': self.category.id}
        s = ProductWriteSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['name'], 'Clean Name')

    def test_negative_unit_price(self):
        data = {'name': 'Neg Price', 'category': self.category.id, 'unit_price': Decimal('-5.00')}
        s = ProductWriteSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('unit_price', s.errors)

    def test_too_many_decimal_places(self):
        data = {
            'name': 'Precise',
            'category': self.category.id,
            'unit_price': Decimal('1.999'),
        }
        s = ProductWriteSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('unit_price', s.errors)

    def test_null_unit_price_allowed(self):
        data = {'name': 'Free Stuff', 'category': self.category.id, 'unit_price': None}
        s = ProductWriteSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)


class SKUSerializerTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Test Product')

    def test_valid_sku_data(self):
        data = {'product': self.product.id, 'code': 'SKU-001'}
        s = SKUSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_code_format(self):
        data = {'product': self.product.id, 'code': 'invalid code!@#'}
        s = SKUSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('code', s.errors)

    def test_code_too_long(self):
        data = {'product': self.product.id, 'code': 'x' * 101}
        s = SKUSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('code', s.errors)

    def test_code_uppercased(self):
        data = {'product': self.product.id, 'code': 'lower-case'}
        s = SKUSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['code'], 'LOWER-CASE')


class StockLevelSerializerTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='SL Product')
        self.sku = SKU.objects.create(product=self.product, code='SL-SKU')

    def test_valid_stock_level(self):
        data = {
            'sku': self.sku.id,
            'quantity_on_hand': 100,
            'reorder_point': 10,
            'reorder_quantity': 25,
            'max_warehouse_capacity': 500,
        }
        s = StockLevelSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_negative_quantity_allowed(self):
        data = {
            'sku': self.sku.id,
            'quantity_on_hand': -5,
            'reorder_point': 10,
            'reorder_quantity': 25,
        }
        s = StockLevelSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_negative_reorder_point(self):
        data = {
            'sku': self.sku.id,
            'quantity_on_hand': 10,
            'reorder_point': -1,
            'reorder_quantity': 25,
        }
        s = StockLevelSerializer(data=data)
        self.assertFalse(s.is_valid())

    def test_reorder_quantity_zero(self):
        data = {
            'sku': self.sku.id,
            'quantity_on_hand': 10,
            'reorder_point': 5,
            'reorder_quantity': 0,
        }
        s = StockLevelSerializer(data=data)
        self.assertFalse(s.is_valid())


class SalesRecordSerializerTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='SR Product')
        self.sku = SKU.objects.create(product=self.product, code='SR-SKU')

    def test_valid_sales_record(self):
        data = {'sku': self.sku.id, 'date': '2026-01-15', 'quantity_sold': 20}
        s = SalesRecordSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_negative_quantity_sold(self):
        data = {'sku': self.sku.id, 'date': '2026-01-15', 'quantity_sold': -5}
        s = SalesRecordSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('quantity_sold', s.errors)

    def test_date_to_before_date_from(self):
        data = {
            'sku': self.sku.id,
            'date': '2026-01-15',
            'quantity_sold': 10,
            'date_from': '2026-01-20',
            'date_to': '2026-01-10',
        }
        s = SalesRecordSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('date_to', s.errors)


class SupplierSerializerTests(TestCase):
    def test_valid_supplier(self):
        data = {
            'name': 'Good Supplier',
            'contact_email': 'good@test.com',
            'default_lead_time_days': 7,
        }
        s = SupplierSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_missing_name(self):
        data = {'contact_email': 'x@test.com', 'default_lead_time_days': 5}
        s = SupplierSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('name', s.errors)

    def test_missing_email(self):
        data = {'name': 'No Email', 'default_lead_time_days': 5}
        s = SupplierSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('contact_email', s.errors)

    def test_name_too_long(self):
        data = {
            'name': 'x' * 256,
            'contact_email': 'long@test.com',
            'default_lead_time_days': 5,
        }
        s = SupplierSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('name', s.errors)

    def test_lead_time_too_low(self):
        data = {
            'name': 'Fast Supplier',
            'contact_email': 'fast@test.com',
            'default_lead_time_days': 0,
        }
        s = SupplierSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('default_lead_time_days', s.errors)

    def test_lead_time_too_high(self):
        data = {
            'name': 'Slow Supplier',
            'contact_email': 'slow@test.com',
            'default_lead_time_days': 400,
        }
        s = SupplierSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('default_lead_time_days', s.errors)
