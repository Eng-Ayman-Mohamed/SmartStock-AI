from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.forecasting.models import ForecastResult
from apps.forecasting.repositories import ForecastingRepository
from apps.forecasting.services import (
    DASHBOARD_CACHE_VERSION,
    ForecastingService,
)
from apps.inventory.models import SKU, Category, Product, StockLevel, Supplier


class ForecastingServiceTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.supplier = Supplier.objects.create(
            name='Test Supplier', contact_email='test@supplier.com', default_lead_time_days=7
        )
        cls.category = Category.objects.create(name='Test Category')
        cls.product = Product.objects.create(
            name='Test Product',
            category=cls.category,
            supplier=cls.supplier,
            safety_stock=5,
        )
        cls.sku = SKU.objects.create(product=cls.product, code='FRC-SKU-001')
        cls.stock_level = StockLevel.objects.create(
            sku=cls.sku,
            quantity_on_hand=50,
            quantity_reserved=0,
            reorder_point=10,
            reorder_quantity=25,
        )


class ForecastingServiceInitTest(TestCase):
    def test_default_init_creates_repo_and_engine(self):
        svc = ForecastingService()
        self.assertIsNotNone(svc.repo)
        self.assertIsNotNone(svc.engine)

    def test_custom_init(self):
        mock_repo = MagicMock()
        mock_engine = MagicMock()
        svc = ForecastingService(repo=mock_repo, engine=mock_engine)
        self.assertIs(svc.repo, mock_repo)
        self.assertIs(svc.engine, mock_engine)


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


class ForecastingServiceGetForecastBySkuCodeOrIdTest(ForecastingServiceTestBase):
    def setUp(self):
        self.repo = MagicMock(spec=ForecastingRepository)
        self.service = ForecastingService(repo=self.repo)

    def test_delegates_to_repo(self):
        mock_qs = MagicMock()
        self.repo.get_by_sku_code_or_id.return_value = mock_qs
        result = self.service.get_forecast_by_sku_code_or_id('SKU-CODE')
        self.repo.get_by_sku_code_or_id.assert_called_once_with('SKU-CODE')
        self.assertEqual(result, mock_qs)

    def test_numeric_string_uses_sku_id(self):
        self.repo.get_by_sku_code_or_id.return_value = []
        self.service.get_forecast_by_sku_code_or_id('123')
        self.repo.get_by_sku_code_or_id.assert_called_once_with('123')


class ForecastingServiceGetDecisionForecastDataTest(ForecastingServiceTestBase):
    def setUp(self):
        self.repo = MagicMock(spec=ForecastingRepository)
        self.service = ForecastingService(repo=self.repo)

    def test_with_forecasts(self):
        forecast = MagicMock(sku=MagicMock(code='SKU-1'), predicted_quantity=10.0)
        self.repo.get_next_for_product.return_value = [forecast]
        result = self.service.get_decision_forecast_data(
            product_id=self.product.id, forecast_days=7
        )
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
        result = self.service.get_decision_forecast_data(
            product_id=self.product.id, forecast_days=0
        )
        self.assertEqual(result['forecast_days'], 7)

    def test_forecast_days_none_defaults_to_seven(self):
        self.repo.get_next_for_product.return_value = []
        self.repo.get_primary_sku_for_product.return_value = None
        result = self.service.get_decision_forecast_data(
            product_id=self.product.id, forecast_days=None
        )
        self.assertEqual(result['forecast_days'], 7)

    def test_multiple_forecasts_summed(self):
        f1 = MagicMock(sku=MagicMock(code='SKU-1'), predicted_quantity=10.0)
        f2 = MagicMock(sku=MagicMock(code='SKU-1'), predicted_quantity=20.0)
        self.repo.get_next_for_product.return_value = [f1, f2]
        result = self.service.get_decision_forecast_data(
            product_id=self.product.id, forecast_days=7
        )
        self.assertEqual(result['total_predicted_demand'], 30.0)

    def test_forecast_with_none_predicted_quantity(self):
        f1 = MagicMock(sku=MagicMock(code='SKU-1'), predicted_quantity=None)
        self.repo.get_next_for_product.return_value = [f1]
        result = self.service.get_decision_forecast_data(
            product_id=self.product.id, forecast_days=7
        )
        self.assertEqual(result['total_predicted_demand'], 0.0)


class ForecastingServiceGetDecisionForecastDataBySkuTest(ForecastingServiceTestBase):
    def setUp(self):
        self.repo = MagicMock(spec=ForecastingRepository)
        self.service = ForecastingService(repo=self.repo)

    def test_with_forecasts(self):
        forecast = MagicMock(sku=MagicMock(code='SKU-1'), predicted_quantity=15.0)
        self.repo.get_next_for_sku.return_value = [forecast]
        result = self.service.get_decision_forecast_data_by_sku(sku_id=self.sku.id, forecast_days=7)
        self.assertEqual(result['sku_id'], self.sku.id)
        self.assertEqual(result['sku_code'], 'SKU-1')
        self.assertEqual(result['total_predicted_demand'], 15.0)
        self.assertEqual(result['forecast_days'], 7)
        self.repo.get_next_for_sku.assert_called_once_with(self.sku.id, 7)

    def test_without_forecasts_falls_back_to_get_sku(self):
        self.repo.get_next_for_sku.return_value = []
        self.repo.get_sku.return_value = MagicMock(code='FALLBACK-SKU')
        result = self.service.get_decision_forecast_data_by_sku(sku_id=self.sku.id)
        self.assertEqual(result['sku_code'], 'FALLBACK-SKU')
        self.assertEqual(result['total_predicted_demand'], 0)

    def test_no_forecasts_no_sku(self):
        self.repo.get_next_for_sku.return_value = []
        self.repo.get_sku.return_value = None
        result = self.service.get_decision_forecast_data_by_sku(sku_id=999)
        self.assertEqual(result['sku_code'], '')

    def test_forecast_days_zero_defaults_to_seven(self):
        self.repo.get_next_for_sku.return_value = []
        self.repo.get_sku.return_value = None
        result = self.service.get_decision_forecast_data_by_sku(sku_id=1, forecast_days=0)
        self.assertEqual(result['forecast_days'], 7)

    def test_forecast_days_none_defaults_to_seven(self):
        self.repo.get_next_for_sku.return_value = []
        self.repo.get_sku.return_value = None
        result = self.service.get_decision_forecast_data_by_sku(sku_id=1, forecast_days=None)
        self.assertEqual(result['forecast_days'], 7)

    def test_multiple_forecasts_summed(self):
        f1 = MagicMock(sku=MagicMock(code='SKU-1'), predicted_quantity=12.0)
        f2 = MagicMock(sku=MagicMock(code='SKU-1'), predicted_quantity=18.0)
        self.repo.get_next_for_sku.return_value = [f1, f2]
        result = self.service.get_decision_forecast_data_by_sku(sku_id=self.sku.id, forecast_days=7)
        self.assertEqual(result['total_predicted_demand'], 30.0)


class ForecastingServicePersistReorderFlagTest(ForecastingServiceTestBase):
    def setUp(self):
        self.repo = MagicMock(spec=ForecastingRepository)
        self.service = ForecastingService(repo=self.repo)

    def test_persist_with_sku_code(self):
        self.repo.get_sku_by_code.return_value = MagicMock(id=1)
        self.repo.upsert_open_reorder_flag.return_value = MagicMock(id=10)
        decision = {
            'sku_code': 'SKU-1',
            'quantity_available': 50,
            'total_predicted_demand': 100.0,
            'safety_stock': 10,
            'lead_time_days': 7,
            'forecast_days': 30,
            'reorder_required': True,
            'has_open_po': False,
            'reasoning': 'Low stock',
        }
        result = self.service.persist_reorder_flag(decision)
        self.repo.get_sku_by_code.assert_called_once_with('SKU-1')
        self.repo.upsert_open_reorder_flag.assert_called_once()
        self.assertEqual(result.id, 10)

    def test_persist_with_sku_id(self):
        self.repo.get_sku.return_value = MagicMock(id=42)
        self.repo.upsert_open_reorder_flag.return_value = MagicMock(id=20)
        decision = {
            'sku_id': 42,
            'quantity_available': 10,
            'total_predicted_demand': 5.0,
            'safety_stock': 2,
            'lead_time_days': 5,
            'forecast_days': 14,
            'reorder_required': True,
            'has_open_po': True,
            'open_po_id': 7,
            'reasoning': 'Reorder needed',
        }
        self.service.persist_reorder_flag(decision)
        self.repo.get_sku.assert_called_once_with(42)
        self.repo.get_sku_by_code.assert_not_called()
        call_kwargs = self.repo.upsert_open_reorder_flag.call_args
        self.assertEqual(call_kwargs[1]['data']['open_po_id'], 7)
        self.assertEqual(call_kwargs[1]['data']['has_open_po'], True)

    def test_persist_without_open_po_id(self):
        self.repo.get_sku_by_code.return_value = MagicMock(id=5)
        self.repo.upsert_open_reorder_flag.return_value = MagicMock(id=15)
        decision = {
            'sku_code': 'SKU-5',
            'quantity_available': 20,
            'total_predicted_demand': 30.0,
            'safety_stock': 5,
            'lead_time_days': 7,
            'forecast_days': 30,
            'reorder_required': False,
            'has_open_po': False,
            'reasoning': 'Stock OK',
        }
        self.service.persist_reorder_flag(decision)
        call_kwargs = self.repo.upsert_open_reorder_flag.call_args
        self.assertIsNone(call_kwargs[1]['data']['open_po_id'])


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

    def test_stockout_risk_does_not_exist(self):
        result = self.service.calculate_stockout_risk('NONEXISTENT')
        self.assertFalse(result)

    def test_stockout_risk_generic_exception(self):
        self.repo.get_all.side_effect = Exception('DB error')
        result = self.service.calculate_stockout_risk(self.sku.code)
        self.assertFalse(result)

    def test_stockout_risk_supplier_no_lead_time(self):
        no_lead_supplier = Supplier.objects.create(
            name='No Lead Supplier', contact_email='no@lead.com'
        )
        product = Product.objects.create(
            name='No Lead Product',
            category=self.category,
            supplier=no_lead_supplier,
            safety_stock=0,
        )
        sku = SKU.objects.create(product=product, code='NO-LEAD-SKU')
        StockLevel.objects.create(
            sku=sku,
            quantity_on_hand=5,
            quantity_reserved=0,
            reorder_point=2,
            reorder_quantity=10,
        )
        forecast = MagicMock(predicted_quantity=1.0)
        self.repo.get_all.return_value.filter.return_value.order_by.return_value.__getitem__ = (
            lambda self_inner, x: [forecast]
        )
        result = self.service.calculate_stockout_risk('NO-LEAD-SKU')
        self.assertFalse(result)

    def test_stockout_risk_safety_stock_none(self):
        self.product.safety_stock = None
        self.product.save()
        forecast = MagicMock(predicted_quantity=1.0)
        self.repo.get_all.return_value.filter.return_value.order_by.return_value.__getitem__ = (
            lambda self_inner, x: [forecast]
        )
        result = self.service.calculate_stockout_risk(self.sku.code)
        self.assertFalse(result)

    def test_stockout_risk_empty_forecasts(self):
        self.repo.get_all.return_value.filter.return_value.order_by.return_value.__getitem__ = (
            lambda self_inner, x: []
        )
        result = self.service.calculate_stockout_risk(self.sku.code)
        self.assertFalse(result)


class ForecastingServiceGetDashboardDataTest(ForecastingServiceTestBase):
    def setUp(self):
        self.repo = MagicMock(spec=ForecastingRepository)
        self.service = ForecastingService(repo=self.repo)

    @patch('apps.forecasting.services.cache')
    def test_returns_cached_data(self, mock_cache):
        cached_data = {
            'skus': [
                {'id': 'SKU1', 'stockout_risk': False, 'current_stock': 10, 'reorder_point': 5}
            ]
        }
        mock_cache.get.return_value = cached_data
        result = self.service.get_dashboard_data()
        self.assertIn('skus', result)
        self.assertEqual(result['skus'], cached_data['skus'])
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['page'], 1)
        self.assertEqual(result['per_page'], 6)
        self.assertIn('alerts', result)
        mock_cache.get.assert_called_once_with(
            f'forecast_dashboard_data_v{DASHBOARD_CACHE_VERSION}'
        )

    @patch('apps.forecasting.services.cache')
    def test_computes_when_not_cached(self, mock_cache):
        mock_cache.get.return_value = None
        with patch.object(self.service, '_compute_dashboard', return_value={'skus': []}):
            result = self.service.get_dashboard_data()
            self.assertIn('skus', result)
            self.assertEqual(result['skus'], [])
            self.assertEqual(result['total'], 0)
            self.assertEqual(result['alerts'], [])
            mock_cache.set.assert_called_once_with(
                f'forecast_dashboard_data_v{DASHBOARD_CACHE_VERSION}',
                {'skus': []},
                timeout=3600,
            )

    @patch('apps.forecasting.services.cache')
    def test_cache_read_exception_falls_through(self, mock_cache):
        mock_cache.get.side_effect = Exception('Redis down')
        with patch.object(self.service, '_compute_dashboard', return_value={'skus': []}):
            result = self.service.get_dashboard_data()
            self.assertEqual(result['total'], 0)

    @patch('apps.forecasting.services.cache')
    def test_cache_write_exception_does_not_crash(self, mock_cache):
        mock_cache.get.return_value = None
        mock_cache.set.side_effect = Exception('Redis write fail')
        with patch.object(self.service, '_compute_dashboard', return_value={'skus': []}):
            result = self.service.get_dashboard_data()
            self.assertEqual(result['total'], 0)

    @patch('apps.forecasting.services.cache')
    def test_pagination_page_2(self, mock_cache):
        skus = [
            {'id': f'SKU{i}', 'stockout_risk': False, 'current_stock': 10, 'reorder_point': 5}
            for i in range(12)
        ]
        mock_cache.get.return_value = {'skus': skus}
        result = self.service.get_dashboard_data(page=2, page_size=6)
        self.assertEqual(len(result['skus']), 6)
        self.assertEqual(result['skus'][0]['id'], 'SKU6')

    @patch('apps.forecasting.services.cache')
    def test_pagination_last_partial_page(self, mock_cache):
        skus = [
            {'id': f'SKU{i}', 'stockout_risk': False, 'current_stock': 10, 'reorder_point': 5}
            for i in range(8)
        ]
        mock_cache.get.return_value = {'skus': skus}
        result = self.service.get_dashboard_data(page=2, page_size=6)
        self.assertEqual(len(result['skus']), 2)

    @patch('apps.forecasting.services.cache')
    def test_pagination_beyond_total(self, mock_cache):
        skus = [{'id': 'SKU0', 'stockout_risk': False, 'current_stock': 10, 'reorder_point': 5}]
        mock_cache.get.return_value = {'skus': skus}
        result = self.service.get_dashboard_data(page=10, page_size=6)
        self.assertEqual(len(result['skus']), 0)

    @patch('apps.forecasting.services.cache')
    def test_alerts_include_stockout_risk(self, mock_cache):
        skus = [
            {'id': 'SKU1', 'stockout_risk': True, 'current_stock': 10, 'reorder_point': 5},
            {'id': 'SKU2', 'stockout_risk': False, 'current_stock': 10, 'reorder_point': 5},
        ]
        mock_cache.get.return_value = {'skus': skus}
        result = self.service.get_dashboard_data()
        self.assertEqual(len(result['alerts']), 1)
        self.assertEqual(result['alerts'][0]['id'], 'SKU1')

    @patch('apps.forecasting.services.cache')
    def test_alerts_include_low_stock(self, mock_cache):
        skus = [
            {'id': 'SKU1', 'stockout_risk': False, 'current_stock': 2, 'reorder_point': 5},
            {'id': 'SKU2', 'stockout_risk': False, 'current_stock': 10, 'reorder_point': 5},
        ]
        mock_cache.get.return_value = {'skus': skus}
        result = self.service.get_dashboard_data()
        self.assertEqual(len(result['alerts']), 1)
        self.assertEqual(result['alerts'][0]['id'], 'SKU1')

    @patch('apps.forecasting.services.cache')
    def test_no_alerts_when_stock_sufficient(self, mock_cache):
        skus = [
            {'id': 'SKU1', 'stockout_risk': False, 'current_stock': 20, 'reorder_point': 5},
        ]
        mock_cache.get.return_value = {'skus': skus}
        result = self.service.get_dashboard_data()
        self.assertEqual(len(result['alerts']), 0)


class ForecastingServiceComputeDashboardTest(ForecastingServiceTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        today = date.today()
        for i in range(5):
            ForecastResult.objects.create(
                sku=cls.sku,
                forecast_date=today + timedelta(days=i),
                predicted_quantity=10.0 + i,
                lower_bound=5.0,
                upper_bound=15.0,
                mae=1.0,
                mape=0.1,
                model_version='v1',
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
        self.assertEqual(sku_data['product_name'], 'Test Product')
        self.assertEqual(sku_data['sku_code'], 'FRC-SKU-001')
        self.assertEqual(len(sku_data['forecast']), 5)
        self.assertIn('date', sku_data['forecast'][0])
        self.assertIn('demand', sku_data['forecast'][0])
        self.assertIn('predicted_demand_30d', sku_data)
        self.assertIn('confidence_score', sku_data)

    def test_compute_dashboard_stockout_risk(self):
        self.stock_level.quantity_on_hand = 1
        self.stock_level.save()
        result = self.service._compute_dashboard()
        sku_data = result['skus'][0]
        self.assertTrue(sku_data['stockout_risk'])

    def test_compute_dashboard_no_stock_level(self):
        StockLevel.objects.filter(sku=self.sku).delete()
        result = self.service._compute_dashboard()
        sku_data = result['skus'][0]
        self.assertFalse(sku_data['stockout_risk'])
        self.assertEqual(sku_data['reorder_point'], 0)
        self.assertEqual(sku_data['current_stock'], 0)

    def test_compute_dashboard_mape_gt_one(self):
        ForecastResult.objects.filter(sku=self.sku).update(mape=1.5)
        result = self.service._compute_dashboard()
        sku_data = result['skus'][0]
        self.assertIsNotNone(sku_data['confidence_score'])

    def test_compute_dashboard_mape_nan(self):
        ForecastResult.objects.filter(sku=self.sku).update(mape=float('nan'))
        result = self.service._compute_dashboard()
        sku_data = result['skus'][0]
        self.assertIsNone(sku_data['confidence_score'])

    def test_compute_dashboard_mape_inf(self):
        ForecastResult.objects.filter(sku=self.sku).update(mape=float('inf'))
        result = self.service._compute_dashboard()
        sku_data = result['skus'][0]
        self.assertIsNone(sku_data['confidence_score'])

    def test_compute_dashboard_mape_none_fallback(self):
        ForecastResult.objects.filter(sku=self.sku).update(mape=None)
        result = self.service._compute_dashboard()
        sku_data = result['skus'][0]
        self.assertIsNone(sku_data['mape'])
        self.assertIsNone(sku_data['confidence_score'])

    def test_compute_dashboard_mae_nan(self):
        ForecastResult.objects.filter(sku=self.sku).update(mae=float('nan'))
        result = self.service._compute_dashboard()
        sku_data = result['skus'][0]
        self.assertIsNone(sku_data['mae'])

    def test_compute_dashboard_mae_inf(self):
        ForecastResult.objects.filter(sku=self.sku).update(mae=float('inf'))
        result = self.service._compute_dashboard()
        sku_data = result['skus'][0]
        self.assertIsNone(sku_data['mae'])

    def test_compute_dashboard_mae_none(self):
        ForecastResult.objects.filter(sku=self.sku).update(mae=None)
        result = self.service._compute_dashboard()
        sku_data = result['skus'][0]
        self.assertIsNone(sku_data['mae'])

    def test_compute_dashboard_upper_lower_bound_none(self):
        ForecastResult.objects.filter(sku=self.sku).update(lower_bound=None, upper_bound=None)
        result = self.service._compute_dashboard()
        forecast_entry = result['skus'][0]['forecast'][0]
        self.assertIsNone(forecast_entry['upper_bound'])
        self.assertIsNone(forecast_entry['lower_bound'])

    def test_compute_dashboard_supplier_name(self):
        result = self.service._compute_dashboard()
        sku_data = result['skus'][0]
        self.assertEqual(sku_data['supplier'], 'Test Supplier')
        self.assertEqual(sku_data['lead_time_days'], 7)

    def test_compute_dashboard_supplier_no_name(self):
        self.supplier.name = None
        self.supplier.save()
        result = self.service._compute_dashboard()
        sku_data = result['skus'][0]
        self.assertEqual(sku_data['supplier'], '—')

    def test_compute_dashboard_no_supplier(self):
        self.product.supplier = None
        self.product.save()
        result = self.service._compute_dashboard()
        sku_data = result['skus'][0]
        self.assertEqual(sku_data['supplier'], '—')
        self.assertEqual(sku_data['lead_time_days'], 7)

    def test_compute_dashboard_empty_when_exception(self):
        with patch('apps.forecasting.services.ForecastResult') as mock_fr:
            mock_fr.objects.filter.side_effect = Exception('DB crash')
            result = self.service._compute_dashboard()
            self.assertEqual(result['skus'], [])


class ForecastingServiceRunForecastTest(ForecastingServiceTestBase):
    def setUp(self):
        self.repo = MagicMock(spec=ForecastingRepository)
        self.service = ForecastingService(repo=self.repo)
        self.engine = MagicMock()
        self.service.engine = self.engine

    @patch('apps.forecasting.services.prepare_forecast_dataframe')
    def test_run_single_sku(self, mock_prepare):
        import pandas as pd

        mock_prepare.return_value = pd.DataFrame({'ds': [date.today()], 'y': [10.0]})
        self.repo.get_sku.return_value = self.sku
        self.engine.predict.return_value = {
            'results': [
                {
                    'forecast_date': date.today(),
                    'predicted_quantity': 10.0,
                    'lower_bound': 5.0,
                    'upper_bound': 15.0,
                }
            ],
            'mae': 1.0,
            'mape': 0.1,
            'model_version': 'v1',
            'forecast_method': 'prophet',
        }
        results = self.service.run_forecast(sku_id=self.sku.id)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['status'], 'success')
        self.assertEqual(results[0]['sku'], 'FRC-SKU-001')
        self.repo.get_sku.assert_called_once_with(self.sku.id)

    @patch('apps.forecasting.services.prepare_forecast_dataframe')
    def test_run_all_skus(self, mock_prepare):
        import pandas as pd

        mock_prepare.return_value = pd.DataFrame({'ds': [date.today()], 'y': [10.0]})
        sku2 = MagicMock(id=2, code='SKU-2')
        self.repo.get_all_skus.return_value = [self.sku, sku2]
        self.engine.predict.return_value = {
            'results': [
                {
                    'forecast_date': date.today(),
                    'predicted_quantity': 10.0,
                    'lower_bound': 5.0,
                    'upper_bound': 15.0,
                }
            ],
            'mae': 1.0,
            'mape': 0.1,
            'model_version': 'v1',
            'forecast_method': 'prophet',
        }
        results = self.service.run_forecast()
        self.assertEqual(len(results), 2)

    @patch('apps.forecasting.services.prepare_forecast_dataframe')
    def test_run_forecast_skipped_when_no_data(self, mock_prepare):
        mock_prepare.return_value = None
        self.repo.get_sku.return_value = self.sku
        results = self.service.run_forecast(sku_id=self.sku.id)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['status'], 'skipped')
        self.assertEqual(results[0]['reason'], 'no_data')
        self.engine.predict.assert_not_called()

    @patch('apps.forecasting.services.prepare_forecast_dataframe')
    def test_run_forecast_exception_per_sku(self, mock_prepare):
        mock_prepare.side_effect = [Exception('fail'), None]
        sku2 = MagicMock(id=2, code='SKU-2')
        self.repo.get_all_skus.return_value = [self.sku, sku2]
        results = self.service.run_forecast()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['status'], 'skipped')


class ForecastingServiceForecastForSkuTest(ForecastingServiceTestBase):
    def setUp(self):
        self.repo = MagicMock(spec=ForecastingRepository)
        self.service = ForecastingService(repo=self.repo)
        self.engine = MagicMock()
        self.service.engine = self.engine

    @patch('apps.forecasting.services.prepare_forecast_dataframe')
    def test_no_data_returns_skipped(self, mock_prepare):
        mock_prepare.return_value = None
        result = self.service._forecast_for_sku(self.sku)
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(result['reason'], 'no_data')
        self.assertIsNone(result['model_version'])

    @patch('apps.forecasting.services.prepare_forecast_dataframe')
    def test_success_upserts_results(self, mock_prepare):
        import pandas as pd

        mock_prepare.return_value = pd.DataFrame({'ds': [date.today()], 'y': [10.0]})
        self.engine.predict.return_value = {
            'results': [
                {
                    'forecast_date': date.today(),
                    'predicted_quantity': 10.0,
                    'lower_bound': 5.0,
                    'upper_bound': 15.0,
                }
            ],
            'mae': 1.0,
            'mape': 0.1,
            'model_version': 'v1',
            'forecast_method': 'prophet',
        }
        result = self.service._forecast_for_sku(self.sku)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['forecast_days'], 1)
        self.repo.upsert.assert_called_once()

    @patch('apps.forecasting.services.prepare_forecast_dataframe')
    def test_mae_nan_becomes_none(self, mock_prepare):
        import pandas as pd

        mock_prepare.return_value = pd.DataFrame({'ds': [date.today()], 'y': [10.0]})
        self.engine.predict.return_value = {
            'results': [
                {
                    'forecast_date': date.today(),
                    'predicted_quantity': 10.0,
                    'lower_bound': 5.0,
                    'upper_bound': 15.0,
                }
            ],
            'mae': float('nan'),
            'mape': float('nan'),
            'model_version': 'v1',
            'forecast_method': 'prophet',
        }
        result = self.service._forecast_for_sku(self.sku)
        self.assertIsNone(result['mae'])
        self.assertIsNone(result['mape'])

    @patch('apps.forecasting.services.prepare_forecast_dataframe')
    def test_mae_inf_becomes_none(self, mock_prepare):
        import pandas as pd

        mock_prepare.return_value = pd.DataFrame({'ds': [date.today()], 'y': [10.0]})
        self.engine.predict.return_value = {
            'results': [
                {
                    'forecast_date': date.today(),
                    'predicted_quantity': 10.0,
                    'lower_bound': 5.0,
                    'upper_bound': 15.0,
                }
            ],
            'mae': float('inf'),
            'mape': float('inf'),
            'model_version': 'v1',
            'forecast_method': 'prophet',
        }
        result = self.service._forecast_for_sku(self.sku)
        self.assertIsNone(result['mae'])
        self.assertIsNone(result['mape'])

    @patch('apps.forecasting.services.prepare_forecast_dataframe')
    def test_mae_mape_none_stays_none(self, mock_prepare):
        import pandas as pd

        mock_prepare.return_value = pd.DataFrame({'ds': [date.today()], 'y': [10.0]})
        self.engine.predict.return_value = {
            'results': [
                {
                    'forecast_date': date.today(),
                    'predicted_quantity': 10.0,
                    'lower_bound': 5.0,
                    'upper_bound': 15.0,
                }
            ],
            'mae': None,
            'mape': None,
            'model_version': 'v1',
            'forecast_method': 'unknown',
        }
        result = self.service._forecast_for_sku(self.sku)
        self.assertIsNone(result['mae'])
        self.assertIsNone(result['mape'])
        self.assertEqual(result['forecast_method'], 'unknown')

    @patch('apps.forecasting.services.prepare_forecast_dataframe')
    def test_multiple_results_all_upserted(self, mock_prepare):
        import pandas as pd

        mock_prepare.return_value = pd.DataFrame({'ds': [date.today()], 'y': [10.0]})
        self.engine.predict.return_value = {
            'results': [
                {
                    'forecast_date': date.today() + timedelta(days=i),
                    'predicted_quantity': 10.0 + i,
                    'lower_bound': 5.0,
                    'upper_bound': 15.0,
                }
                for i in range(3)
            ],
            'mae': 1.0,
            'mape': 0.1,
            'model_version': 'v1',
            'forecast_method': 'prophet',
        }
        result = self.service._forecast_for_sku(self.sku)
        self.assertEqual(result['forecast_days'], 3)
        self.assertEqual(self.repo.upsert.call_count, 3)
