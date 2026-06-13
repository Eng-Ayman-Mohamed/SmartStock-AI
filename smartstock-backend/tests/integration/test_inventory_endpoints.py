from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import CustomUser
from apps.inventory.models import SKU, Category, Product, StockLevel, Supplier


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
        cls.cat_electronics = Category.objects.create(name='Electronics')
        cls.cat_furniture = Category.objects.create(name='Furniture')
        cls.cat_testing = Category.objects.create(name='Testing')

    def setUp(self):
        cache.clear()

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
        self.assertIn('status', data)
        self.assertIn('data', data)
        self.assertIn('meta', data)

    def test_create_product_as_manager(self):
        payload = {
            'name': 'New Product',
            'description': 'Test',
            'category': self.cat_electronics.id,
        }
        resp = self.client.post(
            '/api/inventory/products/',
            payload,
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json()['data']['name'], 'New Product')

    def test_create_product_as_viewer_fails(self):
        viewer = CustomUser.objects.create_user(
            email='viewer@test.com',
            username='viewer@test.com',
            password='testpass123',
            role='viewer',
        )
        payload = {
            'name': 'Should Fail',
            'description': '',
            'category': self.cat_electronics.id,
        }
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
        payload = {
            'name': 'CRUD Product',
            'description': 'Full cycle',
            'category': self.cat_testing.id,
        }
        resp = self.client.post('/api/inventory/products/', payload, format='json', **headers)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        pid = resp.json()['data']['id']

        # Retrieve
        resp = self.client.get(f'/api/inventory/products/{pid}/', **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['data']['name'], 'CRUD Product')

        # Update
        resp = self.client.patch(
            f'/api/inventory/products/{pid}/',
            {'name': 'Updated CRUD Product'},
            format='json',
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Soft delete
        resp = self.client.delete(f'/api/inventory/products/{pid}/', **headers)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Verify soft-deleted (404 for normal users)
        resp = self.client.get(f'/api/inventory/products/{pid}/', **headers)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    # === PAGINATION ===

    def test_pagination_default_page_size(self):
        for i in range(25):
            Product.objects.create(
                name=f'Pagination Product {i}',
                category=self.cat_testing,
            )
        resp = self.client.get(
            '/api/inventory/products/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        data = resp.json()
        self.assertEqual(len(data['data']), 20)
        self.assertIsNotNone(data['meta']['next'])

    def test_pagination_custom_page_size(self):
        for i in range(10):
            Product.objects.create(
                name=f'Page Product {i}',
                category=self.cat_testing,
            )
        resp = self.client.get(
            '/api/inventory/products/?page_size=5',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        data = resp.json()
        self.assertEqual(len(data['data']), 5)
        self.assertEqual(data['meta']['per_page'], 5)

    # === SEARCH & FILTER ===

    def test_search_products(self):
        Product.objects.create(name='Wireless Mouse', category=self.cat_electronics)
        Product.objects.create(name='USB Cable', category=self.cat_electronics)
        resp = self.client.get(
            '/api/inventory/products/?search=Mouse',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        results = resp.json()['data']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Wireless Mouse')

    def test_search_products_by_sku_code(self):
        product = Product.objects.create(name='SKU Search Product', category=self.cat_electronics)
        SKU.objects.create(product=product, code='SKU-SEARCH-001')
        Product.objects.create(name='Other Product', category=self.cat_electronics)

        resp = self.client.get(
            '/api/inventory/products/?search=SKU-SEARCH',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )

        results = resp.json()['data']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], product.id)

    def test_product_list_includes_sku_stock_fields(self):
        product = Product.objects.create(name='Stock Payload Product', category=self.cat_testing)
        sku = SKU.objects.create(product=product, code='STOCK-PAYLOAD-001')
        stock = StockLevel.objects.create(
            sku=sku,
            quantity_on_hand=14,
            quantity_reserved=3,
            reorder_point=9,
        )

        resp = self.client.get(
            '/api/inventory/products/?search=STOCK-PAYLOAD-001',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )

        sku_payload = resp.json()['data'][0]['skus'][0]
        self.assertEqual(sku_payload['stock_level_id'], stock.id)
        self.assertEqual(sku_payload['quantity_on_hand'], 14)
        self.assertEqual(sku_payload['quantity_reserved'], 3)
        self.assertEqual(sku_payload['stock_reorder_point'], 9)

    def test_filter_by_category(self):
        Product.objects.create(name='Item A', category=self.cat_electronics)
        Product.objects.create(name='Item B', category=self.cat_furniture)
        resp = self.client.get(
            f'/api/inventory/products/?category={self.cat_electronics.id}',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        results = resp.json()['data']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['category_name'], 'Electronics')

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

    # === CATEGORIES ===

    def test_list_categories(self):
        resp = self.client.get(
            '/api/inventory/categories/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn('data', data)
        self.assertEqual(len(data['data']), 3)

    def test_retrieve_category(self):
        resp = self.client.get(
            f'/api/inventory/categories/{self.cat_electronics.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['data']['name'], 'Electronics')

    def test_create_category_as_viewer_fails(self):
        viewer = CustomUser.objects.create_user(
            email='viewer2@test.com',
            username='viewer2@test.com',
            password='testpass123',
            role='viewer',
        )
        resp = self.client.post(
            '/api/inventory/categories/',
            {'name': 'NewCat'},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # === SUPPLIER CRUD ===

    def test_create_supplier_as_manager(self):
        payload = {
            'name': 'Test Supplier',
            'contact_email': 'supplier@test.com',
            'contact_phone': '1234567890',
            'default_lead_time_days': 5,
        }
        resp = self.client.post(
            '/api/inventory/suppliers/',
            payload,
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json()['data']['name'], 'Test Supplier')

    def test_list_suppliers(self):
        Supplier.objects.create(name='Supplier A', contact_email='a@test.com')
        Supplier.objects.create(name='Supplier B', contact_email='b@test.com')
        resp = self.client.get(
            '/api/inventory/suppliers/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.json()['data']), 2)

    def test_update_supplier_as_manager(self):
        supplier = Supplier.objects.create(name='Old Name', contact_email='old@test.com')
        resp = self.client.patch(
            f'/api/inventory/suppliers/{supplier.id}/',
            {'name': 'New Name', 'contact_email': 'new@test.com'},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['data']['name'], 'New Name')

    def test_delete_supplier_as_viewer_fails(self):
        supplier = Supplier.objects.create(name='Del Supplier', contact_email='del@test.com')
        viewer = CustomUser.objects.create_user(
            email='viewer3@test.com',
            username='viewer3@test.com',
            password='testpass123',
            role='viewer',
        )
        resp = self.client.delete(
            f'/api/inventory/suppliers/{supplier.id}/',
            HTTP_AUTHORIZATION=self._auth_header(viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_supplier_as_admin(self):
        supplier = Supplier.objects.create(name='Admin Del', contact_email='admin-del@test.com')
        resp = self.client.delete(
            f'/api/inventory/suppliers/{supplier.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    # === SOFT DELETE & INCLUDE_INACTIVE ===

    def test_soft_delete_product(self):
        headers = {'HTTP_AUTHORIZATION': self._auth_header(self.admin)}
        payload = {
            'name': 'Soft Delete Test',
            'description': 'Will be deleted',
            'category': self.cat_testing.id,
        }
        resp = self.client.post('/api/inventory/products/', payload, format='json', **headers)
        pid = resp.json()['data']['id']

        # Delete
        resp = self.client.delete(f'/api/inventory/products/{pid}/', **headers)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Should not appear in default list
        resp = self.client.get('/api/inventory/products/', **headers)
        ids = [p['id'] for p in resp.json()['data']]
        self.assertNotIn(pid, ids)

        # Admin can see it with include_inactive
        resp = self.client.get('/api/inventory/products/?include_inactive=true', **headers)
        ids = [p['id'] for p in resp.json()['data']]
        self.assertIn(pid, ids)

    def test_include_inactive_fails_for_non_admin(self):
        p = Product.objects.create(
            name='Inactive Product', category=self.cat_testing, is_active=False
        )
        resp = self.client.get(
            '/api/inventory/products/?include_inactive=true',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        ids = [p2['id'] for p2 in resp.json()['data']]
        self.assertNotIn(p.id, ids)

    # === STOCK ADJUSTMENT ENDPOINT ===

    def test_stock_adjustment(self):
        product = Product.objects.create(name='Adjustable', category=self.cat_testing)
        sku = SKU.objects.create(product=product, code='ADJ-001')
        stock = StockLevel.objects.create(sku=sku, quantity_on_hand=100)

        resp = self.client.patch(
            f'/api/inventory/stock/{product.id}/',
            {'quantity_delta': -10, 'reason': 'Test adjustment'},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        stock.refresh_from_db()
        self.assertEqual(stock.quantity_on_hand, 90)

    def test_stock_adjustment_invalid_delta(self):
        product = Product.objects.create(name='Bad Adjust', category=self.cat_testing)
        sku = SKU.objects.create(product=product, code='BAD-001')
        StockLevel.objects.create(sku=sku, quantity_on_hand=50)

        resp = self.client.patch(
            f'/api/inventory/stock/{product.id}/',
            {'quantity_delta': 'not-a-number'},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_stock_adjustment_unauthorized(self):
        product = Product.objects.create(name='Unauth Adjust', category=self.cat_testing)
        sku = SKU.objects.create(product=product, code='UNA-001')
        StockLevel.objects.create(sku=sku, quantity_on_hand=50)

        resp = self.client.patch(
            f'/api/inventory/stock/{product.id}/',
            {'quantity_delta': 5},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # === RESPONSE ENVELOPE SHAPE ===

    def test_response_envelope_shape(self):
        resp = self.client.get(
            '/api/inventory/categories/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        data = resp.json()
        self.assertIn('status', data)
        self.assertIn('data', data)
        self.assertIn('meta', data)
        self.assertEqual(data['status'], 'success')

    def test_error_response_envelope(self):
        resp = self.client.get(
            '/api/inventory/products/999999/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        data = resp.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('error', data)
        self.assertIn('message', data)
        self.assertIn('code', data)

    # === STOCK STATUS FILTERS ===

    def test_filter_stock_status_in_stock(self):
        p = Product.objects.create(name='In Stock Product', category=self.cat_testing)
        sku = SKU.objects.create(product=p, code='STK-01')
        StockLevel.objects.create(sku=sku, quantity_on_hand=100, reorder_point=20)
        resp = self.client.get(
            '/api/inventory/products/?stock_status=in_stock',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        ids = [x['id'] for x in resp.json()['data']]
        self.assertIn(p.id, ids)

    def test_filter_stock_status_out_of_stock(self):
        p = Product.objects.create(name='OOS Product', category=self.cat_testing)
        sku = SKU.objects.create(product=p, code='STK-02')
        StockLevel.objects.create(sku=sku, quantity_on_hand=0, reorder_point=10)
        resp = self.client.get(
            '/api/inventory/products/?stock_status=out_of_stock',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        ids = [x['id'] for x in resp.json()['data']]
        self.assertIn(p.id, ids)

    # === DUPLICATE SKU ===

    def test_duplicate_sku_returns_409(self):
        headers = {'HTTP_AUTHORIZATION': self._auth_header(self.admin)}
        p = Product.objects.create(name='Dup Product', category=self.cat_testing)
        SKU.objects.create(product=p, code='DUP-001')
        resp = self.client.post(
            '/api/inventory/skus/',
            {'code': 'DUP-001', 'product': p.id},
            format='json',
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
