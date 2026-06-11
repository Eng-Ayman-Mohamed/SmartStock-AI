from unittest.mock import patch

from django.test import TestCase

from ai.llm.schemas import NLQueryFilters
from apps.inventory.models import SKU, Category, Product, StockLevel, Supplier
from apps.inventory.views import (
    NLQuerySerializer,
    _parse_condition,
)


class NLQuerySerializerTests(TestCase):
    def test_valid_query(self):
        s = NLQuerySerializer(data={'query': 'show me all products'})
        self.assertTrue(s.is_valid(), s.errors)

    def test_query_too_short(self):
        s = NLQuerySerializer(data={'query': 'ab'})
        self.assertFalse(s.is_valid())
        self.assertIn('query', s.errors)

    def test_query_too_long(self):
        s = NLQuerySerializer(data={'query': 'x' * 501})
        self.assertFalse(s.is_valid())
        self.assertIn('query', s.errors)

    def test_query_stripped(self):
        s = NLQuerySerializer(data={'query': '  hello  '})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['query'], 'hello')

    def test_missing_query(self):
        s = NLQuerySerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn('query', s.errors)


class ParseConditionTests(TestCase):
    def test_eq_operator(self):
        from django.db.models import Q

        q = _parse_condition({'field': 'name', 'operator': 'eq', 'value': 'Widget'})
        self.assertEqual(q, Q(name='Widget'))

    def test_neq_operator(self):
        from django.db.models import Q

        q = _parse_condition({'field': 'name', 'operator': 'neq', 'value': 'Widget'})
        self.assertEqual(q, ~Q(name='Widget'))

    def test_lt_operator(self):
        from django.db.models import Q

        q = _parse_condition({'field': 'unit_price', 'operator': 'lt', 'value': 10})
        self.assertEqual(q, Q(unit_price__lt=10))

    def test_lte_operator(self):
        from django.db.models import Q

        q = _parse_condition({'field': 'quantity_sold', 'operator': 'lte', 'value': 50})
        self.assertEqual(q, Q(quantity_sold__lte=50))

    def test_gt_operator(self):
        from django.db.models import Q

        q = _parse_condition({'field': 'quantity_sold', 'operator': 'gt', 'value': 10})
        self.assertEqual(q, Q(quantity_sold__gt=10))

    def test_gte_operator(self):
        from django.db.models import Q

        q = _parse_condition({'field': 'quantity_sold', 'operator': 'gte', 'value': 5})
        self.assertEqual(q, Q(quantity_sold__gte=5))

    def test_contains_operator(self):
        from django.db.models import Q

        q = _parse_condition({'field': 'name', 'operator': 'contains', 'value': 'wid'})
        self.assertEqual(q, Q(name__icontains='wid'))

    def test_in_operator(self):
        from django.db.models import Q

        q = _parse_condition({'field': 'name', 'operator': 'in', 'value': ['A', 'B']})
        self.assertEqual(q, Q(name__in=['A', 'B']))

    def test_in_operator_empty_list(self):
        from django.db.models import Q

        q = _parse_condition({'field': 'name', 'operator': 'in', 'value': []})
        self.assertEqual(q, Q(pk__in=[]))

    def test_not_in_operator(self):
        from django.db.models import Q

        q = _parse_condition({'field': 'name', 'operator': 'not_in', 'value': ['A']})
        self.assertEqual(q, ~Q(name__in=['A']))

    def test_field_alias_category(self):
        from django.db.models import Q

        q = _parse_condition({'field': 'category', 'operator': 'eq', 'value': 'Electronics'})
        self.assertEqual(q, Q(category__name='Electronics'))

    def test_field_alias_sku_code(self):
        from django.db.models import Q

        q = _parse_condition({'field': 'sku_code', 'operator': 'eq', 'value': 'SKU-001'})
        self.assertEqual(q, Q(skus__code='SKU-001'))


class BuildQFromFiltersTests(TestCase):
    def test_empty_conditions(self):
        from django.db.models import Q

        from apps.inventory.views import _build_q_from_filters

        filters = NLQueryFilters(conditions=[])
        q = _build_q_from_filters(filters)
        self.assertEqual(q, Q())

    def test_single_condition(self):
        from django.db.models import Q

        from apps.inventory.views import _build_q_from_filters

        filters = NLQueryFilters(
            conditions=[{'field': 'name', 'operator': 'eq', 'value': 'Widget'}],
        )
        q = _build_q_from_filters(filters)
        self.assertEqual(q, Q(name='Widget'))

    def test_and_conjunction(self):
        from django.db.models import Q

        from apps.inventory.views import _build_q_from_filters

        filters = NLQueryFilters(
            conditions=[
                {'field': 'name', 'operator': 'eq', 'value': 'Widget'},
                {'field': 'is_active', 'operator': 'eq', 'value': True},
            ],
        )
        q = _build_q_from_filters(filters)
        self.assertEqual(q, Q(name='Widget') & Q(is_active=True))


class ForecastingTasksTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.supplier = Supplier.objects.create(
            name='Task Supplier', contact_email='task@supplier.com', default_lead_time_days=7
        )
        cls.category = Category.objects.create(name='Task Category')
        cls.product = Product.objects.create(
            name='Task Product',
            category=cls.category,
            supplier=cls.supplier,
            safety_stock=5,
        )
        cls.sku = SKU.objects.create(product=cls.product, code='TASK-SKU-001')

    def test_run_forecast_for_all_skus(self):
        from apps.forecasting.tasks import run_forecast_for_all_skus

        with patch('apps.forecasting.services.ForecastingService.run_forecast') as mock_run:
            mock_run.return_value = [{'sku': 'TASK-SKU-001', 'status': 'skipped'}]
            result = run_forecast_for_all_skus()
            self.assertIn('1/1', result)

    def test_run_forecast_handles_failure(self):
        from apps.forecasting.tasks import run_forecast_for_all_skus

        with patch('apps.forecasting.services.ForecastingService.run_forecast') as mock_run:
            mock_run.side_effect = Exception('boom')
            result = run_forecast_for_all_skus()
            self.assertIn('0/1', result)


class InventoryServiceMethodTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.supplier = Supplier.objects.create(
            name='Svc Supplier', contact_email='svc@supplier.com', default_lead_time_days=7
        )
        cls.category = Category.objects.create(name='Svc Category')
        cls.product = Product.objects.create(
            name='Svc Product',
            category=cls.category,
            supplier=cls.supplier,
            safety_stock=5,
        )
        cls.sku = SKU.objects.create(product=cls.product, code='SVC-SKU-001')
        cls.stock_level = StockLevel.objects.create(
            sku=cls.sku,
            quantity_on_hand=50,
            quantity_reserved=0,
            reorder_point=10,
            reorder_quantity=25,
        )

    def test_get_all_categories(self):
        from apps.inventory.services import InventoryService

        result = InventoryService().get_all_categories()
        self.assertTrue(result.exists())

    def test_get_category(self):
        from apps.inventory.services import InventoryService

        result = InventoryService().get_category(self.category.id)
        self.assertEqual(result.id, self.category.id)

    def test_get_all_stock_levels(self):
        from apps.inventory.services import InventoryService

        result = InventoryService().get_all_stock_levels()
        self.assertTrue(result.exists())

    def test_get_stock_level(self):
        from apps.inventory.services import InventoryService

        result = InventoryService().get_stock_level(self.stock_level.id)
        self.assertEqual(result.id, self.stock_level.id)

    def test_get_all_suppliers(self):
        from apps.inventory.services import InventoryService

        result = InventoryService().get_all_suppliers()
        self.assertTrue(result.exists())

    def test_get_supplier(self):
        from apps.inventory.services import InventoryService

        result = InventoryService().get_supplier(self.supplier.id)
        self.assertEqual(result.id, self.supplier.id)

    def test_create_supplier(self):
        from apps.inventory.services import InventoryService

        data = {
            'name': 'New Supplier',
            'contact_email': 'new@supplier.com',
            'default_lead_time_days': 5,
        }
        result = InventoryService().create_supplier(data)
        self.assertIsNotNone(result.id)

    def test_update_supplier(self):
        from apps.inventory.services import InventoryService

        result = InventoryService().update_supplier(self.supplier.id, {'name': 'Updated'})
        self.assertEqual(result.name, 'Updated')

    def test_delete_supplier_no_open_pos(self):
        from apps.inventory.services import InventoryService

        s = Supplier.objects.create(
            name='Del', contact_email='del@sup.com', default_lead_time_days=1
        )
        InventoryService().delete_supplier(s.id)
        s.refresh_from_db()
        self.assertFalse(s.is_active)

    def test_find_stock_for_product(self):
        from apps.inventory.services import InventoryService

        result = InventoryService().find_stock_for_product(self.product.id)
        self.assertIsNotNone(result)

    def test_find_stock_for_product_none(self):
        from apps.inventory.services import InventoryService

        new_product = Product.objects.create(name='No Stock', category=self.category)
        result = InventoryService().find_stock_for_product(new_product.id)
        self.assertIsNone(result)

    def test_adjust_stock(self):
        from apps.inventory.services import InventoryService

        result = InventoryService().adjust_stock(self.stock_level.id, 10, user=None, reason='test')
        self.assertEqual(result.quantity_on_hand, 60)

    def test_filter_by_stock_status_in_stock(self):
        from apps.inventory.models import Product
        from apps.inventory.services import InventoryService

        qs = Product.objects.filter(id=self.product.id)
        result = InventoryService.filter_by_stock_status(qs, 'in_stock')
        self.assertTrue(result.exists())

    def test_filter_by_stock_status_low_stock(self):
        from apps.inventory.models import Product
        from apps.inventory.services import InventoryService

        self.stock_level.quantity_on_hand = 5
        self.stock_level.save()
        qs = Product.objects.filter(id=self.product.id)
        result = InventoryService.filter_by_stock_status(qs, 'low_stock')
        self.assertTrue(result.exists())

    def test_filter_by_stock_status_out_of_stock(self):
        from apps.inventory.models import Product
        from apps.inventory.services import InventoryService

        self.stock_level.quantity_on_hand = 0
        self.stock_level.save()
        qs = Product.objects.filter(id=self.product.id)
        result = InventoryService.filter_by_stock_status(qs, 'out_of_stock')
        self.assertTrue(result.exists())

    def test_filter_by_stock_status_unknown(self):
        from apps.inventory.models import Product
        from apps.inventory.services import InventoryService

        qs = Product.objects.filter(id=self.product.id)
        result = InventoryService.filter_by_stock_status(qs, 'unknown')
        self.assertTrue(result.exists())
