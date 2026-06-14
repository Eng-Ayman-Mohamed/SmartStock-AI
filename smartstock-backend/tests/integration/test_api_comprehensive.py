from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import CustomUser
from apps.inventory.models import SKU, Category, Product, StockLevel, Supplier


class AuthEndpointComprehensiveTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            email='auth_admin@test.com',
            username='auth_admin@test.com',
            password='testpass123',
            role='admin',
        )
        cls.manager = CustomUser.objects.create_user(
            email='auth_manager@test.com',
            username='auth_manager@test.com',
            password='testpass123',
            role='manager',
        )

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    def test_register_success(self):
        resp = self.client.post(
            '/api/auth/register/',
            {
                'email': 'new@test.com',
                'name': 'New User',
                'password': 'strongpass123',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_register_duplicate_email(self):
        resp = self.client.post(
            '/api/auth/register/',
            {
                'email': 'auth_admin@test.com',
                'name': 'Dup',
                'password': 'strongpass123',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_register_weak_password(self):
        resp = self.client.post(
            '/api/auth/register/',
            {
                'email': 'weak@test.com',
                'name': 'Weak',
                'password': '123',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_login_success(self):
        resp = self.client.post(
            '/api/auth/login/',
            {
                'email': 'auth_admin@test.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_login_wrong_password(self):
        resp = self.client.post(
            '/api/auth/login/',
            {
                'email': 'auth_admin@test.com',
                'password': 'wrongpass',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_endpoint(self):
        resp = self.client.get(
            '/api/auth/me/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_me_unauthorized(self):
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout(self):
        resp = self.client.post(
            '/api/auth/logout/',
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_logout_unauthorized(self):
        resp = self.client.post('/api/auth/logout/', format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list_create(self):
        resp = self.client.get(
            '/api/auth/users/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_user_detail(self):
        resp = self.client.get(
            f'/api/auth/users/{self.admin.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_user_detail_not_found(self):
        resp = self.client.get(
            '/api/auth/users/999999/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_method_not_allowed(self):
        resp = self.client.put('/api/auth/register/', {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class InventoryEndpointComprehensiveTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            email='inv_admin@test.com',
            username='inv_admin@test.com',
            password='testpass123',
            role='admin',
        )
        cls.manager = CustomUser.objects.create_user(
            email='inv_manager@test.com',
            username='inv_manager@test.com',
            password='testpass123',
            role='manager',
        )
        cls.viewer = CustomUser.objects.create_user(
            email='inv_viewer@test.com',
            username='inv_viewer@test.com',
            password='testpass123',
            role='viewer',
        )
        cls.supplier = Supplier.objects.create(
            name='Test Supplier',
            contact_email='supplier@test.com',
            default_lead_time_days=5,
        )
        cls.category = Category.objects.create(name='Test Category')
        cls.product = Product.objects.create(
            name='Test Product',
            category=cls.category,
            supplier=cls.supplier,
            unit_price=Decimal('19.99'),
        )
        cls.sku = SKU.objects.create(product=cls.product, code='TST-001')
        cls.stock_level = StockLevel.objects.create(
            sku=cls.sku,
            quantity_on_hand=100,
            reorder_point=20,
        )

    def setUp(self):
        cache.clear()

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    def test_product_list_empty(self):
        Product.objects.all().delete()
        resp = self.client.get(
            '/api/inventory/products/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['data'], [])

    def test_product_retrieve(self):
        resp = self.client.get(
            f'/api/inventory/products/{self.product.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['data']['name'], 'Test Product')

    def test_product_not_found(self):
        resp = self.client.get(
            '/api/inventory/products/999999/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_product_create_validation_error(self):
        resp = self.client.post(
            '/api/inventory/products/',
            {'name': ''},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_sku_create(self):
        resp = self.client.post(
            '/api/inventory/skus/',
            {'product': self.product.id, 'code': 'NEW-SKU-001'},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_stock_level_update(self):
        resp = self.client.patch(
            f'/api/inventory/stock-levels/{self.stock_level.id}/',
            {'quantity_on_hand': 200},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_supplier_unicode_name(self):
        resp = self.client.post(
            '/api/inventory/suppliers/',
            {'name': 'مورد اختبار', 'contact_email': 'unicode@test.com'},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_category_list(self):
        resp = self.client.get(
            '/api/inventory/categories/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_sales_records_list(self):
        resp = self.client.get(
            '/api/inventory/sales-records/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_stock_adjustment_success(self):
        resp = self.client.patch(
            f'/api/inventory/stock/{self.product.id}/',
            {'quantity_delta': -5, 'reason': 'test'},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_stock_adjustment_unauthorized(self):
        resp = self.client.patch(
            f'/api/inventory/stock/{self.product.id}/',
            {'quantity_delta': 5},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_id_returns_404(self):
        resp = self.client.get(
            '/api/inventory/products/abc/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class PurchasingEndpointComprehensiveTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            email='pur_admin@test.com',
            username='pur_admin@test.com',
            password='testpass123',
            role='admin',
        )
        cls.supplier = Supplier.objects.create(
            name='PO Supplier',
            contact_email='po@supplier.com',
        )
        cls.category = Category.objects.create(name='PO Category')
        cls.product = Product.objects.create(
            name='PO Product',
            category=cls.category,
            supplier=cls.supplier,
            unit_price=Decimal('25.00'),
        )
        cls.sku = SKU.objects.create(product=cls.product, code='PO-SKU-001')

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    def test_supplier_list(self):
        resp = self.client.get(
            '/api/purchasing/suppliers/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_order_list(self):
        resp = self.client.get(
            '/api/purchasing/orders/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_order_create(self):
        resp = self.client.post(
            '/api/purchasing/orders/',
            {
                'sku': self.sku.id,
                'supplier': self.supplier.id,
                'quantity': 50,
                'total_cost': '1250.00',
            },
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_order_create_validation(self):
        resp = self.client.post(
            '/api/purchasing/orders/',
            {'sku': self.sku.id},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_order_unauthorized(self):
        resp = self.client.get('/api/purchasing/orders/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class ForecastingEndpointComprehensiveTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            email='fc_admin@test.com',
            username='fc_admin@test.com',
            password='testpass123',
            role='admin',
        )
        cls.supplier = Supplier.objects.create(
            name='FC Supplier',
            contact_email='fc@supplier.com',
        )
        cls.category = Category.objects.create(name='FC Category')
        cls.product = Product.objects.create(
            name='FC Product',
            category=cls.category,
            supplier=cls.supplier,
        )
        cls.sku = SKU.objects.create(product=cls.product, code='FC-SKU-001')

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    def test_forecast_list(self):
        resp = self.client.get(
            '/api/forecasting/forecasts/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_forecast_by_sku_no_data(self):
        resp = self.client.get(
            f'/api/forecasting/results/{self.sku.code}/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    @patch('apps.forecasting.views.run_forecasting_agent.delay')
    def test_trigger_forecast(self, mock_task):
        mock_task.return_value.id = 'fake-task-id'
        resp = self.client.post(
            '/api/forecasting/run/',
            {'sku_ids': [self.sku.id]},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

    def test_dashboard(self):
        resp = self.client.get(
            '/api/forecasting/dashboard/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class AuditEndpointComprehensiveTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            email='audit_admin@test.com',
            username='audit_admin@test.com',
            password='testpass123',
            role='admin',
        )

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    def test_audit_log_list(self):
        resp = self.client.get(
            '/api/audit/logs/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_agent_run_list(self):
        resp = self.client.get(
            '/api/audit/logs/agent-runs/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class IngestionEndpointComprehensiveTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            email='ing_admin@test.com',
            username='ing_admin@test.com',
            password='testpass123',
            role='admin',
        )

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    def test_document_list(self):
        resp = self.client.get(
            '/api/ai/documents/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_rag_query_requires_auth(self):
        resp = self.client.post(
            '/api/ai/rag-query/',
            {'query': 'test query'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class HealthEndpointComprehensiveTest(APITestCase):
    def test_health_check_method_not_allowed_post(self):
        resp = self.client.post('/api/health/live/')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_readiness_method_not_allowed_post(self):
        resp = self.client.post('/api/health/ready/')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_health_check_get(self):
        resp = self.client.get('/api/health/live/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        inner = data['data']
        self.assertEqual(inner['status'], 'ok')
        self.assertIn(inner['database'], ['connected', 'disconnected'])
        self.assertIn(inner['redis'], ['connected', 'disconnected'])

    def test_readiness_check(self):
        resp = self.client.get('/api/health/ready/')
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])
        data = resp.json()
        if resp.status_code == status.HTTP_200_OK:
            self.assertEqual(data['data']['status'], 'ok')
        else:
            self.assertEqual(data['data']['status'], 'degraded')
