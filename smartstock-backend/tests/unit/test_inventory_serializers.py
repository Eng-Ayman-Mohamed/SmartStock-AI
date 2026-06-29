from unittest.mock import MagicMock, PropertyMock, patch

from django.test import RequestFactory, TestCase
from rest_framework.exceptions import ValidationError

from apps.inventory.models import (
    Category,
    Product,
    SKU,
    SalesRecord,
    StockLevel,
    Supplier,
)
from apps.inventory.serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductSerializer,
    ProductWriteSerializer,
    SalesRecordSerializer,
    SKUSerializer,
    SKUCompactSerializer,
    StockLevelSerializer,
    SupplierSerializer,
)


# ---------------------------------------------------------------------------
# CategorySerializer
# ---------------------------------------------------------------------------

class CategorySerializerTest(TestCase):
    def test_valid_category(self):
        data = {'name': 'Electronics', 'description': 'Gadgets'}
        s = CategorySerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['name'], 'Electronics')

    def test_missing_name(self):
        s = CategorySerializer(data={'description': 'No name'})
        self.assertFalse(s.is_valid())
        self.assertIn('name', s.errors)

    def test_blank_name_rejected(self):
        s = CategorySerializer(data={'name': ''})
        self.assertFalse(s.is_valid())

    def test_representation(self):
        cat = Category(id=1, name='Food', description='Edible')
        s = CategorySerializer(cat)
        self.assertEqual(s.data['name'], 'Food')
        self.assertIn('created_at', s.data)


# ---------------------------------------------------------------------------
# SKUCompactSerializer
# ---------------------------------------------------------------------------

class SKUCompactSerializerTest(TestCase):
    def test_basic_fields(self):
        s = SKUCompactSerializer()
        self.assertIn('id', s.fields)
        self.assertIn('code', s.fields)
        self.assertIn('created_at', s.fields)

    def test_to_representation_with_stock_level(self):
        stock = MagicMock(spec=StockLevel)
        stock.id = 42
        stock.quantity_on_hand = 100
        stock.quantity_reserved = 10
        stock.reorder_point = 20

        sku = MagicMock(spec=SKU)
        sku.id = 1
        sku.code = 'SKU-001'
        sku.stock_level = stock

        s = SKUCompactSerializer(sku)
        data = s.data
        self.assertEqual(data['stock_level_id'], 42)
        self.assertEqual(data['quantity_on_hand'], 100)
        self.assertEqual(data['quantity_reserved'], 10)
        self.assertEqual(data['stock_reorder_point'], 20)

    def test_to_representation_without_stock_level(self):
        sku = MagicMock(spec=SKU)
        sku.id = 2
        sku.code = 'SKU-002'
        type(sku).stock_level = PropertyMock(
            side_effect=StockLevel.DoesNotExist
        )

        s = SKUCompactSerializer(sku)
        data = s.data
        self.assertIsNone(data['stock_level_id'])
        self.assertEqual(data['quantity_on_hand'], 0)
        self.assertEqual(data['quantity_reserved'], 0)
        self.assertIsNone(data['stock_reorder_point'])


# ---------------------------------------------------------------------------
# ProductSerializer / ProductListSerializer
# ---------------------------------------------------------------------------

class ProductSerializerTest(TestCase):
    def test_fields_include_skus(self):
        s = ProductSerializer()
        self.assertIn('skus', s.fields)
        self.assertIn('category_name', s.fields)
        self.assertIn('supplier_name', s.fields)


class ProductListSerializerTest(TestCase):
    def test_fields_exclude_description(self):
        s = ProductListSerializer()
        self.assertNotIn('description', s.fields)
        self.assertIn('id', s.fields)
        self.assertIn('name', s.fields)
        self.assertIn('unit_price', s.fields)
        self.assertIn('skus', s.fields)

    def test_category_name_field(self):
        s = ProductListSerializer()
        self.assertIn('category_name', s.fields)
        self.assertIn('supplier_name', s.fields)


# ---------------------------------------------------------------------------
# ProductWriteSerializer
# ---------------------------------------------------------------------------

class ProductWriteSerializerTest(TestCase):
    def test_valid_product(self):
        data = {
            'name': 'Widget',
            'unit_price': '9.99',
        }
        s = ProductWriteSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_id_is_read_only(self):
        s = ProductWriteSerializer()
        self.assertTrue(s.fields['id'].read_only)

    # -- validate_name -------------------------------------------------------
    def test_name_too_short(self):
        s = ProductWriteSerializer(data={'name': 'A'})
        self.assertFalse(s.is_valid())
        self.assertIn('name', s.errors)

    def test_name_strips_whitespace(self):
        s = ProductWriteSerializer(data={'name': '  Good Name  '})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['name'], 'Good Name')

    def test_name_max_length(self):
        s = ProductWriteSerializer(data={'name': 'x' * 256})
        self.assertFalse(s.is_valid())
        self.assertIn('name', s.errors)

    def test_name_exactly_2_chars(self):
        s = ProductWriteSerializer(data={'name': 'AB'})
        self.assertTrue(s.is_valid(), s.errors)

    # -- validate_unit_price -------------------------------------------------
    def test_unit_price_negative(self):
        s = ProductWriteSerializer(data={'name': 'X', 'unit_price': '-1'})
        self.assertFalse(s.is_valid())
        self.assertIn('unit_price', s.errors)

    def test_unit_price_zero(self):
        s = ProductWriteSerializer(data={'name': 'X', 'unit_price': '0'})
        self.assertTrue(s.is_valid(), s.errors)

    def test_unit_price_too_many_decimals(self):
        s = ProductWriteSerializer(data={'name': 'X', 'unit_price': '1.999'})
        self.assertFalse(s.is_valid())
        self.assertIn('unit_price', s.errors)

    def test_unit_price_exactly_2_decimals(self):
        s = ProductWriteSerializer(data={'name': 'X', 'unit_price': '1.99'})
        self.assertTrue(s.is_valid(), s.errors)

    def test_unit_price_none_allowed(self):
        s = ProductWriteSerializer(data={'name': 'X', 'unit_price': None})
        self.assertTrue(s.is_valid(), s.errors)

    def test_unit_price_integer(self):
        s = ProductWriteSerializer(data={'name': 'X', 'unit_price': '10'})
        self.assertTrue(s.is_valid(), s.errors)


# ---------------------------------------------------------------------------
# SKUSerializer
# ---------------------------------------------------------------------------

class SKUSerializerTest(TestCase):
    def test_valid_sku(self):
        s = SKUSerializer(data={'code': 'SKU-123', 'product': 1})
        self.assertTrue(s.is_valid(), s.errors)

    def test_code_uppercased(self):
        s = SKUSerializer(data={'code': 'abc-001', 'product': 1})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['code'], 'ABC-001')

    def test_code_too_long(self):
        s = SKUSerializer(data={'code': 'X' * 101, 'product': 1})
        self.assertFalse(s.is_valid())
        self.assertIn('code', s.errors)

    def test_code_invalid_chars(self):
        s = SKUSerializer(data={'code': 'SKU_ABC!', 'product': 1})
        self.assertFalse(s.is_valid())
        self.assertIn('code', s.errors)

    def test_code_with_hyphens_and_digits(self):
        s = SKUSerializer(data={'code': 'SKU-001-ABC', 'product': 1})
        self.assertTrue(s.is_valid(), s.errors)

    def test_code_exactly_100_chars(self):
        s = SKUSerializer(data={'code': 'A' * 100, 'product': 1})
        self.assertTrue(s.is_valid(), s.errors)

    def test_product_name_read_only(self):
        s = SKUSerializer()
        self.assertTrue(s.fields['product_name'].read_only)


# ---------------------------------------------------------------------------
# StockLevelSerializer
# ---------------------------------------------------------------------------

class StockLevelSerializerTest(TestCase):
    def test_valid_stock_level(self):
        s = StockLevelSerializer(
            data={'sku': 1, 'quantity_on_hand': 50, 'reorder_point': 10, 'reorder_quantity': 25}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_quantity_on_hand_negative(self):
        s = StockLevelSerializer(data={'sku': 1, 'quantity_on_hand': -1})
        self.assertFalse(s.is_valid())
        self.assertIn('quantity_on_hand', s.errors)

    def test_quantity_on_hand_zero(self):
        s = StockLevelSerializer(data={'sku': 1, 'quantity_on_hand': 0})
        self.assertTrue(s.is_valid(), s.errors)

    def test_reorder_point_negative(self):
        s = StockLevelSerializer(data={'sku': 1, 'quantity_on_hand': 0, 'reorder_point': -1})
        self.assertFalse(s.is_valid())
        self.assertIn('reorder_point', s.errors)

    def test_reorder_quantity_below_one(self):
        s = StockLevelSerializer(
            data={'sku': 1, 'quantity_on_hand': 0, 'reorder_quantity': 0}
        )
        self.assertFalse(s.is_valid())
        self.assertIn('reorder_quantity', s.errors)

    def test_reorder_quantity_exactly_one(self):
        s = StockLevelSerializer(
            data={'sku': 1, 'quantity_on_hand': 0, 'reorder_quantity': 1}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_quantity_available_property(self):
        sl = StockLevel(quantity_on_hand=100, quantity_reserved=30)
        self.assertEqual(sl.quantity_available, 70)

    def test_read_only_fields(self):
        s = StockLevelSerializer()
        self.assertTrue(s.fields['sku_code'].read_only)
        self.assertTrue(s.fields['product_name'].read_only)
        self.assertTrue(s.fields['quantity'].read_only)
        self.assertTrue(s.fields['quantity_available'].read_only)

    def test_reorder_point_exceeds_capacity(self):
        mock_product = MagicMock()
        mock_product.max_warehouse_capacity = 50

        mock_sku = MagicMock()
        mock_sku.product = mock_product

        instance = MagicMock(spec=StockLevel)
        instance.sku = mock_sku

        s = StockLevelSerializer(instance=instance, data={'reorder_point': 100})
        self.assertFalse(s.is_valid())
        self.assertIn('reorder_point', s.errors)

    def test_reorder_point_within_capacity(self):
        mock_product = MagicMock()
        mock_product.max_warehouse_capacity = 200

        mock_sku = MagicMock()
        mock_sku.product = mock_product

        instance = MagicMock(spec=StockLevel)
        instance.sku = mock_sku

        s = StockLevelSerializer(instance=instance, data={'reorder_point': 50, 'quantity_on_hand': 0})
        self.assertTrue(s.is_valid(), s.errors)

    def test_reorder_point_no_instance(self):
        s = StockLevelSerializer(data={'reorder_point': 50, 'quantity_on_hand': 0})
        self.assertTrue(s.is_valid(), s.errors)


# ---------------------------------------------------------------------------
# SalesRecordSerializer
# ---------------------------------------------------------------------------

class SalesRecordSerializerTest(TestCase):
    def test_valid_record(self):
        s = SalesRecordSerializer(
            data={'sku': 1, 'date': '2025-01-15', 'quantity_sold': 10}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_quantity_sold_negative(self):
        s = SalesRecordSerializer(
            data={'sku': 1, 'date': '2025-01-15', 'quantity_sold': -5}
        )
        self.assertFalse(s.is_valid())
        self.assertIn('quantity_sold', s.errors)

    def test_quantity_sold_zero(self):
        s = SalesRecordSerializer(
            data={'sku': 1, 'date': '2025-01-15', 'quantity_sold': 0}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_date_to_before_date_from(self):
        s = SalesRecordSerializer(
            data={
                'sku': 1,
                'date': '2025-01-15',
                'quantity_sold': 10,
                'date_from': '2025-06-01',
                'date_to': '2025-05-01',
            }
        )
        self.assertFalse(s.is_valid())
        self.assertIn('date_to', s.errors)

    def test_date_to_after_date_from(self):
        s = SalesRecordSerializer(
            data={
                'sku': 1,
                'date': '2025-01-15',
                'quantity_sold': 10,
                'date_from': '2025-05-01',
                'date_to': '2025-06-01',
            }
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_dates_not_required(self):
        s = SalesRecordSerializer(
            data={'sku': 1, 'date': '2025-01-15', 'quantity_sold': 10}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_only_date_from_no_error(self):
        s = SalesRecordSerializer(
            data={
                'sku': 1,
                'date': '2025-01-15',
                'quantity_sold': 10,
                'date_from': '2025-06-01',
            }
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_sku_code_read_only(self):
        s = SalesRecordSerializer()
        self.assertTrue(s.fields['sku_code'].read_only)

    def test_date_from_and_date_to_popped_from_validated(self):
        s = SalesRecordSerializer(
            data={
                'sku': 1,
                'date': '2025-01-15',
                'quantity_sold': 10,
                'date_from': '2025-06-01',
                'date_to': '2025-07-01',
            }
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertNotIn('date_from', s.validated_data)
        self.assertNotIn('date_to', s.validated_data)


# ---------------------------------------------------------------------------
# SupplierSerializer
# ---------------------------------------------------------------------------

class SupplierSerializerTest(TestCase):
    def test_valid_supplier(self):
        data = {
            'name': 'Acme Corp',
            'contact_email': 'acme@example.com',
        }
        s = SupplierSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_name_required(self):
        s = SupplierSerializer(data={'contact_email': 'a@b.com'})
        self.assertFalse(s.is_valid())
        self.assertIn('name', s.errors)

    def test_name_blank_rejected(self):
        s = SupplierSerializer(data={'name': '', 'contact_email': 'a@b.com'})
        self.assertFalse(s.is_valid())
        self.assertIn('name', s.errors)

    def test_contact_email_required(self):
        s = SupplierSerializer(data={'name': 'X'})
        self.assertFalse(s.is_valid())
        self.assertIn('contact_email', s.errors)

    # -- validate_name -------------------------------------------------------
    def test_name_too_long(self):
        s = SupplierSerializer(data={'name': 'x' * 256, 'contact_email': 'a@b.com'})
        self.assertFalse(s.is_valid())
        self.assertIn('name', s.errors)

    def test_name_exactly_255(self):
        s = SupplierSerializer(data={'name': 'x' * 255, 'contact_email': 'a@b.com'})
        self.assertTrue(s.is_valid(), s.errors)

    # -- validate_contact_email ----------------------------------------------
    def test_contact_email_lowercased_and_stripped(self):
        s = SupplierSerializer(data={'name': 'X', 'contact_email': '  FOO@BAR.COM  '})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['contact_email'], 'foo@bar.com')

    # -- validate_default_lead_time_days -------------------------------------
    def test_lead_time_too_low(self):
        s = SupplierSerializer(
            data={'name': 'X', 'contact_email': 'a@b.com', 'default_lead_time_days': 0}
        )
        self.assertFalse(s.is_valid())
        self.assertIn('default_lead_time_days', s.errors)

    def test_lead_time_too_high(self):
        s = SupplierSerializer(
            data={'name': 'X', 'contact_email': 'a@b.com', 'default_lead_time_days': 366}
        )
        self.assertFalse(s.is_valid())
        self.assertIn('default_lead_time_days', s.errors)

    def test_lead_time_valid(self):
        s = SupplierSerializer(
            data={'name': 'X', 'contact_email': 'a@b.com', 'default_lead_time_days': 7}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_lead_time_exactly_1(self):
        s = SupplierSerializer(
            data={'name': 'X', 'contact_email': 'a@b.com', 'default_lead_time_days': 1}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_lead_time_exactly_365(self):
        s = SupplierSerializer(
            data={'name': 'X', 'contact_email': 'a@b.com', 'default_lead_time_days': 365}
        )
        self.assertTrue(s.is_valid(), s.errors)

    # -- to_representation masking -------------------------------------------
    def _make_request(self, role, authenticated=True):
        factory = RequestFactory()
        request = factory.get('/')
        request.user = MagicMock()
        request.user.is_authenticated = authenticated
        request.user.role = role
        return request

    def test_masking_for_viewer(self):
        supplier = Supplier(
            id=1, name='Test', contact_email='test@example.com', contact_phone='555-1234'
        )
        ctx = {'request': self._make_request('viewer')}
        s = SupplierSerializer(supplier, context=ctx)
        data = s.data
        self.assertEqual(data['contact_email'], '***@***.***')
        self.assertEqual(data['contact_phone'], '***-***-****')

    def test_no_masking_for_admin(self):
        supplier = Supplier(
            id=1, name='Test', contact_email='test@example.com', contact_phone='555-1234'
        )
        ctx = {'request': self._make_request('admin')}
        s = SupplierSerializer(supplier, context=ctx)
        data = s.data
        self.assertEqual(data['contact_email'], 'test@example.com')
        self.assertEqual(data['contact_phone'], '555-1234')

    def test_no_masking_for_manager(self):
        supplier = Supplier(
            id=1, name='Test', contact_email='test@example.com', contact_phone='555-1234'
        )
        ctx = {'request': self._make_request('manager')}
        s = SupplierSerializer(supplier, context=ctx)
        data = s.data
        self.assertEqual(data['contact_email'], 'test@example.com')
        self.assertEqual(data['contact_phone'], '555-1234')

    def test_no_masking_when_unauthenticated(self):
        supplier = Supplier(
            id=1, name='Test', contact_email='test@example.com', contact_phone='555-1234'
        )
        ctx = {'request': self._make_request('viewer', authenticated=False)}
        s = SupplierSerializer(supplier, context=ctx)
        data = s.data
        self.assertEqual(data['contact_email'], 'test@example.com')
        self.assertEqual(data['contact_phone'], '555-1234')

    def test_no_masking_when_no_request_context(self):
        supplier = Supplier(
            id=1, name='Test', contact_email='test@example.com', contact_phone='555-1234'
        )
        s = SupplierSerializer(supplier, context={})
        data = s.data
        self.assertEqual(data['contact_email'], 'test@example.com')
        self.assertEqual(data['contact_phone'], '555-1234')

    def test_masking_with_none_phone(self):
        supplier = Supplier(
            id=1, name='Test', contact_email='test@example.com', contact_phone=None
        )
        ctx = {'request': self._make_request('viewer')}
        s = SupplierSerializer(supplier, context=ctx)
        data = s.data
        self.assertEqual(data['contact_email'], '***@***.***')
        self.assertIsNone(data['contact_phone'])

    def test_masking_with_none_email(self):
        supplier = Supplier(
            id=1, name='Test', contact_email=None, contact_phone='555-1234'
        )
        ctx = {'request': self._make_request('viewer')}
        s = SupplierSerializer(supplier, context=ctx)
        data = s.data
        self.assertIsNone(data['contact_email'])
        self.assertEqual(data['contact_phone'], '***-***-****')
