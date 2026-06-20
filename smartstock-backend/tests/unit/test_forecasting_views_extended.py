"""Tests for apps/forecasting/views.py — edge cases not covered by integration tests."""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class ForecastBySKUViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='viewer1', email='viewer@test.com', password='pass1234', role='viewer'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('apps.forecasting.views.cache')
    def test_cache_hit_returns_cached(self, mock_cache):
        cached = {'sku_id': 1, 'sku_code': 'SKU001', 'forecasts': []}
        mock_cache.get.return_value = cached
        response = self.client.get('/api/forecasting/results/SKU001/')
        self.assertEqual(response.status_code, 200)

    @patch('apps.forecasting.views.cache')
    @patch('apps.forecasting.views.ForecastingService')
    def test_cache_miss_fetches_from_service(self, MockService, mock_cache):
        mock_cache.get.return_value = None
        mock_service = MockService.return_value
        mock_service.get_forecast_by_sku_code_or_id.return_value = []
        response = self.client.get('/api/forecasting/results/SKU001/')
        self.assertEqual(response.status_code, 404)

    @patch('apps.forecasting.views.cache')
    @patch('apps.forecasting.views.ForecastingService')
    def test_resolved_key_caching(self, MockService, mock_cache):
        mock_cache.get.return_value = None
        mock_service = MockService.return_value

        row = MagicMock()
        row.sku_id = 1
        row.sku.code = 'SKU001'
        row.sku.product.name = 'Widget'
        row.forecast_date.isoformat.return_value = '2026-07-01'
        row.predicted_quantity = 10
        row.lower_bound = 8
        row.upper_bound = 12
        row.mae = 0.5
        row.mape = 0.03
        row.model_version = 'v1'

        mock_service.get_forecast_by_sku_code_or_id.return_value = [row]
        response = self.client.get('/api/forecasting/results/1/')
        self.assertEqual(response.status_code, 200)


class RunForecastViewEdgeTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin1', email='admin@test.com', password='pass1234', role='admin'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('apps.forecasting.views.run_forecasting_agent')
    def test_valid_sku_ids(self, mock_task):
        mock_task.delay.return_value = MagicMock(id='task-123')
        response = self.client.post('/api/forecasting/run/', {'sku_ids': [1, 2, 3]}, format='json')
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['status'], 'forecast_triggered')

    def test_invalid_sku_ids_not_list(self):
        response = self.client.post(
            '/api/forecasting/run/', {'sku_ids': 'not-a-list'}, format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_sku_ids_contain_non_int(self):
        response = self.client.post('/api/forecasting/run/', {'sku_ids': [1, 'abc']}, format='json')
        self.assertEqual(response.status_code, 400)


class ForecastDashboardViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='viewer2', email='v2@test.com', password='pass1234', role='viewer'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('apps.forecasting.views.ForecastingService')
    def test_valid_page_params(self, MockService):
        mock_service = MockService.return_value
        mock_service.get_dashboard_data.return_value = {
            'skus': [],
            'alerts': [],
            'total': 0,
            'page': 1,
            'per_page': 6,
        }
        response = self.client.get('/api/forecasting/dashboard/?page=2&page_size=10')
        self.assertEqual(response.status_code, 200)

    @patch('apps.forecasting.views.ForecastingService')
    def test_invalid_page_params_use_defaults(self, MockService):
        mock_service = MockService.return_value
        mock_service.get_dashboard_data.return_value = {
            'skus': [],
            'alerts': [],
            'total': 0,
            'page': 1,
            'per_page': 6,
        }
        response = self.client.get('/api/forecasting/dashboard/?page=abc&page_size=-5')
        self.assertEqual(response.status_code, 200)


class ForecastJobStatusViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin2', email='a2@test.com', password='pass1234', role='admin'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('apps.forecasting.views.AsyncResult')
    def test_success_status(self, MockResult):
        mock_result = MockResult.return_value
        mock_result.status = 'SUCCESS'
        mock_result.result = {'processed': 5}
        response = self.client.get('/api/forecasting/run/fake-job-id/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'SUCCESS')

    @patch('apps.forecasting.views.AsyncResult')
    def test_failure_status(self, MockResult):
        mock_result = MockResult.return_value
        mock_result.status = 'FAILURE'
        mock_result.result = 'boom'
        response = self.client.get('/api/forecasting/run/fake-job-id/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'FAILURE')
        self.assertIn('error', response.data)

    @patch('apps.forecasting.views.AsyncResult')
    def test_pending_status(self, MockResult):
        mock_result = MockResult.return_value
        mock_result.status = 'PENDING'
        response = self.client.get('/api/forecasting/run/fake-job-id/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'PENDING')
