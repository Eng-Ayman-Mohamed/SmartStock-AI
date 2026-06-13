import types
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.purchasing.services import PurchasingService


class PurchasingServiceDraftPoTest(TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = PurchasingService(repo=self.repo)
        self.user = MagicMock(id=1)

    def test_draft_po_creates_with_draft_status(self):
        self.repo.create.return_value = MagicMock(id=10, status='draft')
        result = self.service.draft_po(sku_id=5, quantity=100, supplier_id=3, user=self.user)
        self.repo.create.assert_called_once_with(
            {
                'sku_id': 5,
                'quantity': 100,
                'supplier_id': 3,
                'requested_by': self.user,
                'status': 'draft',
            }
        )
        self.assertEqual(result.status, 'draft')

    def test_draft_po_passes_correct_args(self):
        self.repo.create.return_value = MagicMock()
        user = MagicMock(id=42)
        self.service.draft_po(sku_id=1, quantity=10, supplier_id=2, user=user)
        call_args = self.repo.create.call_args[0][0]
        self.assertEqual(call_args['sku_id'], 1)
        self.assertEqual(call_args['quantity'], 10)
        self.assertEqual(call_args['supplier_id'], 2)
        self.assertIs(call_args['requested_by'], user)
        self.assertEqual(call_args['status'], 'draft')

    def test_draft_po_returns_repo_result(self):
        mock_po = MagicMock(id=99)
        self.repo.create.return_value = mock_po
        result = self.service.draft_po(sku_id=1, quantity=1, supplier_id=1, user=self.user)
        self.assertIs(result, mock_po)


class PurchasingServiceApprovePoTest(TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = PurchasingService(repo=self.repo)
        self.user = MagicMock(id=10)

    def test_approve_draft_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='draft')
        updated = MagicMock(id=1, status='approved')
        self.repo.update.return_value = updated

        result = self.service.approve_po(po_id=1, user=self.user)

        self.repo.get_by_id.assert_called_once_with(1)
        self.repo.update.assert_called_once_with(1, {'status': 'approved', 'approved_by_id': 10})
        self.assertEqual(result.status, 'approved')

    def test_approve_pending_approval_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='pending_approval')
        updated = MagicMock(status='approved')
        self.repo.update.return_value = updated

        result = self.service.approve_po(po_id=5, user=self.user)
        self.assertEqual(result.status, 'approved')

    def test_approve_rejects_sent_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='sent')
        with self.assertRaises(ValidationError) as ctx:
            self.service.approve_po(po_id=1, user=self.user)
        self.assertIn('draft or pending approval', str(ctx.exception))

    def test_approve_rejects_approved_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='approved')
        with self.assertRaises(ValidationError):
            self.service.approve_po(po_id=1, user=self.user)

    def test_approve_rejects_rejected_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='rejected')
        with self.assertRaises(ValidationError):
            self.service.approve_po(po_id=1, user=self.user)

    def test_approve_rejects_cancelled_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='cancelled')
        with self.assertRaises(ValidationError):
            self.service.approve_po(po_id=1, user=self.user)

    def test_approve_rejects_confirmed_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='confirmed')
        with self.assertRaises(ValidationError):
            self.service.approve_po(po_id=1, user=self.user)


class PurchasingServiceRejectPoTest(TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = PurchasingService(repo=self.repo)
        self.user = MagicMock(id=10)

    def test_reject_draft_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='draft')
        updated = MagicMock(id=1, status='rejected')
        self.repo.update.return_value = updated

        result = self.service.reject_po(po_id=1, user=self.user)

        self.repo.update.assert_called_once_with(1, {'status': 'rejected'})
        self.assertEqual(result.status, 'rejected')

    def test_reject_pending_approval_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='pending_approval')
        updated = MagicMock(status='rejected')
        self.repo.update.return_value = updated

        result = self.service.reject_po(po_id=5, user=self.user)
        self.assertEqual(result.status, 'rejected')

    def test_reject_rejects_sent_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='sent')
        with self.assertRaises(ValidationError) as ctx:
            self.service.reject_po(po_id=1, user=self.user)
        self.assertIn('draft or pending approval', str(ctx.exception))

    def test_reject_rejects_approved_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='approved')
        with self.assertRaises(ValidationError):
            self.service.reject_po(po_id=1, user=self.user)

    def test_reject_rejects_cancelled_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='cancelled')
        with self.assertRaises(ValidationError):
            self.service.reject_po(po_id=1, user=self.user)


class PurchasingServiceSendPoTest(TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = PurchasingService(repo=self.repo)

    @patch('apps.purchasing.services.timezone')
    def test_send_approved_po(self, mock_tz):
        mock_tz.now.return_value = timezone.now()
        self.repo.get_by_id.return_value = MagicMock(status='approved')
        updated = MagicMock(id=1, status='sent', sent_at=mock_tz.now.return_value)
        self.repo.update.return_value = updated

        result = self.service.send_po(po_id=1)

        self.repo.update.assert_called_once()
        update_call = self.repo.update.call_args
        self.assertEqual(update_call[0][0], 1)
        self.assertEqual(update_call[0][1]['status'], 'sent')
        self.assertIn('sent_at', update_call[0][1])
        self.assertEqual(result.status, 'sent')

    def test_send_rejects_draft_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='draft')
        with self.assertRaises(ValidationError) as ctx:
            self.service.send_po(po_id=1)
        self.assertIn('Only approved orders can be sent', str(ctx.exception))

    def test_send_rejects_sent_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='sent')
        with self.assertRaises(ValidationError):
            self.service.send_po(po_id=1)

    def test_send_rejects_rejected_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='rejected')
        with self.assertRaises(ValidationError):
            self.service.send_po(po_id=1)

    def test_send_rejects_cancelled_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='cancelled')
        with self.assertRaises(ValidationError):
            self.service.send_po(po_id=1)

    def test_send_rejects_pending_approval_po(self):
        self.repo.get_by_id.return_value = MagicMock(status='pending_approval')
        with self.assertRaises(ValidationError):
            self.service.send_po(po_id=1)


class PurchasingServiceGetOpenPoStatusTest(TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = PurchasingService(repo=self.repo)

    def test_has_open_po_returns_true(self):
        self.repo.get_open_for_product.return_value = MagicMock(id=42)
        result = self.service.get_open_po_status(product_id=7)
        self.repo.get_open_for_product.assert_called_once_with(7)
        self.assertTrue(result['has_open_po'])
        self.assertEqual(result['open_po_id'], 42)

    def test_no_open_po_returns_false(self):
        self.repo.get_open_for_product.return_value = None
        result = self.service.get_open_po_status(product_id=7)
        self.assertFalse(result['has_open_po'])
        self.assertIsNone(result['open_po_id'])

    def test_returns_dict_with_both_keys(self):
        self.repo.get_open_for_product.return_value = MagicMock(id=1)
        result = self.service.get_open_po_status(product_id=1)
        self.assertIn('has_open_po', result)
        self.assertIn('open_po_id', result)


class PurchasingServiceGetOverdueSuppliersTest(TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = PurchasingService(repo=self.repo)

    @patch('apps.purchasing.services.timezone')
    def test_no_overdue_pos(self, mock_tz):
        mock_tz.now.return_value = timezone.now()
        mock_qs = MagicMock()
        mock_qs.filter.return_value.select_related.return_value = []
        self.repo.get_all.return_value = mock_qs

        result = self.service.get_overdue_suppliers()
        self.assertEqual(result, [])

    @patch('apps.purchasing.services.timezone')
    def test_overdue_supplier_detected(self, mock_tz):
        now = timezone.now()
        mock_tz.now.return_value = now
        mock_tz.timedelta = timezone.timedelta

        sent_at = now - timezone.timedelta(days=20)
        supplier = types.SimpleNamespace(id=1, name='Acme Corp', default_lead_time_days=7)
        po = MagicMock(id=10, sent_at=sent_at, supplier=supplier)

        mock_qs = MagicMock()
        mock_qs.filter.return_value.select_related.return_value = [po]
        self.repo.get_all.return_value = mock_qs

        result = self.service.get_overdue_suppliers()

        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry['supplier_id'], 1)
        self.assertEqual(entry['supplier_name'], 'Acme Corp')
        self.assertEqual(len(entry['overdue_pos']), 1)
        self.assertEqual(entry['overdue_pos'][0]['po_id'], 10)
        self.assertEqual(entry['overdue_pos'][0]['po_number'], 'PO-10')
        self.assertGreater(entry['days_overdue'], 0)

    @patch('apps.purchasing.services.timezone')
    def test_not_overdue_if_within_lead_time(self, mock_tz):
        now = timezone.now()
        mock_tz.now.return_value = now
        mock_tz.timedelta = timezone.timedelta

        sent_at = now - timezone.timedelta(days=3)
        supplier = types.SimpleNamespace(id=1, name='Quick Supplier', default_lead_time_days=7)
        po = MagicMock(id=20, sent_at=sent_at, supplier=supplier)

        mock_qs = MagicMock()
        mock_qs.filter.return_value.select_related.return_value = [po]
        self.repo.get_all.return_value = mock_qs

        result = self.service.get_overdue_suppliers()
        self.assertEqual(result, [])

    @patch('apps.purchasing.services.timezone')
    def test_multiple_pos_same_supplier_aggregated(self, mock_tz):
        now = timezone.now()
        mock_tz.now.return_value = now
        mock_tz.timedelta = timezone.timedelta

        sent_at = now - timezone.timedelta(days=30)
        supplier = types.SimpleNamespace(id=5, name='Slow Supplier', default_lead_time_days=5)
        po1 = MagicMock(id=100, sent_at=sent_at, supplier=supplier)
        po2 = MagicMock(id=101, sent_at=sent_at, supplier=supplier)

        mock_qs = MagicMock()
        mock_qs.filter.return_value.select_related.return_value = [po1, po2]
        self.repo.get_all.return_value = mock_qs

        result = self.service.get_overdue_suppliers()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['supplier_id'], 5)
        self.assertEqual(len(result[0]['overdue_pos']), 2)

    @patch('apps.purchasing.services.timezone')
    def test_different_suppliers_returned_separately(self, mock_tz):
        now = timezone.now()
        mock_tz.now.return_value = now
        mock_tz.timedelta = timezone.timedelta

        sent_at = now - timezone.timedelta(days=15)
        supplier1 = types.SimpleNamespace(id=1, name='Supplier A', default_lead_time_days=5)
        supplier2 = types.SimpleNamespace(id=2, name='Supplier B', default_lead_time_days=5)
        po1 = MagicMock(id=30, sent_at=sent_at, supplier=supplier1)
        po2 = MagicMock(id=31, sent_at=sent_at, supplier=supplier2)

        mock_qs = MagicMock()
        mock_qs.filter.return_value.select_related.return_value = [po1, po2]
        self.repo.get_all.return_value = mock_qs

        result = self.service.get_overdue_suppliers()
        self.assertEqual(len(result), 2)
        supplier_ids = {r['supplier_id'] for r in result}
        self.assertEqual(supplier_ids, {1, 2})


class PurchasingServiceSignalsTest(TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = PurchasingService(repo=self.repo)
        self.user = MagicMock(id=10)

    @patch('apps.purchasing.services.po_approved')
    def test_approve_po_sends_signal(self, mock_signal):
        self.repo.get_by_id.return_value = MagicMock(status='draft')
        self.repo.update.return_value = MagicMock(status='approved')
        self.service.approve_po(po_id=1, user=self.user)
        mock_signal.send.assert_called_once()

    @patch('apps.purchasing.services.po_rejected')
    def test_reject_po_sends_signal(self, mock_signal):
        self.repo.get_by_id.return_value = MagicMock(status='draft')
        self.repo.update.return_value = MagicMock(status='rejected')
        self.service.reject_po(po_id=1, user=self.user)
        mock_signal.send.assert_called_once()

    @patch('apps.purchasing.services.po_sent')
    def test_send_po_sends_signal(self, mock_signal):
        self.repo.get_by_id.return_value = MagicMock(status='approved')
        self.repo.update.return_value = MagicMock(status='sent')
        self.service.send_po(po_id=1)
        mock_signal.send.assert_called_once()


class PurchasingServiceGetPoWithSupplierTest(TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = PurchasingService(repo=self.repo)

    def test_get_po_with_supplier_returns_dict(self):
        mock_po = MagicMock()
        mock_po.id = 5
        mock_po.po_number = 'PO-2026-001'
        mock_po.sku.code = 'SKU-001'
        mock_po.sku.product.name = 'Test Product'
        mock_po.sku.product.unit_price = 10.00
        mock_po.total_cost = 500.00
        mock_po.supplier.contact_email = 'supplier@test.com'
        mock_po.supplier.name = 'Test Supplier'
        self.repo.get_by_id.return_value = mock_po

        result = self.service.get_po_with_supplier(po_id=5)

        self.assertEqual(result['po_id'], 5)
        self.assertEqual(result['po_number'], 'PO-2026-001')
        self.assertEqual(result['sku_code'], 'SKU-001')
        self.assertEqual(result['product_name'], 'Test Product')
        self.assertEqual(result['supplier_email'], 'supplier@test.com')
        self.repo.get_by_id.assert_called_once_with(5)

    def test_get_po_with_supplier_works_without_po_number(self):
        mock_po = MagicMock()
        mock_po.id = 10
        mock_po.po_number = None
        mock_po.sku.code = 'SKU-002'
        mock_po.sku.product.name = 'Another Product'
        mock_po.sku.product.unit_price = 5.00
        mock_po.total_cost = 250.00
        mock_po.supplier.contact_email = 'sup2@test.com'
        mock_po.supplier.name = 'Supplier 2'
        self.repo.get_by_id.return_value = mock_po

        result = self.service.get_po_with_supplier(po_id=10)

        self.assertEqual(result['po_id'], 10)
        self.assertIsNone(result['po_number'])


class PurchasingServiceSendPoEmailTest(TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = PurchasingService(repo=self.repo)

    @patch('django.template.loader.render_to_string')
    @patch('apps.purchasing.services.EmailService')
    def test_send_po_email_calls_email_service(self, mock_email_cls, mock_render):
        mock_po = MagicMock()
        mock_po.id = 7
        mock_po.po_number = 'PO-2026-050'
        mock_po.sku.code = 'SKU-100'
        mock_po.sku.product.name = 'Email Test Product'
        mock_po.sku.product.unit_price = 3.00
        mock_po.total_cost = 150.00
        mock_po.supplier.contact_email = 'send@test.com'
        mock_po.supplier.name = 'Email Supplier'
        self.repo.get_by_id.return_value = mock_po

        mock_render.return_value = 'Please find below PO details.'
        mock_email_instance = MagicMock()
        mock_email_cls.return_value = mock_email_instance

        result = self.service.send_po_email(po_id=7)

        self.assertTrue(result['sent'])
        self.assertEqual(result['recipient'], 'send@test.com')
        mock_render.assert_called_once()
        mock_email_instance.send.assert_called_once()
        send_call = mock_email_instance.send.call_args
        self.assertIn('Confirmation Required', send_call[1]['subject'])


class PurchasingServiceDraftPoOptionalParamsTest(TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.service = PurchasingService(repo=self.repo)
        self.user = MagicMock(id=1)

    def test_draft_po_with_po_number(self):
        self.repo.create.return_value = MagicMock(id=20)
        self.service.draft_po(
            sku_id=3,
            quantity=50,
            supplier_id=7,
            user=self.user,
            po_number='PO-CUSTOM-001',
        )
        call_data = self.repo.create.call_args[0][0]
        self.assertEqual(call_data['po_number'], 'PO-CUSTOM-001')

    def test_draft_po_with_total_cost(self):
        self.repo.create.return_value = MagicMock(id=21)
        self.service.draft_po(
            sku_id=4,
            quantity=10,
            supplier_id=8,
            user=self.user,
            total_cost=999.99,
        )
        call_data = self.repo.create.call_args[0][0]
        self.assertEqual(call_data['total_cost'], 999.99)

    def test_draft_po_with_both_optional_params(self):
        self.repo.create.return_value = MagicMock(id=22)
        self.service.draft_po(
            sku_id=5,
            quantity=15,
            supplier_id=9,
            user=self.user,
            po_number='PO-BOTH-001',
            total_cost=1500.00,
        )
        call_data = self.repo.create.call_args[0][0]
        self.assertEqual(call_data['po_number'], 'PO-BOTH-001')
        self.assertEqual(call_data['total_cost'], 1500.00)
