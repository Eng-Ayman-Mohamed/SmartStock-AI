from datetime import date, timedelta

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

    # === TRIGGER FORECAST ===

    def test_trigger_unauthenticated(self):
        resp = self.client.post(
            '/api/forecasting/trigger/',
            {'sku_id': self.sku.id},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_trigger_as_viewer_fails(self):
        resp = self.client.post(
            '/api/forecasting/trigger/',
            {'sku_id': self.sku.id},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_trigger_as_manager_fails(self):
        resp = self.client.post(
            '/api/forecasting/trigger/',
            {'sku_id': self.sku.id},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_trigger_as_admin_success(self):
        resp = self.client.post(
            '/api/forecasting/trigger/',
            {'sku_id': self.sku.id},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        inner = data['data']
        self.assertEqual(inner['status'], 'forecast_triggered')
        forecasts = inner['forecasts']
        self.assertEqual(len(forecasts), 1)
        self.assertEqual(forecasts[0]['sku'], 'FRC-TST')
        self.assertEqual(forecasts[0]['status'], 'success')
        self.assertEqual(forecasts[0]['forecast_days'], 30)

    def test_trigger_creates_30_forecast_results(self):
        self.client.post(
            '/api/forecasting/trigger/',
            {'sku_id': self.sku.id},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        forecasts = ForecastResult.objects.filter(sku=self.sku)
        self.assertEqual(forecasts.count(), 30)

        for f in forecasts:
            self.assertIsNotNone(f.predicted_quantity)
            self.assertIsNotNone(f.forecast_date)
            self.assertIn(f.model_version, ['prophet_1.1', 'moving_average_fallback'])

    # === FORECAST LIST AFTER TRIGGER ===

    def test_forecast_list_shows_triggered_data(self):
        self.client.post(
            '/api/forecasting/trigger/',
            {'sku_id': self.sku.id},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        resp = self.client.get(
            '/api/forecasting/forecasts/?page_size=30',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        items = resp.json()['data']
        self.assertEqual(len(items), 30)
        self.assertIn('sku_code', items[0])
        self.assertIn('product_name', items[0])
        self.assertIn('predicted_quantity', items[0])

    # === FORECAST DETAIL ===

    def test_retrieve_forecast_detail(self):
        self.client.post(
            '/api/forecasting/trigger/',
            {'sku_id': self.sku.id},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        forecast = ForecastResult.objects.first()
        resp = self.client.get(
            f'/api/forecasting/forecasts/{forecast.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        item = resp.json()['data']
        self.assertEqual(item['id'], forecast.id)
        self.assertEqual(item['sku_code'], 'FRC-TST')
        self.assertEqual(item['product_name'], 'Forecast Product')

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

    def test_dashboard_with_forecast_data(self):
        self.client.post(
            '/api/forecasting/trigger/',
            {'sku_id': self.sku.id},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        resp = self.client.get(
            '/api/forecasting/dashboard/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()['data']
        self.assertIn('skus', data)
        self.assertEqual(len(data['skus']), 1)
        sku_data = data['skus'][0]
        self.assertEqual(sku_data['id'], 'FRC-TST')
        self.assertEqual(sku_data['sku_code'], 'FRC-TST')
        self.assertEqual(sku_data['product_name'], 'Forecast Product')
        self.assertEqual(sku_data['current_stock'], 50)
        self.assertEqual(sku_data['reorder_point'], 10)
        self.assertEqual(len(sku_data['forecast']), 30)
        self.assertIn('predicted_demand_30d', sku_data)
        self.assertIn('confidence_score', sku_data)

    # === TRIGGER WITH NO SALES DATA ===

    def test_trigger_no_sales_data(self):
        new_product = Product.objects.create(name='Dry Product', category=self.category)
        dry_sku = SKU.objects.create(product=new_product, code='DRY-001')
        StockLevel.objects.create(sku=dry_sku, quantity_on_hand=0)

        resp = self.client.post(
            '/api/forecasting/trigger/',
            {'sku_id': dry_sku.id},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()['data']
        self.assertEqual(data['status'], 'forecast_triggered')
        forecasts = data['forecasts']
        self.assertEqual(len(forecasts), 1)
        self.assertEqual(forecasts[0]['status'], 'skipped')
        self.assertEqual(forecasts[0]['reason'], 'no_data')

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
