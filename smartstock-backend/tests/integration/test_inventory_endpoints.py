from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import CustomUser
from apps.inventory.models import Product


class InventoryEndpointTests(APITestCase):
    """Integration tests for inventory API endpoints."""

    @classmethod
    def setUpTestData(cls):
        cls.manager = CustomUser.objects.create_user(
            email='manager@test.com',
            username='manager@test.com',
            password='testpass123',
            role='manager',
        )
        cls.admin = CustomUser.objects.create_user(
            email='admin@test.com',
            username='admin@test.com',
            password='testpass123',
            role='admin',
        )

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    # === PRODUCT ENDPOINTS ===

    def test_list_products_unauthenticated(self):
        resp = self.client.get('/api/inventory/products/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_products_authenticated(self):
        resp = self.client.get(
            '/api/inventory/products/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn('count', data)
        self.assertIn('results', data)
        self.assertIn('next', data)
        self.assertIn('previous', data)

    def test_create_product_as_manager(self):
        payload = {'name': 'New Product', 'description': 'Test', 'category': 'Electronics'}
        resp = self.client.post(
            '/api/inventory/products/',
            payload,
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json()['name'], 'New Product')

    def test_create_product_as_viewer_fails(self):
        viewer = CustomUser.objects.create_user(
            email='viewer@test.com',
            username='viewer@test.com',
            password='testpass123',
            role='viewer',
        )
        payload = {'name': 'Should Fail', 'description': '', 'category': 'Other'}
        resp = self.client.post(
            '/api/inventory/products/',
            payload,
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_full_product_crud(self):
        headers = {'HTTP_AUTHORIZATION': self._auth_header(self.admin)}

        # Create
        payload = {'name': 'CRUD Product', 'description': 'Full cycle', 'category': 'Testing'}
        resp = self.client.post('/api/inventory/products/', payload, format='json', **headers)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        pid = resp.json()['id']

        # Retrieve
        resp = self.client.get(f'/api/inventory/products/{pid}/', **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['name'], 'CRUD Product')

        # Update
        resp = self.client.patch(
            f'/api/inventory/products/{pid}/',
            {'name': 'Updated CRUD Product'},
            format='json',
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Delete
        resp = self.client.delete(f'/api/inventory/products/{pid}/', **headers)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Verify deleted
        resp = self.client.get(f'/api/inventory/products/{pid}/', **headers)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # === PAGINATION ===

    def test_pagination_default_page_size(self):
        for i in range(25):
            Product.objects.create(name=f'Pagination Product {i}', category='Test')
        resp = self.client.get(
            '/api/inventory/products/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        data = resp.json()
        self.assertEqual(len(data['results']), 20)
        self.assertIsNotNone(data['next'])

    def test_pagination_custom_page_size(self):
        for i in range(10):
            Product.objects.create(name=f'Page Product {i}', category='Test')
        resp = self.client.get(
            '/api/inventory/products/?page_size=5',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        data = resp.json()
        self.assertEqual(len(data['results']), 5)

    # === SEARCH & FILTER ===

    def test_search_products(self):
        Product.objects.create(name='Wireless Mouse', category='Electronics')
        Product.objects.create(name='USB Cable', category='Electronics')
        resp = self.client.get(
            '/api/inventory/products/?search=Mouse',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        results = resp.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Wireless Mouse')

    def test_filter_by_category(self):
        Product.objects.create(name='Item A', category='Electronics')
        Product.objects.create(name='Item B', category='Furniture')
        resp = self.client.get(
            '/api/inventory/products/?category=Electronics',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        results = resp.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['category'], 'Electronics')

    # === OTHER ENDPOINTS ===

    def test_sku_endpoint(self):
        resp = self.client.get(
            '/api/inventory/skus/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_stock_levels_endpoint(self):
        resp = self.client.get(
            '/api/inventory/stock-levels/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_low_stock_endpoint(self):
        resp = self.client.get(
            '/api/inventory/stock-levels/low_stock/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_sales_records_endpoint(self):
        resp = self.client.get(
            '/api/inventory/sales-records/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
