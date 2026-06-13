from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.notifications.models import EscalationNotification
from apps.notifications.service import (
    create_escalation_notification,
    get_escalation_recipients,
)


def _make_po():
    """Create a minimal PurchaseOrder with related objects."""
    from apps.authentication.models import CustomUser
    from apps.inventory.models import SKU, Product, Supplier
    from apps.purchasing.models import PurchaseOrder

    user = CustomUser.objects.create_user(username='requester', password='test', role='viewer')
    supplier = Supplier.objects.create(name='Acme', contact_email='acme@test.com')
    product = Product.objects.create(name='Widget', unit_price=10.0)
    sku = SKU.objects.create(product=product, code='SKU-TEST')
    return PurchaseOrder.objects.create(
        sku=sku,
        supplier=supplier,
        quantity=10,
        total_cost=100.00,
        status='email_sent',
        sent_at=timezone.now(),
        requested_by=user,
    )


class EscalationNotificationModelTest(TestCase):
    """Test the EscalationNotification model."""

    def test_str_representation(self):
        po = _make_po()
        notif = EscalationNotification.objects.create(
            po=po,
            reason='email_delivery_failed',
        )
        self.assertIn('PO-', str(notif))
        self.assertIn('email_delivery_failed', str(notif))

    def test_default_status_is_pending(self):
        po = _make_po()
        notif = EscalationNotification.objects.create(
            po=po,
            reason='supplier_timeout',
        )
        self.assertEqual(notif.status, 'pending')

    def test_default_channel_is_email(self):
        po = _make_po()
        notif = EscalationNotification.objects.create(
            po=po,
            reason='email_delivery_failed',
        )
        self.assertEqual(notif.channel, 'email')


class CreateEscalationNotificationTest(TestCase):
    """Test create_escalation_notification service function."""

    @override_settings(ESCALATION_RECIPIENT_EMAILS=['mgr@test.com'])
    @patch('apps.notifications.service._send_escalation_email')
    def test_creates_notification(self, mock_send):
        po = _make_po()
        notif = create_escalation_notification(
            po=po,
            reason='email_delivery_failed',
            message='Test message',
        )
        self.assertIsNotNone(notif.id)
        self.assertEqual(notif.reason, 'email_delivery_failed')
        self.assertEqual(notif.message, 'Test message')
        mock_send.assert_called_once_with(notif)

    @override_settings(ESCALATION_RECIPIENT_EMAILS=['mgr@test.com'])
    @patch('apps.notifications.service._send_escalation_email')
    def test_prevents_duplicate_within_24h(self, mock_send):
        po = _make_po()
        notif1 = create_escalation_notification(po=po, reason='email_delivery_failed')
        notif2 = create_escalation_notification(po=po, reason='email_delivery_failed')
        self.assertEqual(notif1.id, notif2.id)
        mock_send.assert_called_once()

    @override_settings(ESCALATION_RECIPIENT_EMAILS=['mgr@test.com'])
    @patch('apps.notifications.service._send_escalation_email')
    def test_different_reasons_not_deduplicated(self, mock_send):
        po = _make_po()
        notif1 = create_escalation_notification(po=po, reason='email_delivery_failed')
        notif2 = create_escalation_notification(po=po, reason='supplier_timeout')
        self.assertNotEqual(notif1.id, notif2.id)
        self.assertEqual(mock_send.call_count, 2)

    @override_settings(ESCALATION_RECIPIENT_EMAILS=[])
    @patch('apps.notifications.service._send_escalation_email')
    def test_uses_supplier_email_when_no_recipients_configured(self, mock_send):
        po = _make_po()
        notif = create_escalation_notification(po=po, reason='email_delivery_failed')
        self.assertEqual(notif.recipient_email, 'acme@test.com')

    @override_settings(ESCALATION_RECIPIENT_EMAILS=['mgr@test.com'])
    @patch('apps.notifications.service._send_escalation_email')
    def test_uses_first_configured_recipient(self, mock_send):
        po = _make_po()
        notif = create_escalation_notification(po=po, reason='supplier_timeout')
        self.assertEqual(notif.recipient_email, 'mgr@test.com')

    @override_settings(ESCALATION_RECIPIENT_EMAILS=['mgr@test.com'])
    @patch('apps.notifications.service._send_escalation_email')
    def test_supplier_timeout_message_content(self, mock_send):
        po = _make_po()
        notif = create_escalation_notification(po=po, reason='supplier_timeout')
        self.assertIn('48 hours', notif.message)
        self.assertIn('Acme', notif.message)
        self.assertIn('follow up', notif.message)

    @override_settings(ESCALATION_RECIPIENT_EMAILS=['mgr@test.com'])
    @patch('apps.notifications.service._send_escalation_email')
    def test_email_failed_message_content(self, mock_send):
        po = _make_po()
        notif = create_escalation_notification(po=po, reason='email_delivery_failed')
        self.assertIn('permanently failed', notif.message)
        self.assertIn('Acme', notif.message)
        self.assertIn('contact the supplier', notif.message)


class SendEscalationEmailTest(TestCase):
    """Test the _send_escalation_email helper."""

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        ESCALATION_RECIPIENT_EMAILS=['mgr@test.com'],
    )
    def test_sends_email_and_updates_status(self):
        po = _make_po()
        notif = EscalationNotification.objects.create(
            po=po,
            reason='email_delivery_failed',
            recipient_email='mgr@test.com',
            message='Test escalation',
        )
        from apps.notifications.service import _send_escalation_email

        _send_escalation_email(notif)
        notif.refresh_from_db()
        self.assertEqual(notif.status, 'sent')
        self.assertIsNotNone(notif.sent_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('[Escalation]', mail.outbox[0].subject)

    @override_settings(ESCALATION_RECIPIENT_EMAILS=[])
    def test_skips_when_no_recipient(self):
        po = _make_po()
        notif = EscalationNotification.objects.create(
            po=po,
            reason='email_delivery_failed',
            recipient_email='',
            message='No recipient',
        )
        from apps.notifications.service import _send_escalation_email

        _send_escalation_email(notif)
        notif.refresh_from_db()
        self.assertEqual(notif.status, 'pending')

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        ESCALATION_RECIPIENT_EMAILS=['mgr@test.com'],
    )
    @patch('infrastructure.email.EmailService.send')
    def test_handles_send_failure(self, mock_send):
        po = _make_po()
        notif = EscalationNotification.objects.create(
            po=po,
            reason='email_delivery_failed',
            recipient_email='mgr@test.com',
            message='Will fail',
        )
        mock_send.side_effect = Exception('SMTP down')
        from apps.notifications.service import _send_escalation_email

        _send_escalation_email(notif)
        notif.refresh_from_db()
        self.assertEqual(notif.status, 'failed')
        self.assertIn('SMTP down', notif.error_message)


class EscalationRecipientsTest(TestCase):
    """Test get_escalation_recipients helper."""

    @override_settings(ESCALATION_RECIPIENT_EMAILS=['a@test.com', 'b@test.com'])
    def test_returns_configured_list(self):
        result = get_escalation_recipients()
        self.assertEqual(result, ['a@test.com', 'b@test.com'])

    @override_settings(ESCALATION_RECIPIENT_EMAILS=[])
    def test_returns_empty_list(self):
        result = get_escalation_recipients()
        self.assertEqual(result, [])


class DefaultMessageTest(TestCase):
    """Test _build_default_message for various reasons."""

    @override_settings(ESCALATION_RECIPIENT_EMAILS=[])
    @patch('apps.notifications.service._send_escalation_email')
    def test_email_failed_default_message(self, mock_send):
        po = _make_po()
        notif = create_escalation_notification(po=po, reason='email_delivery_failed')
        self.assertIn('permanently failed', notif.message)
        self.assertIn('3 retries', notif.message)

    @override_settings(ESCALATION_RECIPIENT_EMAILS=[])
    @patch('apps.notifications.service._send_escalation_email')
    def test_supplier_timeout_default_message(self, mock_send):
        po = _make_po()
        notif = create_escalation_notification(po=po, reason='supplier_timeout')
        self.assertIn('48 hours', notif.message)
        self.assertIn('Action required', notif.message)

    @override_settings(ESCALATION_RECIPIENT_EMAILS=[])
    @patch('apps.notifications.service._send_escalation_email')
    def test_other_reason_default_message(self, mock_send):
        po = _make_po()
        notif = create_escalation_notification(po=po, reason='other')
        self.assertIn('other', notif.message)
        self.assertIn('Action required', notif.message)


class EscalationTriggeredByEmailFailureTest(TestCase):
    """Integration test: email failure triggers escalation."""

    @override_settings(
        ESCALATION_RECIPIENT_EMAILS=['mgr@test.com'],
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    def test_trigger_escalation_creates_notification(self):
        from apps.purchasing.email_tasks import _trigger_escalation

        po = _make_po()
        _trigger_escalation(po.id, 'SMTP timeout')
        self.assertTrue(
            EscalationNotification.objects.filter(po=po, reason='email_delivery_failed').exists()
        )

    @override_settings(
        ESCALATION_RECIPIENT_EMAILS=['mgr@test.com'],
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    def test_trigger_escalation_with_none_po_id(self):
        from apps.purchasing.email_tasks import _trigger_escalation

        _trigger_escalation(None, 'error')
        self.assertEqual(EscalationNotification.objects.count(), 0)


class EscalationTriggeredByTimeoutTest(TestCase):
    """Integration test: supplier timeout triggers escalation."""

    @override_settings(
        ESCALATION_RECIPIENT_EMAILS=['mgr@test.com'],
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    def test_timeout_triggers_escalation(self):
        from apps.purchasing.timeout_tasks import _trigger_escalation

        po = _make_po()
        po.status = 'timeout'
        po.save(update_fields=['status'])

        _trigger_escalation(po)
        self.assertTrue(
            EscalationNotification.objects.filter(po=po, reason='supplier_timeout').exists()
        )
