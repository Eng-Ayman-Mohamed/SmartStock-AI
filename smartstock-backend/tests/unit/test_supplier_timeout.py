import uuid
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.purchasing.models import PurchaseOrder
from apps.purchasing.timeout_tasks import (
    SUPPLIER_TIMEOUT_HOURS,
    check_supplier_timeouts,
)


def _make_supplier():
    from apps.inventory.models import Supplier

    return Supplier.objects.create(name='Acme', contact_email='acme@test.com')


def _make_po(status, sent_at=None, supplier=None):
    """Helper: create a minimal PurchaseOrder with related objects."""
    from apps.inventory.models import SKU, Product

    if supplier is None:
        supplier = _make_supplier()
    product = Product.objects.create(name='Widget', unit_price=10.0)
    sku = SKU.objects.create(product=product, code=f'SKU-{uuid.uuid4().hex[:8]}')
    return PurchaseOrder.objects.create(
        sku=sku,
        supplier=supplier,
        quantity=10,
        total_cost=100.00,
        status=status,
        sent_at=sent_at,
    )


@override_settings(ESCALATION_RECIPIENT_EMAILS=['manager@test.com'])
class SupplierTimeoutTaskTest(TestCase):
    """Tests for check_supplier_timeouts periodic task."""

    @patch('apps.purchasing.timeout_tasks._trigger_escalation')
    @patch('apps.purchasing.timeout_tasks._create_audit_log')
    def test_47h_no_timeout(self, mock_audit, mock_escal):
        """PO sent 47h ago should NOT time out (threshold is 48h)."""
        sent_at = timezone.now() - timedelta(hours=47)
        po = _make_po(status='email_sent', sent_at=sent_at)

        result = check_supplier_timeouts()

        self.assertEqual(result['timed_out_count'], 0)
        po.refresh_from_db()
        self.assertEqual(po.status, 'email_sent')
        mock_audit.assert_not_called()
        mock_escal.assert_not_called()

    @patch('apps.purchasing.timeout_tasks._trigger_escalation')
    @patch('apps.purchasing.timeout_tasks._create_audit_log')
    def test_exactly_48h_timeout(self, mock_audit, mock_escal):
        """PO sent exactly 48h ago should time out."""
        sent_at = timezone.now() - timedelta(hours=SUPPLIER_TIMEOUT_HOURS)
        po = _make_po(status='email_sent', sent_at=sent_at)

        result = check_supplier_timeouts()

        self.assertEqual(result['timed_out_count'], 1)
        self.assertIn(po.id, result['timed_out_ids'])
        po.refresh_from_db()
        self.assertEqual(po.status, 'timeout')
        mock_audit.assert_called_once_with(po)
        mock_escal.assert_called_once_with(po)

    @patch('apps.purchasing.timeout_tasks._trigger_escalation')
    @patch('apps.purchasing.timeout_tasks._create_audit_log')
    def test_greater_than_48h_timeout(self, mock_audit, mock_escal):
        """PO sent 72h ago should time out."""
        sent_at = timezone.now() - timedelta(hours=72)
        po = _make_po(status='waiting_confirmation', sent_at=sent_at)

        result = check_supplier_timeouts()

        self.assertEqual(result['timed_out_count'], 1)
        po.refresh_from_db()
        self.assertEqual(po.status, 'timeout')
        self.assertIn('Timed out', po.notes)

    @patch('apps.purchasing.timeout_tasks._trigger_escalation')
    @patch('apps.purchasing.timeout_tasks._create_audit_log')
    def test_already_confirmed_ignored(self, mock_audit, mock_escal):
        """Confirmed POs should not be timed out."""
        sent_at = timezone.now() - timedelta(hours=100)
        po = _make_po(status='confirmed', sent_at=sent_at)

        result = check_supplier_timeouts()

        self.assertEqual(result['timed_out_count'], 0)
        po.refresh_from_db()
        self.assertEqual(po.status, 'confirmed')
        mock_audit.assert_not_called()

    @patch('apps.purchasing.timeout_tasks._trigger_escalation')
    @patch('apps.purchasing.timeout_tasks._create_audit_log')
    def test_cancelled_ignored(self, mock_audit, mock_escal):
        """Cancelled POs should not be timed out."""
        sent_at = timezone.now() - timedelta(hours=100)
        po = _make_po(status='cancelled', sent_at=sent_at)

        result = check_supplier_timeouts()

        self.assertEqual(result['timed_out_count'], 0)
        po.refresh_from_db()
        self.assertEqual(po.status, 'cancelled')
        mock_audit.assert_not_called()

    @patch('apps.purchasing.timeout_tasks._trigger_escalation')
    @patch('apps.purchasing.timeout_tasks._create_audit_log')
    def test_draft_ignored(self, mock_audit, mock_escal):
        """Draft POs (no sent_at) should not be timed out."""
        po = _make_po(status='draft', sent_at=None)

        result = check_supplier_timeouts()

        self.assertEqual(result['timed_out_count'], 0)
        po.refresh_from_db()
        self.assertEqual(po.status, 'draft')

    @patch('apps.purchasing.timeout_tasks._trigger_escalation')
    @patch('apps.purchasing.timeout_tasks._create_audit_log')
    def test_already_timed_out_not_reprocessed(self, mock_audit, mock_escal):
        """Already timed-out POs should not be processed again."""
        sent_at = timezone.now() - timedelta(hours=100)
        _make_po(status='timeout', sent_at=sent_at)

        result = check_supplier_timeouts()

        self.assertEqual(result['timed_out_count'], 0)

    @patch('apps.purchasing.timeout_tasks._trigger_escalation')
    @patch('apps.purchasing.timeout_tasks._create_audit_log')
    def test_audit_log_recorded(self, mock_audit, mock_escal):
        """Timeout should create an audit log entry."""
        sent_at = timezone.now() - timedelta(hours=48)
        po = _make_po(status='email_sent', sent_at=sent_at)

        check_supplier_timeouts()

        mock_audit.assert_called_once()
        call_args = mock_audit.call_args
        self.assertEqual(call_args[0][0].id, po.id)

    @patch('apps.purchasing.timeout_tasks._trigger_escalation')
    @patch('apps.purchasing.timeout_tasks._create_audit_log')
    def test_multiple_pos_timeout(self, mock_audit, mock_escal):
        """Multiple stale POs should all be timed out."""
        sent_at = timezone.now() - timedelta(hours=50)
        supplier = _make_supplier()
        po1 = _make_po(status='email_sent', sent_at=sent_at, supplier=supplier)
        po2 = _make_po(status='waiting_confirmation', sent_at=sent_at, supplier=supplier)

        result = check_supplier_timeouts()

        self.assertEqual(result['timed_out_count'], 2)
        self.assertIn(po1.id, result['timed_out_ids'])
        self.assertIn(po2.id, result['timed_out_ids'])

    @patch('apps.purchasing.timeout_tasks._trigger_escalation')
    @patch('apps.purchasing.timeout_tasks._create_audit_log')
    def test_result_contains_checked_at(self, mock_audit, mock_escal):
        """Result should contain checked_at timestamp."""
        result = check_supplier_timeouts()
        self.assertIn('checked_at', result)
        self.assertIsInstance(result['checked_at'], str)

    @patch('apps.purchasing.timeout_tasks._trigger_escalation')
    @patch('apps.purchasing.timeout_tasks._create_audit_log')
    def test_notes_append_to_existing(self, mock_audit, mock_escal):
        """Timeout message should append to existing notes, not replace."""
        sent_at = timezone.now() - timedelta(hours=48)
        po = _make_po(status='email_sent', sent_at=sent_at)
        po.notes = 'Original note'
        po.save(update_fields=['notes'])

        check_supplier_timeouts()

        po.refresh_from_db()
        self.assertIn('Original note', po.notes)
        self.assertIn('Timed out', po.notes)


class TimeoutErrorHandlingTest(TestCase):
    """Test error handling in timeout tasks."""

    @patch('apps.purchasing.timeout_tasks._trigger_escalation')
    @patch('apps.purchasing.timeout_tasks._create_audit_log')
    def test_po_save_failure_continues(self, mock_audit, mock_escal):
        """If saving one PO fails, the task continues with others."""
        sent_at = timezone.now() - timedelta(hours=50)
        supplier = _make_supplier()
        po1 = _make_po(status='email_sent', sent_at=sent_at, supplier=supplier)
        po2 = _make_po(status='email_sent', sent_at=sent_at, supplier=supplier)

        original_save = PurchaseOrder.save

        def fail_first_save(self_obj, *args, **kwargs):
            if self_obj.id == po1.id:
                raise Exception('DB error')
            return original_save(self_obj, *args, **kwargs)

        with patch.object(PurchaseOrder, 'save', fail_first_save):
            result = check_supplier_timeouts()

        # po2 should have timed out (po1 failed)
        self.assertIn(po2.id, result['timed_out_ids'])

    @patch('apps.purchasing.timeout_tasks._trigger_escalation')
    @patch('apps.purchasing.timeout_tasks._create_audit_log')
    def test_create_audit_log_calls_function(self, mock_audit, mock_escal):
        """_create_audit_log is called during timeout."""
        sent_at = timezone.now() - timedelta(hours=48)
        po = _make_po(status='email_sent', sent_at=sent_at)

        check_supplier_timeouts()

        mock_audit.assert_called_once()
        self.assertEqual(mock_audit.call_args[0][0].id, po.id)

    @patch('apps.purchasing.timeout_tasks._create_audit_log')
    def test_trigger_escalation_handles_error(self, mock_audit):
        """_trigger_escalation should not raise when escalation creation fails."""
        from apps.purchasing.timeout_tasks import _trigger_escalation

        po = _make_po(status='timeout', sent_at=timezone.now())

        with patch(
            'apps.notifications.service.create_escalation_notification',
            side_effect=Exception('db error'),
        ):
            # Should not raise
            _trigger_escalation(po)

    def test_create_audit_log_error_handled(self):
        """_create_audit_log should not raise on error."""
        from apps.purchasing.timeout_tasks import _create_audit_log

        po = _make_po(status='timeout', sent_at=timezone.now())

        with patch('apps.audit.models.AuditLog.objects.create', side_effect=Exception('db error')):
            # Should not raise
            _create_audit_log(po)


class TimeoutConstantsTest(TestCase):
    """Test timeout constants match requirements."""

    def test_timeout_hours_is_48(self):
        self.assertEqual(SUPPLIER_TIMEOUT_HOURS, 48)
