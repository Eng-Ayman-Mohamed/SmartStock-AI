"""Extended integration tests for inventory views — covers uncovered code paths.

See test_inventory_endpoints.py for the baseline test coverage.
This file targets specific view actions and edge cases not yet covered:
  - Product update/destroy with role-based permission checks
  - Full SKU CRUD (create, update, delete) + list + filter
  - StockLevel retrieve (single)
  - SalesRecord create + list
  - Supplier retrieve + manager-delete-fails
  - Viewer-level permission checks for writes
"""

from datetime import date, timedelta

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import CustomUser
from apps.inventory.models import SKU, Category, Product, SalesRecord, StockLevel, Supplier


class ProductExtendedTests(APITestCase):
    """Product endpoint tests: update, destroy, and permission checks."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            email='admin-ext@test.com',
            username='admin-ext@test.com',
            password='testpass123',
            role='admin',
        )
        cls.manager = CustomUser.objects.create_user(
            email='mgr-ext@test.com',
            username='mgr-ext@test.com',
            password='testpass123',
            role='manager',
        )
        cls.viewer = CustomUser.objects.create_user(
            email='viewer-ext@test.com',
            username='viewer-ext@test.com',
            password='testpass123',
            role='viewer',
        )
        cls.category = Category.objects.create(name='Extended Test Cat')

    def setUp(self):
        cache.clear()

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    # ---- Product update ----

    def test_update_product_as_manager(self):
        """Manager can update a product (partial_update / PATCH)."""
        product = Product.objects.create(
            name='Original Name',
            description='Original description',
            category=self.category,
        )
        headers = {'HTTP_AUTHORIZATION': self._auth_header(self.manager)}
        payload = {
            'name': 'Updated Name',
            'description': 'Updated description',
        }
        resp = self.client.patch(
            f'/api/inventory/products/{product.id}/',
            payload,
            format='json',
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['data']['name'], 'Updated Name')
        self.assertEqual(data['data']['description'], 'Updated description')

        # Verify persistence
        product.refresh_from_db()
        self.assertEqual(product.name, 'Updated Name')

    def test_update_product_as_viewer_fails(self):
        """Viewer cannot update a product."""
        product = Product.objects.create(
            name='Viewer Update Test',
            category=self.category,
        )
        headers = {'HTTP_AUTHORIZATION': self._auth_header(self.viewer)}
        resp = self.client.patch(
            f'/api/inventory/products/{product.id}/',
            {'name': 'Hacked Name'},
            format='json',
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ---- Product destroy ----

    def test_delete_product_as_admin(self):
        """Admin can soft-delete a product."""
        product = Product.objects.create(
            name='Admin Delete Me',
            category=self.category,
        )
        pid = product.id
        headers = {'HTTP_AUTHORIZATION': self._auth_header(self.admin)}
        resp = self.client.delete(f'/api/inventory/products/{pid}/', **headers)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # Product should be gone from default queryset (soft delete)
        resp = self.client.get(f'/api/inventory/products/{pid}/', **headers)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_product_as_manager_fails(self):
        """Manager cannot delete a product (403 Forbidden)."""
        product = Product.objects.create(
            name='Manager Delete Fail',
            category=self.category,
        )
        headers = {'HTTP_AUTHORIZATION': self._auth_header(self.manager)}
        resp = self.client.delete(
            f'/api/inventory/products/{product.id}/',
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Product must still exist
        product.refresh_from_db()
        self.assertTrue(product.is_active)

    def test_delete_product_as_viewer_fails(self):
        """Viewer cannot delete a product (403 Forbidden)."""
        product = Product.objects.create(
            name='Viewer Delete Fail',
            category=self.category,
        )
        headers = {'HTTP_AUTHORIZATION': self._auth_header(self.viewer)}
        resp = self.client.delete(
            f'/api/inventory/products/{product.id}/',
            **headers,
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class SKUExtendedTests(APITestCase):
    """Full SKU CRUD, list, and filter coverage."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            email='sku-admin@test.com',
            username='sku-admin@test.com',
            password='testpass123',
            role='admin',
        )
        cls.manager = CustomUser.objects.create_user(
            email='sku-mgr@test.com',
            username='sku-mgr@test.com',
            password='testpass123',
            role='manager',
        )
        cls.viewer = CustomUser.objects.create_user(
            email='sku-viewer@test.com',
            username='sku-viewer@test.com',
            password='testpass123',
            role='viewer',
        )
        cls.category = Category.objects.create(name='SKU Test Cat')
        cls.product_a = Product.objects.create(
            name='Product A',
            category=cls.category,
        )
        cls.product_b = Product.objects.create(
            name='Product B',
            category=cls.category,
        )

    def setUp(self):
        cache.clear()
        # Ensure clean state per test
        SKU.objects.filter(code__startswith='EXT-').delete()

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    def _manager_headers(self):
        return {'HTTP_AUTHORIZATION': self._auth_header(self.manager)}

    def _admin_headers(self):
        return {'HTTP_AUTHORIZATION': self._auth_header(self.admin)}

    # ---- SKU Create ----

    def test_create_sku(self):
        """Manager can create a SKU for a product."""
        payload = {
            'code': 'EXT-SKU-001',
            'product': self.product_a.id,
        }
        resp = self.client.post(
            '/api/inventory/skus/',
            payload,
            format='json',
            **self._manager_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['data']['code'], 'EXT-SKU-001')
        self.assertEqual(data['data']['product'], self.product_a.id)

    def test_create_sku_as_viewer_fails(self):
        """Viewer cannot create a SKU."""
        payload = {
            'code': 'EXT-SKU-VIEWER',
            'product': self.product_a.id,
        }
        resp = self.client.post(
            '/api/inventory/skus/',
            payload,
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ---- SKU Update ----

    def test_update_sku(self):
        """Manager can update a SKU code."""
        sku = SKU.objects.create(product=self.product_a, code='EXT-OLD-CODE')

        resp = self.client.patch(
            f'/api/inventory/skus/{sku.id}/',
            {'code': 'EXT-NEW-CODE'},
            format='json',
            **self._manager_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['data']['code'], 'EXT-NEW-CODE')

        sku.refresh_from_db()
        self.assertEqual(sku.code, 'EXT-NEW-CODE')

    def test_update_sku_as_viewer_fails(self):
        """Viewer cannot update a SKU."""
        sku = SKU.objects.create(product=self.product_a, code='EXT-NO-UPDATE')

        resp = self.client.patch(
            f'/api/inventory/skus/{sku.id}/',
            {'code': 'EXT-HACKED'},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ---- SKU Delete ----

    def test_delete_sku(self):
        """Admin can delete a SKU."""
        sku = SKU.objects.create(product=self.product_a, code='EXT-DEL-ME')

        resp = self.client.delete(
            f'/api/inventory/skus/{sku.id}/',
            **self._admin_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # SKU must be gone
        self.assertFalse(SKU.objects.filter(id=sku.id).exists())

    def test_delete_sku_as_manager_fails(self):
        """Manager cannot delete a SKU."""
        sku = SKU.objects.create(product=self.product_a, code='EXT-MGR-DEL-FAIL')

        resp = self.client.delete(
            f'/api/inventory/skus/{sku.id}/',
            **self._manager_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # SKU must still exist
        self.assertTrue(SKU.objects.filter(id=sku.id).exists())

    def test_delete_sku_as_viewer_fails(self):
        """Viewer cannot delete a SKU."""
        sku = SKU.objects.create(product=self.product_a, code='EXT-VIEW-DEL-FAIL')

        resp = self.client.delete(
            f'/api/inventory/skus/{sku.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # ---- SKU List ----

    def test_list_skus(self):
        """Authenticated user can list SKUs with envelope."""
        SKU.objects.create(product=self.product_a, code='EXT-LIST-01')
        SKU.objects.create(product=self.product_b, code='EXT-LIST-02')

        resp = self.client.get(
            '/api/inventory/skus/',
            **self._manager_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)
        self.assertIn('meta', data)
        # At least our two SKUs are present
        codes = [s['code'] for s in data['data']]
        self.assertIn('EXT-LIST-01', codes)
        self.assertIn('EXT-LIST-02', codes)

    def test_list_skus_unauthenticated(self):
        """Unauthenticated request for SKUs returns 401."""
        resp = self.client.get('/api/inventory/skus/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---- SKU Filter ----

    def test_filter_sku_by_code(self):
        """Filter SKUs by code (icontains)."""
        SKU.objects.create(product=self.product_a, code='EXT-FILTER-ABC')
        SKU.objects.create(product=self.product_b, code='EXT-FILTER-XYZ')

        resp = self.client.get(
            '/api/inventory/skus/?code=ABC',
            **self._manager_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.json()['data']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['code'], 'EXT-FILTER-ABC')

    def test_filter_sku_by_product(self):
        """Filter SKUs by product ID."""
        SKU.objects.create(product=self.product_a, code='EXT-PROD-A')
        SKU.objects.create(product=self.product_b, code='EXT-PROD-B')

        resp = self.client.get(
            f'/api/inventory/skus/?product={self.product_a.id}',
            **self._manager_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.json()['data']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['code'], 'EXT-PROD-A')


class StockLevelExtendedTests(APITestCase):
    """StockLevel retrieve and listing."""

    @classmethod
    def setUpTestData(cls):
        cls.manager = CustomUser.objects.create_user(
            email='sl-mgr@test.com',
            username='sl-mgr@test.com',
            password='testpass123',
            role='manager',
        )
        cls.category = Category.objects.create(name='StockLevel Cat')
        cls.product = Product.objects.create(
            name='StockLevel Product',
            category=cls.category,
        )
        cls.sku = SKU.objects.create(product=cls.product, code='EXT-SL-001')
        cls.stock = StockLevel.objects.create(
            sku=cls.sku,
            quantity_on_hand=250,
            quantity_reserved=10,
            reorder_point=30,
            reorder_quantity=100,
        )

    def setUp(self):
        cache.clear()

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    # ---- StockLevel Retrieve ----

    def test_retrieve_stock_level(self):
        """Authenticated user can retrieve a single stock level."""
        resp = self.client.get(
            f'/api/inventory/stock-levels/{self.stock.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['data']['id'], self.stock.id)
        self.assertEqual(data['data']['quantity_on_hand'], 250)
        self.assertEqual(data['data']['quantity_reserved'], 10)
        self.assertEqual(data['data']['sku_code'], 'EXT-SL-001')

    def test_retrieve_stock_level_not_found(self):
        """Retrieving a non-existent stock level returns 404."""
        resp = self.client.get(
            '/api/inventory/stock-levels/99999/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.json()
        self.assertEqual(data['status'], 'error')

    def test_retrieve_stock_level_unauthenticated(self):
        """Unauthenticated request for a stock level returns 401."""
        resp = self.client.get(
            f'/api/inventory/stock-levels/{self.stock.id}/',
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class SalesRecordExtendedTests(APITestCase):
    """SalesRecord creation and listing coverage."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            email='sr-admin@test.com',
            username='sr-admin@test.com',
            password='testpass123',
            role='admin',
        )
        cls.manager = CustomUser.objects.create_user(
            email='sr-mgr@test.com',
            username='sr-mgr@test.com',
            password='testpass123',
            role='manager',
        )
        cls.viewer = CustomUser.objects.create_user(
            email='sr-viewer@test.com',
            username='sr-viewer@test.com',
            password='testpass123',
            role='viewer',
        )
        cls.category = Category.objects.create(name='SalesRecord Cat')
        cls.product = Product.objects.create(
            name='SalesRecord Product',
            category=cls.category,
        )
        cls.sku = SKU.objects.create(product=cls.product, code='EXT-SR-001')

    def setUp(self):
        cache.clear()

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    def _manager_headers(self):
        return {'HTTP_AUTHORIZATION': self._auth_header(self.manager)}

    # ---- SalesRecord Create ----

    def test_create_sales_record(self):
        """Manager can create a sales record."""
        payload = {
            'sku': self.sku.id,
            'date': str(date.today() - timedelta(days=1)),
            'quantity_sold': 15,
        }
        resp = self.client.post(
            '/api/inventory/sales-records/',
            payload,
            format='json',
            **self._manager_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['data']['quantity_sold'], 15)
        self.assertEqual(data['data']['sku_code'], 'EXT-SR-001')

    def test_create_sales_record_as_viewer_fails(self):
        """Viewer cannot create a sales record."""
        payload = {
            'sku': self.sku.id,
            'date': str(date.today() - timedelta(days=2)),
            'quantity_sold': 5,
        }
        resp = self.client.post(
            '/api/inventory/sales-records/',
            payload,
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_sales_record_duplicate_fails(self):
        """Creating a duplicate (sku + date) sales record fails."""
        yesterday = str(date.today() - timedelta(days=1))
        SalesRecord.objects.create(
            sku=self.sku,
            date=yesterday,
            quantity_sold=10,
        )
        payload = {
            'sku': self.sku.id,
            'date': yesterday,
            'quantity_sold': 20,
        }
        resp = self.client.post(
            '/api/inventory/sales-records/',
            payload,
            format='json',
            **self._manager_headers(),
        )
        # The unique_together constraint raises IntegrityError,
        # which propagates as a 422 Unprocessable Entity
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    # ---- SalesRecord List ----

    def test_list_sales_records(self):
        """Authenticated user can list sales records with envelope."""
        SalesRecord.objects.create(
            sku=self.sku,
            date=date.today() - timedelta(days=3),
            quantity_sold=8,
        )
        SalesRecord.objects.create(
            sku=self.sku,
            date=date.today() - timedelta(days=1),
            quantity_sold=12,
        )

        resp = self.client.get(
            '/api/inventory/sales-records/',
            **self._manager_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)
        self.assertIn('meta', data)
        self.assertGreaterEqual(len(data['data']), 2)

    def test_list_sales_records_unauthenticated(self):
        """Unauthenticated list returns 401."""
        resp = self.client.get('/api/inventory/sales-records/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class SupplierExtendedTests(APITestCase):
    """Supplier CRUD coverage: retrieve, update, and permission checks."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            email='sup-admin@test.com',
            username='sup-admin@test.com',
            password='testpass123',
            role='admin',
        )
        cls.manager = CustomUser.objects.create_user(
            email='sup-mgr@test.com',
            username='sup-mgr@test.com',
            password='testpass123',
            role='manager',
        )
        cls.viewer = CustomUser.objects.create_user(
            email='sup-viewer@test.com',
            username='sup-viewer@test.com',
            password='testpass123',
            role='viewer',
        )

    def setUp(self):
        cache.clear()

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    def _manager_headers(self):
        return {'HTTP_AUTHORIZATION': self._auth_header(self.manager)}

    def _admin_headers(self):
        return {'HTTP_AUTHORIZATION': self._auth_header(self.admin)}

    # ---- Supplier Retrieve ----

    def test_retrieve_supplier(self):
        """Authenticated user can retrieve a single supplier."""
        supplier = Supplier.objects.create(
            name='Retrieve Me',
            contact_email='retrieve@test.com',
        )
        resp = self.client.get(
            f'/api/inventory/suppliers/{supplier.id}/',
            **self._manager_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['data']['name'], 'Retrieve Me')
        self.assertEqual(data['data']['contact_email'], 'retrieve@test.com')

    def test_retrieve_supplier_not_found(self):
        """Non-existent supplier returns 404."""
        resp = self.client.get(
            '/api/inventory/suppliers/99999/',
            **self._manager_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.json()['status'], 'error')

    def test_retrieve_supplier_unauthenticated(self):
        """Unauthenticated retrieve returns 401."""
        supplier = Supplier.objects.create(
            name='Hidden Supplier',
            contact_email='hidden@test.com',
        )
        resp = self.client.get(f'/api/inventory/suppliers/{supplier.id}/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ---- Supplier Delete ----

    def test_delete_supplier_as_manager_fails(self):
        """Manager cannot delete a supplier (403 Forbidden)."""
        supplier = Supplier.objects.create(
            name='Manager Delete Supplier',
            contact_email='mgr-del@test.com',
        )
        resp = self.client.delete(
            f'/api/inventory/suppliers/{supplier.id}/',
            **self._manager_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Supplier must still exist
        self.assertTrue(Supplier.objects.filter(id=supplier.id).exists())

    # ---- Supplier Update ----

    def test_update_supplier_full(self):
        """Manager can fully update a supplier (PUT semantics via PATCH)."""
        supplier = Supplier.objects.create(
            name='Old Supplier',
            contact_email='old@test.com',
            contact_phone='1111111111',
            default_lead_time_days=10,
        )
        resp = self.client.patch(
            f'/api/inventory/suppliers/{supplier.id}/',
            {
                'name': 'Updated Supplier',
                'contact_email': 'updated@test.com',
                'default_lead_time_days': 14,
            },
            format='json',
            **self._manager_headers(),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()['data']
        self.assertEqual(data['name'], 'Updated Supplier')
        self.assertEqual(data['contact_email'], 'updated@test.com')
        self.assertEqual(data['default_lead_time_days'], 14)

        supplier.refresh_from_db()
        self.assertEqual(supplier.name, 'Updated Supplier')

    def test_update_supplier_as_viewer_fails(self):
        """Viewer cannot update a supplier."""
        supplier = Supplier.objects.create(
            name='Viewer Target',
            contact_email='viewer-target@test.com',
        )
        resp = self.client.patch(
            f'/api/inventory/suppliers/{supplier.id}/',
            {'name': 'Hacked'},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
