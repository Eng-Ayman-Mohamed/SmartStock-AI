from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.authentication.models import CustomUser
from apps.forecasting.models import ForecastResult, ReorderFlag
from apps.forecasting.repositories import ForecastingRepository
from apps.forecasting.services import ForecastingService
from apps.inventory.models import Category, Product, SKU, SalesRecord, StockLevel, Supplier


class ForecastingServiceTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.supplier = Supplier.objects.create(
            name='Test Supplier', contact_email='test@supplier.com', default_lead_time_days=7
        )
        cls.category = Category.objects.create(name='Test Category')
        cls.product = Product.objects.create(
            name='Test Product', category=cls.category, supplier=cls.supplier, safety_stock=5,
        )
        cls.sku = SKU.objects.create(product=cls.product, code='FRC-SKU-001')
        cls.stock_level = StockLevel.objects.create(
            sku=cls.sku, quantity_on_hand=50, quantity_reserved=0,
            reorder_point=10, reorder_quantity=25,
        )


class ForecastingServiceGetForecastTest(ForecastingServiceTestBase):
    def setUp(self):
        self.repo = MagicMock(spec=ForecastingRepository)
        self.service = ForecastingService(repo=self.repo)

    def test_get_forecast_delegates_to_repo(self):
        mock_qs = MagicMock()
        self.repo.get_by_sku.return_value = mock_qs
        result = self.service.get_forecast(sku_id=self.sku.id)
        self.repo.get_by_sku.assert_called_once_with(self.sku.id)
        self.assertEqual(result, mock_qs)


class ForecastingServiceGetDecisionForecastDataTest(ForecastingServiceTestBase):
    def setUp(self):
        self.repo = MagicMock(spec=ForecastingRepository)
        self.service = ForecastingService(repo=self.repo)

    def test_with_forecasts(self):
        forecast = MagicMock(sku=MagicMock(code='SKU-1'), predicted_quantity=10.0)
        self.repo.get_next_for_product.return_value = [forecast]
        result = self.service.get_decision_forecast_data(product_id=self.product.id, forecast_days=7)
        self.assertEqual(result['sku_code'], 'SKU-1')
        self.assertEqual(result['total_predicted_demand'], 10.0)
        self.assertEqual(result['forecast_days'], 7)

    def test_without_forecasts_falls_back_to_primary_sku(self):
        self.repo.get_next_for_product.return_value = []
        self.repo.get_primary_sku_for_product.return_value = MagicMock(code='PRIMARY-SKU')
        result = self.service.get_decision_forecast_data(product_id=self.product.id)
        self.assertEqual(result['sku_code'], 'PRIMARY-SKU')
        self.assertEqual(result['total_predicted_demand'], 0)

    def test_no_forecasts_no_sku(self):
        self.repo.get_next_for_product.return_value = []
        self.repo.get_primary_sku_for_product.return_value = None
        result = self.service.get_decision_forecast_data(product_id=self.product.id)
        self.assertEqual(result['sku_code'], '')

    def test_forecast_days_zero_defaults_to_seven(self):
        self.repo.get_next_for_product.return_value = []
        self.repo.get_primary_sku_for_product.return_value = None
        result = self.service.get_decision_forecast_data(product_id=self.product.id, forecast_days=0)
        self.assertEqual(result['forecast_days'], 7)

    def test_forecast_days_none_defaults_to_seven(self):
        self.repo.get_next_for_product.return_value = []
        self.repo.get_primary_sku_for_product.return_value = None
        result = self.service.get_decision_forecast_data(product_id=self.product.id, forecast_days=None)
        self.assertEqual(result['forecast_days'], 7)


class ForecastingServicePersistReorderFlagTest(ForecastingServiceTestBase):
    def setUp(self):
        self.repo = MagicMock(spec=ForecastingRepository)
        self.service = ForecastingService(repo=self.repo)

    def test_persist_reorder_flag(self):
        self.repo.get_sku_by_code.return_value = MagicMock(id=1)
        self.repo.upsert_open_reorder_flag.return_value = MagicMock(id=10)
        decision = {
            'sku_code': 'SKU-1', 'quantity_available': 50, 'total_predicted_demand': 100.0,
            'safety_stock': 10, 'lead_time_days': 7, 'forecast_days': 30,
            'reorder_required': True, 'has_open_po': False, 'reasoning': 'Low stock',
        }
        result = self.service.persist_reorder_flag(decision)
        self.repo.get_sku_by_code.assert_called_once_with('SKU-1')
        self.repo.upsert_open_reorder_flag.assert_called_once()
        self.assertEqual(result.id, 10)


class ForecastingServiceCalculateStockoutRiskTest(ForecastingServiceTestBase):
    def setUp(self):
        self.repo = MagicMock(spec=ForecastingRepository)
        self.service = ForecastingService(repo=self.repo)

    def test_stockout_risk_true(self):
        forecast = MagicMock(predicted_quantity=100.0)
        self.repo.get_all.return_value.filter.return_value.order_by.return_value.__getitem__ = (
            lambda self_inner, x: [forecast]
        )
        result = self.service.calculate_stockout_risk(self.sku.code)
        self.assertTrue(result)

    def test_stockout_risk_false_when_sufficient_stock(self):
        forecast = MagicMock(predicted_quantity=1.0)
        self.repo.get_all.return_value.filter.return_value.order_by.return_value.__getitem__ = (
            lambda self_inner, x: [forecast]
        )
        result = self.service.calculate_stockout_risk(self.sku.code)
        self.assertFalse(result)

    def test_stockout_risk_false_on_exception(self):
        self.repo.get_all.side_effect = Exception('DB error')
        result = self.service.calculate_stockout_risk('NONEXISTENT')
        self.assertFalse(result)


class ForecastingServiceGetDashboardDataTest(ForecastingServiceTestBase):
    def setUp(self):
        self.repo = MagicMock(spec=ForecastingRepository)
        self.service = ForecastingService(repo=self.repo)

    @patch('apps.forecasting.services.cache')
    def test_returns_cached_data(self, mock_cache):
        cached_data = {'skus': []}
        mock_cache.get.return_value = cached_data
        result = self.service.get_dashboard_data()
        self.assertEqual(result, cached_data)
        mock_cache.get.assert_called_once_with('forecast_dashboard_data')

    @patch('apps.forecasting.services.cache')
    def test_computes_when_not_cached(self, mock_cache):
        mock_cache.get.return_value = None
        with patch.object(self.service, '_compute_dashboard', return_value={'skus': []}):
            result = self.service.get_dashboard_data()
            self.assertEqual(result, {'skus': []})
            mock_cache.set.assert_called_once_with(
                'forecast_dashboard_data', {'skus': []}, timeout=3600
            )


class ForecastingServiceComputeDashboardTest(ForecastingServiceTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        today = date.today()
        for i in range(5):
            ForecastResult.objects.create(
                sku=cls.sku, forecast_date=today + timedelta(days=i),
                predicted_quantity=10.0 + i, lower_bound=5.0, upper_bound=15.0,
                mae=1.0, mape=0.1, model_version='v1',
            )

    def setUp(self):
        self.repo = ForecastingRepository()
        self.service = ForecastingService(repo=self.repo)

    def test_compute_dashboard_returns_skus(self):
        result = self.service._compute_dashboard()
        self.assertIn('skus', result)
        self.assertEqual(len(result['skus']), 1)
        sku_data = result['skus'][0]
        self.assertEqual(sku_data['id'], 'FRC-SKU-001')
        self.assertEqual(sku_data['name'], 'Test Product')
        self.assertEqual(len(sku_data['days']), 5)
        self.assertIn('date', sku_data['days'][0])
        self.assertIn('demand', sku_data['days'][0])
