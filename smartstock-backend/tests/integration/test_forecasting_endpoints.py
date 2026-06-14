from datetime import date, timedelta
from unittest.mock import patch

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import CustomUser
from apps.forecasting.models import ForecastResult
from apps.inventory.models import SKU, Category, Product, SalesRecord, StockLevel


class ForecastingEndpointTests(APITestCase):
    """Integration tests for forecasting API endpoints."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            email='admin@test.com',
            username='admin@test.com',
            password='testpass123',
            role='admin',
        )
        cls.manager = CustomUser.objects.create_user(
            email='manager@test.com',
            username='manager@test.com',
            password='testpass123',
            role='manager',
        )
        cls.viewer = CustomUser.objects.create_user(
            email='viewer@test.com',
            username='viewer@test.com',
            password='testpass123',
            role='viewer',
        )

        cls.category = Category.objects.create(name='Forecast Test Cat')
        cls.product = Product.objects.create(name='Forecast Product', category=cls.category)
        cls.sku = SKU.objects.create(product=cls.product, code='FRC-TST')
        cls.stock = StockLevel.objects.create(sku=cls.sku, quantity_on_hand=50, reorder_point=10)

        base = date.today() - timedelta(days=60)
        for i in range(60):
            SalesRecord.objects.create(
                sku=cls.sku,
                date=base + timedelta(days=i),
                quantity_sold=float(10 + (i % 5)),
            )

    def setUp(self):
        cache.clear()

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    # === LIST FORECASTS ===

    def test_list_forecasts_unauthenticated(self):
        resp = self.client.get('/api/forecasting/forecasts/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_forecasts_as_viewer(self):
        resp = self.client.get(
            '/api/forecasting/forecasts/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn('status', data)
        self.assertIn('data', data)
        self.assertIn('meta', data)

    def test_list_forecasts_empty(self):
        resp = self.client.get(
            '/api/forecasting/forecasts/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()['data']), 0)

    # === RUN FORECAST (async Celery task) ===

    @patch('apps.forecasting.views.run_forecasting_agent.delay')
    def test_run_forecast_unauthenticated(self, mock_task):
        resp = self.client.post(
            '/api/forecasting/run/',
            {'sku_ids': [self.sku.id]},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('apps.forecasting.views.run_forecasting_agent.delay')
    def test_run_forecast_as_viewer_fails(self, mock_task):
        resp = self.client.post(
            '/api/forecasting/run/',
            {'sku_ids': [self.sku.id]},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @patch('apps.forecasting.views.run_forecasting_agent.delay')
    def test_run_forecast_as_manager_fails(self, mock_task):
        resp = self.client.post(
            '/api/forecasting/run/',
            {'sku_ids': [self.sku.id]},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @patch('apps.forecasting.views.run_forecasting_agent.delay')
    def test_run_forecast_as_admin_success(self, mock_task):
        mock_task.return_value.id = 'fake-task-id'
        resp = self.client.post(
            '/api/forecasting/run/',
            {'sku_ids': [self.sku.id]},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        data = resp.json()
        self.assertEqual(data['status'], 'forecast_triggered')
        self.assertIn('job_id', data)
        mock_task.assert_called_once_with(sku_ids=[self.sku.id])

    @patch('apps.forecasting.views.run_forecasting_agent.delay')
    def test_run_forecast_all_skus(self, mock_task):
        mock_task.return_value.id = 'fake-task-id'
        resp = self.client.post(
            '/api/forecasting/run/',
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        mock_task.assert_called_once_with(sku_ids=None)

    @patch('apps.forecasting.views.run_forecasting_agent.delay')
    def test_run_forecast_invalid_sku_ids(self, mock_task):
        resp = self.client.post(
            '/api/forecasting/run/',
            {'sku_ids': 'not-a-list'},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # === JOB STATUS ===

    @patch('apps.forecasting.views.run_forecasting_agent.delay')
    def test_job_status_pending(self, mock_task):
        mock_task.return_value.id = 'fake-task-id'
        resp = self.client.post(
            '/api/forecasting/run/',
            {'sku_ids': [self.sku.id]},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        job_id = resp.json()['job_id']

        with patch('apps.forecasting.views.AsyncResult') as mock_result:
            mock_result.return_value.status = 'PENDING'
            mock_result.return_value.result = None
            resp = self.client.get(
                f'/api/forecasting/run/{job_id}/',
                HTTP_AUTHORIZATION=self._auth_header(self.admin),
            )
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # === DASHBOARD ===

    def test_dashboard_unauthenticated(self):
        resp = self.client.get('/api/forecasting/dashboard/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_empty(self):
        resp = self.client.get(
            '/api/forecasting/dashboard/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn('status', data)
        self.assertIn('data', data)
        self.assertEqual(data['data']['skus'], [])

    # === ERROR ENVELOPE ===

    def test_forecast_404_returns_error_envelope(self):
        resp = self.client.get(
            '/api/forecasting/forecasts/99999/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        data = resp.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('error', data)
        self.assertIn('message', data)
        self.assertIn('code', data)
