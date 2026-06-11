from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audit.models import AuditLog
from apps.authentication.models import CustomUser
from apps.inventory.models import SKU, Category, Product, StockLevel


class AuditLogEndpointTests(APITestCase):
    """Integration tests for audit log API endpoints."""

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

        # Seed audit log entries for listing and filtering tests
        AuditLog.objects.create(
            event='STOCK_ADJUSTED',
            user=cls.admin,
            entity_type='StockLevel',
            entity_id=1001,
            data_snapshot={
                'sku_code': 'FILTER-TEST-A',
                'delta': 20,
                'new_quantity': 120,
                'reason': 'Initial stock',
            },
        )
        AuditLog.objects.create(
            event='USER_LOGIN',
            user=cls.admin,
            entity_type='User',
            entity_id=cls.admin.id,
            data_snapshot={'path': '/api/auth/login/', 'method': 'POST'},
        )
        AuditLog.objects.create(
            event='PO_APPROVED',
            user=cls.admin,
            entity_type='PurchaseOrder',
            entity_id=5001,
            data_snapshot={'supplier': 'Test Supplier', 'amount': '1500.00'},
        )

    def _auth_header(self, user):
        refresh = RefreshToken.for_user(user)
        return f'Bearer {refresh.access_token}'

    # ------------------------------------------------------------------
    # Permission enforcement
    # ------------------------------------------------------------------

    def test_list_audit_logs_unauthenticated(self):
        """Unauthenticated users receive 401 Unauthorized."""
        resp = self.client.get('/api/audit/logs/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_audit_logs_as_viewer_fails(self):
        """Viewer role receives 403 Forbidden (IsAdminOnly)."""
        resp = self.client.get(
            '/api/audit/logs/',
            HTTP_AUTHORIZATION=self._auth_header(self.viewer),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_audit_logs_as_manager_fails(self):
        """Manager role receives 403 Forbidden (IsAdminOnly)."""
        resp = self.client.get(
            '/api/audit/logs/',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_audit_logs_as_admin(self):
        """Admin role can list audit logs successfully."""
        resp = self.client.get(
            '/api/audit/logs/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn('status', data)
        self.assertIn('data', data)
        self.assertIn('meta', data)
        self.assertEqual(data['status'], 'success')
        self.assertIsInstance(data['data'], list)
        self.assertGreaterEqual(len(data['data']), 3)

    # ------------------------------------------------------------------
    # Response envelope
    # ------------------------------------------------------------------

    def test_audit_log_response_envelope_shape(self):
        """Response follows standard envelope: status, data, meta."""
        resp = self.client.get(
            '/api/audit/logs/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        data = resp.json()
        self.assertIn('status', data)
        self.assertIn('data', data)
        self.assertIn('meta', data)
        self.assertEqual(data['status'], 'success')
        # meta should have page, total, per_page for paginated responses
        self.assertIn('page', data['meta'])
        self.assertIn('total', data['meta'])
        self.assertIn('per_page', data['meta'])

    def test_audit_log_response_includes_expected_fields(self):
        """Each audit log entry exposes all model fields via serializer."""
        resp = self.client.get(
            '/api/audit/logs/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        entry = resp.json()['data'][0]
        self.assertIn('id', entry)
        self.assertIn('event', entry)
        self.assertIn('entity_type', entry)
        self.assertIn('entity_id', entry)
        self.assertIn('user', entry)
        self.assertIn('ip_address', entry)
        self.assertIn('data_snapshot', entry)
        self.assertIn('timestamp', entry)

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def test_filter_by_event(self):
        """Filtering by ?event=... returns only matching entries."""
        resp = self.client.get(
            '/api/audit/logs/?event=USER_LOGIN',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()['data']
        self.assertGreater(len(data), 0)
        for entry in data:
            self.assertEqual(entry['event'], 'USER_LOGIN')

    def test_filter_by_event_no_matches(self):
        """Filtering by a valid event with no entries returns empty list."""
        # PO_CREATED is a valid AuditEvent choice but has no seeded entries
        resp = self.client.get(
            '/api/audit/logs/?event=PO_CREATED',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()['data']
        self.assertEqual(len(data), 0)

    def test_filter_by_entity_type(self):
        """Filtering by ?entity_type=... returns only matching entries."""
        resp = self.client.get(
            '/api/audit/logs/?entity_type=User',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()['data']
        self.assertGreater(len(data), 0)
        for entry in data:
            self.assertEqual(entry['entity_type'], 'User')

    def test_filter_by_user_id(self):
        """Filtering by ?user_id=... returns entries for that user."""
        resp = self.client.get(
            f'/api/audit/logs/?user_id={self.admin.id}',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()['data']
        self.assertGreater(len(data), 0)
        for entry in data:
            self.assertEqual(entry['user'], self.admin.id)

    def test_filter_by_user_id_no_matches(self):
        """Filtering by non-existent user_id returns empty result set."""
        resp = self.client.get(
            '/api/audit/logs/?user_id=99999',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()['data']
        self.assertEqual(len(data), 0)

    def test_filter_by_created_after(self):
        """Filtering by ?created_after=... narrows results."""
        resp = self.client.get(
            '/api/audit/logs/?created_after=2020-01-01T00:00:00Z',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # All seeded entries are after this date, so we should get everything
        data = resp.json()['data']
        self.assertGreaterEqual(len(data), 3)

    def test_filter_by_created_before(self):
        """Filtering by ?created_before=... narrows results."""
        resp = self.client.get(
            '/api/audit/logs/?created_before=2099-12-31T23:59:59Z',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()['data']
        self.assertGreaterEqual(len(data), 3)

    def test_filter_by_created_after_excludes_old_entries(self):
        """Filtering with a future created_after returns no results."""
        from datetime import datetime, timedelta, timezone
        from urllib.parse import quote

        future = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        resp = self.client.get(
            f'/api/audit/logs/?created_after={quote(future)}',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()['data']
        self.assertEqual(len(data), 0)

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    def test_audit_log_pagination_default(self):
        """List endpoint returns paginated results (default page_size=20)."""
        # Bulk-create 25 entries
        entries = [
            AuditLog(
                event='STOCK_ADJUSTED',
                user=self.admin,
                entity_type='StockLevel',
                entity_id=2000 + i,
                data_snapshot={'reason': f'Bulk {i}'},
            )
            for i in range(25)
        ]
        AuditLog.objects.bulk_create(entries)

        resp = self.client.get(
            '/api/audit/logs/',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data['data']), 20)
        self.assertIsNotNone(data['meta'].get('next'))

    def test_audit_log_pagination_custom_page_size(self):
        """Respecting ?page_size=... query parameter."""
        entries = [
            AuditLog(
                event='STOCK_ADJUSTED',
                user=self.admin,
                entity_type='StockLevel',
                entity_id=3000 + i,
                data_snapshot={'reason': f'Page {i}'},
            )
            for i in range(10)
        ]
        AuditLog.objects.bulk_create(entries)

        resp = self.client.get(
            '/api/audit/logs/?page_size=5',
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(len(data['data']), 5)
        # The response envelope renderer reports the default page_size in meta
        self.assertEqual(data['meta']['total'], len(data['data']) + 8)
        self.assertIsNotNone(data['meta'].get('next'))

    # ------------------------------------------------------------------
    # Signal-based audit logging
    # ------------------------------------------------------------------

    def test_signal_creates_audit_log_on_stock_adjustment(self):
        """Performing a stock adjustment triggers stock_adjusted
        signal, which creates an AuditLog entry via the receiver."""
        cat = Category.objects.create(name='Signal Test Cat')
        product = Product.objects.create(name='Signal Test Product', category=cat)
        sku = SKU.objects.create(product=product, code='SIGNAL-SADJ-001')
        StockLevel.objects.create(sku=sku, quantity_on_hand=100)

        before = AuditLog.objects.filter(event='STOCK_ADJUSTED').count()

        resp = self.client.patch(
            f'/api/inventory/stock/{product.id}/',
            {'quantity_delta': -10, 'reason': 'Signal audit verification'},
            format='json',
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        after = AuditLog.objects.filter(event='STOCK_ADJUSTED').count()
        self.assertEqual(after, before + 1)

        log = AuditLog.objects.filter(event='STOCK_ADJUSTED').latest('timestamp')
        self.assertEqual(log.data_snapshot.get('sku_code'), 'SIGNAL-SADJ-001')
        self.assertEqual(log.data_snapshot.get('delta'), -10)
        self.assertEqual(log.data_snapshot.get('new_quantity'), 90)
        self.assertEqual(log.data_snapshot.get('reason'), 'Signal audit verification')
        self.assertEqual(log.user, self.manager)

    def test_log_event_utility_creates_audit_entry(self):
        """The log_event utility function from signals.py
        directly creates an AuditLog entry."""
        from apps.audit.signals import log_event

        before = AuditLog.objects.filter(event='PRODUCT_CREATED').count()

        log_event(
            event='PRODUCT_CREATED',
            user=self.admin,
            entity_id=777,
            data_snapshot={'name': 'Utility Test Product'},
        )

        after = AuditLog.objects.filter(event='PRODUCT_CREATED').count()
        self.assertEqual(after, before + 1)

        log = AuditLog.objects.get(event='PRODUCT_CREATED', entity_id=777)
        self.assertEqual(log.data_snapshot.get('name'), 'Utility Test Product')
        self.assertEqual(log.user, self.admin)

    def test_log_ai_action_utility_creates_audit_entry(self):
        """The log_ai_action utility from utils.py
        creates an AuditLog entry with ip_address populated."""
        from apps.audit.utils import log_ai_action

        before = AuditLog.objects.filter(event='AI_NL_QUERY').count()

        log_ai_action(
            event='AI_NL_QUERY',
            user=self.admin,
            entity_type='NLQuery',
            entity_id=888,
            data={'query': 'Show low stock items', 'result_count': 5},
            ip='192.168.1.100',
        )

        after = AuditLog.objects.filter(event='AI_NL_QUERY').count()
        self.assertEqual(after, before + 1)

        log = AuditLog.objects.get(event='AI_NL_QUERY', entity_id=888)
        self.assertEqual(log.entity_type, 'NLQuery')
        self.assertEqual(log.ip_address, '192.168.1.100')
        self.assertEqual(log.data_snapshot.get('query'), 'Show low stock items')
        self.assertEqual(log.user, self.admin)

    # ------------------------------------------------------------------
    # Audit middleware (USER_LOGIN on successful login)
    # ------------------------------------------------------------------

    def test_audit_middleware_logs_successful_login(self):
        """AuditMiddleware creates a USER_LOGIN entry when a user
        successfully authenticates via POST /api/auth/login/."""
        before = AuditLog.objects.filter(event='USER_LOGIN').count()

        resp = self.client.post(
            '/api/auth/login/',
            {'email': 'admin@test.com', 'password': 'testpass123'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        after = AuditLog.objects.filter(event='USER_LOGIN').count()
        self.assertEqual(after, before + 1)

        log = AuditLog.objects.filter(event='USER_LOGIN').latest('timestamp')
        self.assertEqual(log.entity_type, 'User')
        self.assertEqual(log.entity_id, self.admin.id)
        self.assertEqual(log.data_snapshot.get('path'), '/api/auth/login/')
        self.assertEqual(log.data_snapshot.get('method'), 'POST')
        self.assertIsNotNone(log.ip_address)

    def test_audit_middleware_does_not_log_failed_login(self):
        """AuditMiddleware does not create a USER_LOGIN entry for
        failed authentication attempts (non-200 response)."""
        before = AuditLog.objects.filter(event='USER_LOGIN').count()

        resp = self.client.post(
            '/api/auth/login/',
            {'email': 'admin@test.com', 'password': 'wrongpassword'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        after = AuditLog.objects.filter(event='USER_LOGIN').count()
        self.assertEqual(after, before)
