from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.audit.signals import (
    log_event,
    log_po_approval,
    log_po_confirmed,
    log_po_rejection,
    log_po_sent,
    log_stock_adjustment,
)

User = get_user_model()


class LogEventTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='pass1234'
        )

    @patch('apps.audit.signals.AuditLog')
    def test_log_event_creates_entry(self, mock_audit):
        log_event('TEST_EVENT', self.user, entity_id=1, data_snapshot={'key': 'value'})
        mock_audit.objects.create.assert_called_once_with(
            event='TEST_EVENT',
            user=self.user,
            entity_type='',
            entity_id=1,
            data_snapshot={'key': 'value'},
        )

    @patch('apps.audit.signals.AuditLog')
    def test_log_event_default_empty_snapshot(self, mock_audit):
        log_event('TEST_EVENT', self.user)
        mock_audit.objects.create.assert_called_once_with(
            event='TEST_EVENT',
            user=self.user,
            entity_type='',
            entity_id=None,
            data_snapshot={},
        )

    @patch('apps.audit.signals.AuditLog.objects.create', side_effect=Exception('DB error'))
    def test_log_event_exception_handled(self, mock_create):
        log_event('FAIL_EVENT', self.user)


class LogPoApprovalTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser2', email='test2@example.com', password='pass1234'
        )

    @patch('apps.audit.signals.AuditLog')
    def test_log_po_approval(self, mock_audit):
        po = MagicMock()
        po.id = 42
        po.supplier.name = 'Acme'
        po.total_cost = '500.00'
        log_po_approval(sender=None, po=po, user=self.user)
        mock_audit.objects.create.assert_called_once()
        call_kwargs = mock_audit.objects.create.call_args[1]
        self.assertEqual(call_kwargs['event'], 'PO_APPROVED')
        self.assertEqual(call_kwargs['entity_id'], 42)

    def test_log_po_approval_non_custom_user_skips(self):
        po = MagicMock()
        log_po_approval(sender=None, po=po, user='not_a_user')


class LogPoRejectionTest(TestCase):
    @patch('apps.audit.signals.AuditLog')
    def test_log_po_rejection(self, mock_audit):
        po = MagicMock()
        po.id = 10
        po.supplier.name = 'WidgetCorp'
        po.total_cost = '200.00'
        user = MagicMock()
        log_po_rejection(sender=None, po=po, user=user)
        mock_audit.objects.create.assert_called_once()
        call_kwargs = mock_audit.objects.create.call_args[1]
        self.assertEqual(call_kwargs['event'], 'PO_REJECTED')


class LogPoSentTest(TestCase):
    @patch('apps.audit.signals.AuditLog')
    def test_log_po_sent(self, mock_audit):
        po = MagicMock()
        po.id = 20
        po.supplier.name = 'PartsInc'
        po.sku.code = 'SKU-001'
        po.total_cost = '300.00'
        log_po_sent(sender=None, po=po)
        mock_audit.objects.create.assert_called_once()
        call_kwargs = mock_audit.objects.create.call_args[1]
        self.assertEqual(call_kwargs['event'], 'PO_SENT')


class LogPoConfirmedTest(TestCase):
    @patch('apps.audit.signals.AuditLog')
    def test_log_po_confirmed(self, mock_audit):
        po = MagicMock()
        po.id = 30
        po.supplier.name = 'SupplyCo'
        po.sku.code = 'SKU-002'
        po.total_cost = '150.00'
        log_po_confirmed(sender=None, po=po)
        mock_audit.objects.create.assert_called_once()
        call_kwargs = mock_audit.objects.create.call_args[1]
        self.assertEqual(call_kwargs['event'], 'INVOICE_CONFIRMED')


class LogStockAdjustmentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser3', email='test3@example.com', password='pass1234'
        )

    @patch('apps.audit.signals.AuditLog')
    def test_log_stock_adjustment(self, mock_audit):
        stock_level = MagicMock()
        stock_level.id = 55
        stock_level.sku.code = 'SKU-100'
        stock_level.quantity_on_hand = 42
        log_stock_adjustment(
            sender=None,
            stock_level=stock_level,
            delta=-5,
            user=self.user,
            reason='Damaged',
        )
        mock_audit.objects.create.assert_called_once()
        call_kwargs = mock_audit.objects.create.call_args[1]
        self.assertEqual(call_kwargs['event'], 'STOCK_ADJUSTED')

    def test_log_stock_adjustment_non_custom_user_skips(self):
        stock_level = MagicMock()
        log_stock_adjustment(
            sender=None,
            stock_level=stock_level,
            delta=1,
            user='not_a_user',
            reason='test',
        )
