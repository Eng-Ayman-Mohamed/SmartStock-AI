from decimal import Decimal

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import CustomUser
from apps.inventory.models import SKU, Category, Product, Supplier
from apps.purchasing.models import PurchaseOrder


class PurchasingEndpointTests(APITestCase):
    """Integration tests for purchasing API endpoints."""

    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_user(
            email='admin@purchasing.com',
            username='admin@purchasing.com',
            password='testpass123',
            role='admin',
        )
        cls.manager = CustomUser.objects.create_user(
            email='manager@purchasing.com',
            username='manager@purchasing.com',
            password='testpass123',
            role='manager',
        )
        cls.viewer = CustomUser.objects.create_user(
            email='viewer@purchasing.com',
            username='viewer@purchasing.com',
            password='testpass123',
            role='viewer',
        )

        cls.category = Category.objects.create(name='Purchasing Test Category')
        cls.product = Product.objects.create(
            name='Purchasing Test Product',
            category=cls.category,
        )
        cls.sku = SKU.objects.create(product=cls.product, code='PO-SKU-001')
        cls.supplier = Supplier.objects.create(
            name='Purchasing Test Supplier',
            contact_email='supplier@purchasing.com',
            default_lead_time_days=7,
        )

    def setUp(self):
        cache.clear()

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    # ──────────────────────────────────────────────
    #  SUPPLIER CRUD (via purchasing endpoint)
    # ──────────────────────────────────────────────

    def test_list_suppliers_authenticated(self):
        """Any authenticated user can list suppliers."""
        resp = self.client.get(
            '/api/purchasing/suppliers/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn('status', data)
        self.assertIn('data', data)
        self.assertIn('meta', data)
        self.assertEqual(data['status'], 'success')

    def test_list_suppliers_unauthenticated(self):
        """Unauthenticated request returns 401."""
        resp = self.client.get('/api/purchasing/suppliers/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_supplier_as_manager(self):
        """Manager can create a supplier."""
        payload = {
            'name': 'New Manager Supplier',
            'contact_email': 'new@supplier.com',
            'contact_phone': '01000000001',
            'default_lead_time_days': 10,
        }
        resp = self.client.post(
            '/api/purchasing/suppliers/',
            payload,
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json()['data']['name'], 'New Manager Supplier')

    def test_create_supplier_as_admin(self):
        """Admin can create a supplier."""
        payload = {
            'name': 'Admin Created Supplier',
            'contact_email': 'admin@supplier.com',
        }
        resp = self.client.post(
            '/api/purchasing/suppliers/',
            payload,
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_create_supplier_as_viewer_fails(self):
        """Viewer cannot create a supplier."""
        payload = {
            'name': 'Viewer Supplier',
            'contact_email': 'viewer@supplier.com',
        }
        resp = self.client.post(
            '/api/purchasing/suppliers/',
            payload,
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_supplier_unauthenticated_fails(self):
        """Unauthenticated user cannot create a supplier."""
        payload = {
            'name': 'Ghost Supplier',
            'contact_email': 'ghost@supplier.com',
        }
        resp = self.client.post(
            '/api/purchasing/suppliers/',
            payload,
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_supplier(self):
        """Any authenticated user can retrieve a supplier."""
        resp = self.client.get(
            f'/api/purchasing/suppliers/{self.supplier.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['data']['name'], 'Purchasing Test Supplier')

    def test_retrieve_supplier_unauthenticated(self):
        """Unauthenticated retrieve returns 401."""
        resp = self.client.get(f'/api/purchasing/suppliers/{self.supplier.id}/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_nonexistent_supplier(self):
        """Retrieving a non-existent supplier returns 404."""
        resp = self.client.get(
            '/api/purchasing/suppliers/99999/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_supplier_as_manager(self):
        """Manager can update a supplier."""
        supplier = Supplier.objects.create(
            name='Update Me', contact_email='update@supplier.com'
        )
        resp = self.client.patch(
            f'/api/purchasing/suppliers/{supplier.id}/',
            {'name': 'Updated Name'},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['data']['name'], 'Updated Name')

    def test_update_supplier_as_viewer_fails(self):
        """Viewer cannot update a supplier."""
        supplier = Supplier.objects.create(
            name='Viewer Update', contact_email='vu@supplier.com'
        )
        resp = self.client.patch(
            f'/api/purchasing/suppliers/{supplier.id}/',
            {'name': 'Hacked'},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_supplier_as_admin(self):
        """Admin can delete a supplier."""
        supplier = Supplier.objects.create(
            name='Admin Delete', contact_email='del@supplier.com'
        )
        resp = self.client.delete(
            f'/api/purchasing/suppliers/{supplier.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_supplier_as_manager_fails(self):
        """Manager cannot delete a supplier (admin-only)."""
        supplier = Supplier.objects.create(
            name='Manager Delete', contact_email='mdel@supplier.com'
        )
        resp = self.client.delete(
            f'/api/purchasing/suppliers/{supplier.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_supplier_as_viewer_fails(self):
        """Viewer cannot delete a supplier."""
        supplier = Supplier.objects.create(
            name='Viewer Delete', contact_email='vdel@supplier.com'
        )
        resp = self.client.delete(
            f'/api/purchasing/suppliers/{supplier.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_supplier_unauthenticated_fails(self):
        """Unauthenticated user cannot delete a supplier."""
        supplier = Supplier.objects.create(
            name='Unauth Delete', contact_email='udel@supplier.com'
        )
        resp = self.client.delete(
            f'/api/purchasing/suppliers/{supplier.id}/',
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ──────────────────────────────────────────────
    #  PURCHASE ORDER CRUD
    # ──────────────────────────────────────────────

    def _valid_po_payload(self):
        return {
            'sku': self.sku.id,
            'supplier': self.supplier.id,
            'quantity': 50,
            'total_cost': '750.00',
            'notes': 'Integration test PO',
        }

    def test_po_create_as_manager(self):
        """Manager can create a purchase order."""
        payload = self._valid_po_payload()
        resp = self.client.post(
            '/api/purchasing/orders/',
            payload,
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.json()['data']
        self.assertEqual(data['quantity'], 50)
        self.assertEqual(data['status'], 'draft')
        self.assertIsNone(data.get('approved_by'))

    def test_po_create_as_admin(self):
        """Admin can create a purchase order."""
        payload = self._valid_po_payload()
        resp = self.client.post(
            '/api/purchasing/orders/',
            payload,
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json()['data']['status'], 'draft')

    def test_po_create_as_viewer_fails(self):
        """Viewer cannot create a purchase order."""
        payload = self._valid_po_payload()
        resp = self.client.post(
            '/api/purchasing/orders/',
            payload,
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_po_create_unauthenticated_fails(self):
        """Unauthenticated user cannot create a purchase order."""
        payload = self._valid_po_payload()
        resp = self.client.post(
            '/api/purchasing/orders/',
            payload,
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_po_create_missing_required_fields(self):
        """Creating a PO without required fields returns 422."""
        resp = self.client.post(
            '/api/purchasing/orders/',
            {'notes': 'incomplete'},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        body = resp.json()
        self.assertIn('fields', body)
        # sku, supplier, quantity, total_cost should all be flagged
        self.assertIn('sku', body['fields'])
        self.assertIn('supplier', body['fields'])
        self.assertIn('quantity', body['fields'])
        self.assertIn('total_cost', body['fields'])

    def test_po_list_as_viewer(self):
        """Viewer can list purchase orders."""
        PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=10,
            total_cost=Decimal('100.00'),
        )
        resp = self.client.get(
            '/api/purchasing/orders/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn('data', data)
        self.assertIn('meta', data)
        self.assertGreaterEqual(len(data['data']), 1)

    def test_po_list_unauthenticated(self):
        """Unauthenticated user cannot list purchase orders."""
        resp = self.client.get('/api/purchasing/orders/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_po_retrieve(self):
        """Any authenticated user can retrieve a PO by ID."""
        po = PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=5,
            total_cost=Decimal('75.00'),
            notes='retrieve me',
        )
        resp = self.client.get(
            f'/api/purchasing/orders/{po.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['data']['quantity'], 5)
        self.assertEqual(resp.json()['data']['notes'], 'retrieve me')

    def test_po_retrieve_nonexistent(self):
        """Retrieving a non-existent PO returns 404."""
        resp = self.client.get(
            '/api/purchasing/orders/99999/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_po_update_as_manager(self):
        """Manager can update a purchase order."""
        po = PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=10,
            total_cost=Decimal('200.00'),
            notes='original note',
        )
        resp = self.client.patch(
            f'/api/purchasing/orders/{po.id}/',
            {'quantity': 25, 'notes': 'updated note'},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['data']['quantity'], 25)
        self.assertEqual(resp.json()['data']['notes'], 'updated note')
        # read_only fields should not be affected by the update
        self.assertEqual(resp.json()['data']['status'], 'draft')

    def test_po_update_as_viewer_fails(self):
        """Viewer cannot update a purchase order."""
        po = PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=3,
            total_cost=Decimal('30.00'),
        )
        resp = self.client.patch(
            f'/api/purchasing/orders/{po.id}/',
            {'quantity': 100},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_po_delete_as_manager(self):
        """Manager can delete a purchase order."""
        po = PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=1,
            total_cost=Decimal('10.00'),
        )
        resp = self.client.delete(
            f'/api/purchasing/orders/{po.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PurchaseOrder.objects.filter(pk=po.id).exists())

    def test_po_delete_as_viewer_fails(self):
        """Viewer cannot delete a purchase order."""
        po = PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=1,
            total_cost=Decimal('10.00'),
        )
        resp = self.client.delete(
            f'/api/purchasing/orders/{po.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_po_delete_unauthenticated_fails(self):
        """Unauthenticated user cannot delete a purchase order."""
        po = PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=1,
            total_cost=Decimal('10.00'),
        )
        resp = self.client.delete(
            f'/api/purchasing/orders/{po.id}/',
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ──────────────────────────────────────────────
    #  PO LIFECYCLE (draft → approve → approved)
    # ──────────────────────────────────────────────

    def test_po_draft_to_approve_lifecycle(self):
        """Full PO lifecycle: draft → list → retrieve → approve → verify."""
        headers = {'HTTP_AUTHORIZATION': self._auth_header(self.manager)}

        # 1. Draft the PO
        payload = self._valid_po_payload()
        resp = self.client.post(
            '/api/purchasing/orders/', payload, format='json', **headers
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        po_id = resp.json()['data']['id']
        self.assertEqual(resp.json()['data']['status'], 'draft')

        # 2. List POs – the new PO should appear
        resp = self.client.get('/api/purchasing/orders/', **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        po_ids = [po['id'] for po in resp.json()['data']]
        self.assertIn(po_id, po_ids)

        # 3. Retrieve the PO – confirm draft status
        resp = self.client.get(f'/api/purchasing/orders/{po_id}/', **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['data']['status'], 'draft')

        # 4. Approve the PO
        resp = self.client.post(
            f'/api/purchasing/orders/{po_id}/approve/', **headers
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        approve_data = resp.json()
        self.assertEqual(approve_data['status'], 'success')
        self.assertEqual(approve_data['data']['status'], 'approved')
        self.assertEqual(approve_data['data']['po_id'], po_id)

        # 5. Retrieve again – status should now be 'approved'
        resp = self.client.get(f'/api/purchasing/orders/{po_id}/', **headers)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()['data']['status'], 'approved')

    def test_approve_non_draft_po_fails(self):
        """Approving a non-draft PO returns 409 conflict."""
        po = PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=5,
            total_cost=Decimal('50.00'),
            status='approved',
        )
        resp = self.client.post(
            f'/api/purchasing/orders/{po.id}/approve/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        body = resp.json()
        self.assertEqual(body['status'], 'error')
        self.assertIn('Only draft orders can be approved', str(body))

    def test_approve_po_already_approved_fails(self):
        """Approving an already-approved PO returns 409."""
        po = PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=10,
            total_cost=Decimal('150.00'),
            status='approved',
            approved_by=self.admin,
        )
        resp = self.client.post(
            f'/api/purchasing/orders/{po.id}/approve/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_approve_cancelled_po_fails(self):
        """Approving a cancelled PO returns 409."""
        po = PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=10,
            total_cost=Decimal('150.00'),
            status='cancelled',
        )
        resp = self.client.post(
            f'/api/purchasing/orders/{po.id}/approve/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_approve_po_as_viewer_fails(self):
        """Viewer cannot approve a purchase order."""
        po = PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=5,
            total_cost=Decimal('50.00'),
            status='draft',
        )
        resp = self.client.post(
            f'/api/purchasing/orders/{po.id}/approve/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_po_as_admin(self):
        """Admin can approve a purchase order."""
        po = PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=20,
            total_cost=Decimal('300.00'),
            status='draft',
        )
        resp = self.client.post(
            f'/api/purchasing/orders/{po.id}/approve/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        po.refresh_from_db()
        self.assertEqual(po.status, 'approved')
        self.assertEqual(po.approved_by, self.admin)

    def test_approve_po_unauthenticated_fails(self):
        """Unauthenticated user cannot approve a purchase order."""
        po = PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=5,
            total_cost=Decimal('50.00'),
            status='draft',
        )
        resp = self.client.post(
            f'/api/purchasing/orders/{po.id}/approve/',
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_approve_nonexistent_po_returns_404(self):
        """Approving a non-existent PO returns 404."""
        resp = self.client.post(
            '/api/purchasing/orders/99999/approve/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        body = resp.json()
        self.assertEqual(body['status'], 'error')

    # ──────────────────────────────────────────────
    #  RESPONSE ENVELOPE SHAPE
    # ──────────────────────────────────────────────

    def test_success_response_envelope(self):
        """List endpoints return the standard success envelope."""
        resp = self.client.get(
            '/api/purchasing/suppliers/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        data = resp.json()
        self.assertIn('status', data)
        self.assertIn('data', data)
        self.assertIn('meta', data)
        self.assertEqual(data['status'], 'success')

    def test_error_response_envelope(self):
        """Non-existent resource returns the standard error envelope."""
        resp = self.client.get(
            '/api/purchasing/suppliers/99999/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        data = resp.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('error', data)
        self.assertIn('message', data)
        self.assertIn('code', data)

    # ──────────────────────────────────────────────
    #  READ_ONLY FIELDS
    # ──────────────────────────────────────────────

    def test_po_read_only_status_ignored_on_create(self):
        """The 'status' field is read-only; provided value is ignored."""
        payload = self._valid_po_payload()
        payload['status'] = 'approved'
        resp = self.client.post(
            '/api/purchasing/orders/',
            payload,
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # The serializer ignores the provided status and defaults to 'draft'
        self.assertEqual(resp.json()['data']['status'], 'draft')

    def test_po_read_only_fields_not_updatable(self):
        """status, requested_by, approved_by are read-only on update."""
        po = PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=10,
            total_cost=Decimal('200.00'),
        )
        resp = self.client.patch(
            f'/api/purchasing/orders/{po.id}/',
            {'status': 'approved', 'quantity': 99},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()['data']
        # quantity was updated
        self.assertEqual(data['quantity'], 99)
        # status should still be 'draft' (read-only)
        self.assertEqual(data['status'], 'draft')

    # ──────────────────────────────────────────────
    #  PERMISSION EDGE CASES
    # ──────────────────────────────────────────────

    def test_viewer_can_list_orders(self):
        """Viewer has read access to PO list."""
        resp = self.client.get(
            '/api/purchasing/orders/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_viewer_can_retrieve_order(self):
        """Viewer has read access to individual PO."""
        po = PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=2,
            total_cost=Decimal('20.00'),
        )
        resp = self.client.get(
            f'/api/purchasing/orders/{po.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_admin_can_list_and_retrieve_orders(self):
        """Admin has full read access to POs."""
        po = PurchaseOrder.objects.create(
            sku=self.sku,
            supplier=self.supplier,
            quantity=7,
            total_cost=Decimal('70.00'),
        )
        # List
        resp = self.client.get(
            '/api/purchasing/orders/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Retrieve
        resp = self.client.get(
            f'/api/purchasing/orders/{po.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_viewer_can_list_suppliers(self):
        """Viewer has read access to supplier list."""
        resp = self.client.get(
            '/api/purchasing/suppliers/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_viewer_can_retrieve_supplier(self):
        """Viewer has read access to individual supplier."""
        resp = self.client.get(
            f'/api/purchasing/suppliers/{self.supplier.id}/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
