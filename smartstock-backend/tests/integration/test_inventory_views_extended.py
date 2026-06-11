from decimal import Decimal

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import CustomUser
from apps.inventory.models import SKU, Category, Product, SalesRecord, StockLevel, Supplier


class InventoryTestBase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            username='inv_admin', email='inv_admin@test.com', password='pass123', role='admin'
        )
        cls.manager = CustomUser.objects.create_user(
            username='inv_manager', email='inv_manager@test.com', password='pass123', role='manager'
        )
        cls.viewer = CustomUser.objects.create_user(
            username='inv_viewer', email='inv_viewer@test.com', password='pass123', role='viewer'
        )
        cls.category = Category.objects.create(name='Electronics')
        cls.supplier = Supplier.objects.create(
            name='Acme Corp', contact_email='acme@test.com', default_lead_time_days=7
        )
        cls.product = Product.objects.create(
            name='Widget',
            category=cls.category,
            supplier=cls.supplier,
            unit_price=Decimal('29.99'),
            unit_of_measure='pcs',
            reorder_point=10,
            safety_stock=5,
        )
        cls.sku = SKU.objects.create(product=cls.product, code='WDG-001')
        cls.stock_level = StockLevel.objects.create(
            sku=cls.sku,
            quantity_on_hand=50,
            quantity_reserved=0,
            reorder_point=10,
            reorder_quantity=25,
        )
        cls.sales_record = SalesRecord.objects.create(
            sku=cls.sku, date='2026-01-15', quantity_sold=20
        )

    def _auth(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')


class ProductViewSetCRUDTests(InventoryTestBase):
    def setUp(self):
        cache.clear()

    def test_list_products(self):
        self._auth(self.viewer)
        resp = self.client.get('/api/inventory/products/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_products_caching(self):
        self._auth(self.viewer)
        cache.clear()
        self.client.get('/api/inventory/products/')
        resp = self.client.get('/api/inventory/products/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_product(self):
        self._auth(self.viewer)
        resp = self.client.get(f'/api/inventory/products/{self.product.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_product_as_manager(self):
        self._auth(self.manager)
        resp = self.client.post(
            '/api/inventory/products/',
            {
                'name': 'New Gadget',
                'category': self.category.id,
                'supplier': self.supplier.id,
                'unit_price': '19.99',
                'unit_of_measure': 'pcs',
                'reorder_point': 5,
                'safety_stock': 2,
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_product_validation_error_empty_name(self):
        self._auth(self.manager)
        resp = self.client.post(
            '/api/inventory/products/',
            {'name': '', 'category': self.category.id},
            format='json',
        )
        self.assertIn(
            resp.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
        )

    def test_create_product_validation_error_short_name(self):
        self._auth(self.manager)
        resp = self.client.post(
            '/api/inventory/products/',
            {'name': 'A', 'category': self.category.id},
            format='json',
        )
        self.assertIn(
            resp.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
        )

    def test_create_product_validation_error_negative_price(self):
        self._auth(self.manager)
        resp = self.client.post(
            '/api/inventory/products/',
            {'name': 'Bad Price', 'category': self.category.id, 'unit_price': '-5.00'},
            format='json',
        )
        self.assertIn(
            resp.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
        )

    def test_update_product(self):
        self._auth(self.manager)
        resp = self.client.patch(
            f'/api/inventory/products/{self.product.id}/',
            {'name': 'Updated Widget'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_update_product_as_viewer_fails(self):
        self._auth(self.viewer)
        resp = self.client.patch(
            f'/api/inventory/products/{self.product.id}/',
            {'name': 'Nope'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_product_as_admin(self):
        self._auth(self.admin)
        product = Product.objects.create(name='ToDelete', category=self.category)
        resp = self.client.delete(f'/api/inventory/products/{product.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        product.refresh_from_db()
        self.assertFalse(product.is_active)

    def test_destroy_product_as_viewer_fails(self):
        self._auth(self.viewer)
        resp = self.client.delete(f'/api/inventory/products/{self.product.id}/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_product_404(self):
        self._auth(self.admin)
        resp = self.client.delete('/api/inventory/products/99999/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_products_unauthenticated(self):
        resp = self.client.get('/api/inventory/products/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class SKUViewSetCRUDTests(InventoryTestBase):
    def test_list_skus(self):
        self._auth(self.viewer)
        resp = self.client.get('/api/inventory/skus/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_sku(self):
        self._auth(self.viewer)
        resp = self.client.get(f'/api/inventory/skus/{self.sku.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_sku_as_manager(self):
        self._auth(self.manager)
        resp = self.client.post(
            '/api/inventory/skus/',
            {'product': self.product.id, 'code': 'WDG-002'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_sku_validation_error_invalid_code(self):
        self._auth(self.manager)
        resp = self.client.post(
            '/api/inventory/skus/',
            {'product': self.product.id, 'code': 'invalid code!@#'},
            format='json',
        )
        self.assertIn(
            resp.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
        )

    def test_create_sku_code_normalized_uppercase(self):
        self._auth(self.manager)
        resp = self.client.post(
            '/api/inventory/skus/',
            {'product': self.product.id, 'code': 'lower-case-sku'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['code'], 'LOWER-CASE-SKU')

    def test_update_sku(self):
        self._auth(self.manager)
        resp = self.client.patch(
            f'/api/inventory/skus/{self.sku.id}/',
            {'code': 'WDG-001-NEW'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_destroy_sku_as_admin(self):
        self._auth(self.admin)
        sku = SKU.objects.create(product=self.product, code='DEL-SKU')
        resp = self.client.delete(f'/api/inventory/skus/{sku.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_destroy_sku_404(self):
        self._auth(self.admin)
        resp = self.client.delete('/api/inventory/skus/99999/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_destroy_sku_as_viewer_fails(self):
        self._auth(self.viewer)
        resp = self.client.delete(f'/api/inventory/skus/{self.sku.id}/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class StockLevelViewSetCRUDTests(InventoryTestBase):
    def test_list_stock_levels(self):
        self._auth(self.viewer)
        resp = self.client.get('/api/inventory/stock-levels/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_stock_level(self):
        self._auth(self.viewer)
        resp = self.client.get(f'/api/inventory/stock-levels/{self.stock_level.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_stock_level_as_manager(self):
        self._auth(self.manager)
        sku2 = SKU.objects.create(product=self.product, code='WDG-003')
        resp = self.client.post(
            '/api/inventory/stock-levels/',
            {'sku': sku2.id, 'quantity_on_hand': 100, 'reorder_point': 10, 'reorder_quantity': 25},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_update_stock_level(self):
        self._auth(self.manager)
        resp = self.client.patch(
            f'/api/inventory/stock-levels/{self.stock_level.id}/',
            {'quantity_on_hand': 75},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_destroy_stock_level_as_admin(self):
        self._auth(self.admin)
        resp = self.client.delete(f'/api/inventory/stock-levels/{self.stock_level.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_low_stock_action(self):
        self._auth(self.viewer)
        self.stock_level.quantity_on_hand = 2
        self.stock_level.save()
        resp = self.client.get('/api/inventory/stock-levels/low_stock/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_low_stock_action_empty(self):
        self._auth(self.viewer)
        self.stock_level.quantity_on_hand = 999
        self.stock_level.save()
        resp = self.client.get('/api/inventory/stock-levels/low_stock/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class StockAdjustViewTests(InventoryTestBase):
    def test_adjust_stock_valid_positive(self):
        self._auth(self.manager)
        url = f'/api/inventory/stock/{self.product.id}/'
        resp = self.client.patch(url, {'quantity_delta': 10}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_adjust_stock_valid_negative(self):
        self._auth(self.manager)
        url = f'/api/inventory/stock/{self.product.id}/'
        resp = self.client.patch(url, {'quantity_delta': -10}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_adjust_stock_missing_quantity_delta(self):
        self._auth(self.manager)
        url = f'/api/inventory/stock/{self.product.id}/'
        resp = self.client.patch(url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_adjust_stock_negative_makes_negative(self):
        self._auth(self.manager)
        url = f'/api/inventory/stock/{self.product.id}/'
        resp = self.client.patch(url, {'quantity_delta': -100}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_adjust_stock_non_integer_delta(self):
        self._auth(self.manager)
        url = f'/api/inventory/stock/{self.product.id}/'
        resp = self.client.patch(url, {'quantity_delta': 'abc'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_adjust_stock_not_found(self):
        self._auth(self.manager)
        resp = self.client.patch(
            '/api/inventory/stock/99999/', {'quantity_delta': 1}, format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_adjust_stock_as_viewer_fails(self):
        self._auth(self.viewer)
        url = f'/api/inventory/stock/{self.product.id}/'
        resp = self.client.patch(url, {'quantity_delta': 1}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_adjust_stock_with_reason(self):
        self._auth(self.manager)
        url = f'/api/inventory/stock/{self.product.id}/'
        resp = self.client.patch(url, {'quantity_delta': 5, 'reason': 'Restock'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class SalesRecordViewSetCRUDTests(InventoryTestBase):
    def test_list_sales_records(self):
        self._auth(self.viewer)
        resp = self.client.get('/api/inventory/sales-records/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_sales_record(self):
        self._auth(self.manager)
        resp = self.client.post(
            '/api/inventory/sales-records/',
            {'sku': self.sku.id, 'date': '2026-02-01', 'quantity_sold': 30},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_sales_record_as_viewer_fails(self):
        self._auth(self.viewer)
        resp = self.client.post(
            '/api/inventory/sales-records/',
            {'sku': self.sku.id, 'date': '2026-03-01', 'quantity_sold': 5},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_sales_record(self):
        self._auth(self.manager)
        resp = self.client.patch(
            f'/api/inventory/sales-records/{self.sales_record.id}/',
            {'quantity_sold': 25},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_destroy_sales_record(self):
        self._auth(self.admin)
        resp = self.client.delete(f'/api/inventory/sales-records/{self.sales_record.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


class SupplierViewSetCRUDTests(InventoryTestBase):
    def test_list_suppliers(self):
        self._auth(self.viewer)
        resp = self.client.get('/api/inventory/suppliers/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_supplier(self):
        self._auth(self.manager)
        resp = self.client.post(
            '/api/inventory/suppliers/',
            {'name': 'New Supplier', 'contact_email': 'new@test.com', 'default_lead_time_days': 5},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_supplier_validation_error_missing_name(self):
        self._auth(self.manager)
        resp = self.client.post(
            '/api/inventory/suppliers/',
            {'contact_email': 'test@test.com', 'default_lead_time_days': 5},
            format='json',
        )
        self.assertIn(
            resp.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
        )

    def test_create_supplier_validation_error_missing_email(self):
        self._auth(self.manager)
        resp = self.client.post(
            '/api/inventory/suppliers/',
            {'name': 'No Email', 'default_lead_time_days': 5},
            format='json',
        )
        self.assertIn(
            resp.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
        )

    def test_update_supplier(self):
        self._auth(self.manager)
        resp = self.client.patch(
            f'/api/inventory/suppliers/{self.supplier.id}/',
            {'name': 'Updated Supplier'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_destroy_supplier(self):
        self._auth(self.admin)
        supplier = Supplier.objects.create(
            name='To Delete', contact_email='del@test.com', default_lead_time_days=3
        )
        resp = self.client.delete(f'/api/inventory/suppliers/{supplier.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)


class CategoryViewSetTests(InventoryTestBase):
    def test_list_categories(self):
        self._auth(self.viewer)
        resp = self.client.get('/api/inventory/categories/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_category(self):
        self._auth(self.viewer)
        resp = self.client.get(f'/api/inventory/categories/{self.category.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_category_404(self):
        self._auth(self.viewer)
        resp = self.client.get('/api/inventory/categories/99999/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
