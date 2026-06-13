import smtplib
from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.purchasing.email_tasks import (
    MAX_RETRIES,
    RETRY_COUNTDOWN,
    is_retriable,
)


class IsRetriableTest(TestCase):
    """Test the is_retriable helper function."""

    def test_smtp_server_disconnected_is_retriable(self):
        self.assertTrue(is_retriable(smtplib.SMTPServerDisconnected()))

    def test_smtp_connect_error_is_retriable(self):
        self.assertTrue(is_retriable(smtplib.SMTPConnectError(421, b'temp')))

    def test_smtp_helo_error_is_retriable(self):
        self.assertTrue(is_retriable(smtplib.SMTPHeloError(421, b'helo failed')))

    def test_smtp_response_exception_is_retriable(self):
        self.assertTrue(is_retriable(smtplib.SMTPResponseException(421, b'temp')))

    def test_smtp_exception_is_retriable(self):
        self.assertTrue(is_retriable(smtplib.SMTPException('temp')))

    def test_connection_error_is_retriable(self):
        self.assertTrue(is_retriable(ConnectionError('reset')))

    def test_timeout_error_is_retriable(self):
        self.assertTrue(is_retriable(TimeoutError('timed out')))

    def test_os_error_is_retriable(self):
        self.assertTrue(is_retriable(OSError('network')))

    def test_smtp_auth_error_not_retriable(self):
        self.assertFalse(is_retriable(smtplib.SMTPAuthenticationError(535, b'bad')))

    def test_smtp_recipients_refused_not_retriable(self):
        self.assertFalse(is_retriable(smtplib.SMTPRecipientsRefused({})))

    def test_smtp_sender_refused_not_retriable(self):
        self.assertFalse(is_retriable(smtplib.SMTPSenderRefused(550, b'x', b's')))

    def test_generic_exception_not_retriable(self):
        self.assertFalse(is_retriable(ValueError('bad')))

    def test_all_retriable_samples(self):
        for exc in [
            smtplib.SMTPServerDisconnected(),
            smtplib.SMTPConnectError(421, b't'),
            smtplib.SMTPHeloError(421, b'h'),
            smtplib.SMTPResponseException(421, b't'),
            smtplib.SMTPException('t'),
            ConnectionError('r'),
            TimeoutError('t'),
            OSError('n'),
        ]:
            self.assertTrue(is_retriable(exc), f'{type(exc).__name__}')

    def test_all_non_retriable_samples(self):
        for exc in [
            smtplib.SMTPAuthenticationError(535, b'b'),
            smtplib.SMTPRecipientsRefused({}),
            smtplib.SMTPSenderRefused(550, b'r', b's'),
        ]:
            self.assertFalse(is_retriable(exc), f'{type(exc).__name__}')


class RetryCountdownTest(TestCase):
    def test_countdown_values(self):
        self.assertEqual(RETRY_COUNTDOWN, [30, 120, 600])

    def test_first_retry_30s(self):
        self.assertEqual(RETRY_COUNTDOWN[0], 30)

    def test_second_retry_2min(self):
        self.assertEqual(RETRY_COUNTDOWN[1], 120)

    def test_third_retry_10min(self):
        self.assertEqual(RETRY_COUNTDOWN[2], 600)

    def test_max_retries(self):
        self.assertEqual(MAX_RETRIES, 3)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='test@smartstock.ai',
    ESCALATION_RECIPIENT_EMAILS=['manager@smartstock.ai'],
)
class SendEmailWithRetryTest(TestCase):
    """Tests for the send_email_with_retry task via __wrapped__."""

    @patch('apps.purchasing.email_tasks._trigger_escalation')
    def test_success_first_attempt(self, mock_escalation):
        from apps.purchasing.email_tasks import send_email_with_retry

        result = send_email_with_retry.__wrapped__(
            subject='Test',
            body='Hello',
            recipient='supplier@example.com',
            po_id=1,
            message_id='msg-001',
        )
        self.assertEqual(result['status'], 'sent')
        self.assertEqual(result['attempts'], 1)
        self.assertEqual(result['message_id'], 'msg-001')
        mock_escalation.assert_not_called()

    @patch('apps.purchasing.email_tasks._trigger_escalation')
    def test_success_sends_email(self, mock_escalation):
        from apps.purchasing.email_tasks import send_email_with_retry

        send_email_with_retry.__wrapped__(
            subject='PO Test',
            body='Body',
            recipient='supplier@example.com',
        )
        from django.core.mail import outbox

        self.assertEqual(len(outbox), 1)
        self.assertEqual(outbox[0].subject, 'PO Test')
        self.assertEqual(outbox[0].to, ['supplier@example.com'])

    @patch('apps.purchasing.email_tasks._trigger_escalation')
    @patch('django.core.mail.EmailMessage.send')
    def test_non_retriable_auth_error(self, mock_send, mock_escalation):
        from apps.purchasing.email_tasks import send_email_with_retry

        mock_send.side_effect = smtplib.SMTPAuthenticationError(535, b'bad')
        result = send_email_with_retry.__wrapped__(
            subject='Test',
            body='Hello',
            recipient='a@b.com',
            po_id=1,
            message_id='msg-auth',
        )
        self.assertEqual(result['status'], 'permanently_failed')
        self.assertEqual(result['attempts'], 1)
        mock_escalation.assert_called_once()

    @patch('apps.purchasing.email_tasks._trigger_escalation')
    @patch('django.core.mail.EmailMessage.send')
    def test_non_retriable_recipients_refused(self, mock_send, mock_escalation):
        from apps.purchasing.email_tasks import send_email_with_retry

        mock_send.side_effect = smtplib.SMTPRecipientsRefused({'bad@x.com': (550, b'no')})
        result = send_email_with_retry.__wrapped__(
            subject='Test',
            body='Hello',
            recipient='bad@x.com',
            po_id=2,
        )
        self.assertEqual(result['status'], 'permanently_failed')

    @patch('apps.purchasing.email_tasks._trigger_escalation')
    @patch('django.core.mail.EmailMessage.send')
    def test_non_retriable_sender_refused(self, mock_send, mock_escalation):
        from apps.purchasing.email_tasks import send_email_with_retry

        mock_send.side_effect = smtplib.SMTPSenderRefused(550, b'r', b's')
        result = send_email_with_retry.__wrapped__(
            subject='Test',
            body='Hello',
            recipient='a@b.com',
            po_id=9,
        )
        self.assertEqual(result['status'], 'permanently_failed')
        self.assertEqual(result['attempts'], 1)

    @patch('apps.purchasing.email_tasks._trigger_escalation')
    def test_generates_message_id_if_not_provided(self, mock_escalation):
        from apps.purchasing.email_tasks import send_email_with_retry

        result = send_email_with_retry.__wrapped__(
            subject='Test',
            body='Hello',
            recipient='supplier@example.com',
        )
        self.assertTrue(result['message_id'].startswith('email-'))

    @patch('apps.purchasing.email_tasks._trigger_escalation')
    def test_uses_default_from_email(self, mock_escalation):
        from apps.purchasing.email_tasks import send_email_with_retry

        send_email_with_retry.__wrapped__(
            subject='Test',
            body='Hello',
            recipient='supplier@example.com',
        )
        from django.core.mail import outbox

        self.assertEqual(outbox[0].from_email, 'test@smartstock.ai')

    @patch('apps.purchasing.email_tasks._trigger_escalation')
    def test_result_includes_po_id(self, mock_escalation):
        from apps.purchasing.email_tasks import send_email_with_retry

        result = send_email_with_retry.__wrapped__(
            subject='Test',
            body='Hello',
            recipient='a@b.com',
            po_id=42,
        )
        self.assertEqual(result['po_id'], 42)

    @patch('apps.purchasing.email_tasks._trigger_escalation')
    def test_result_includes_recipient(self, mock_escalation):
        from apps.purchasing.email_tasks import send_email_with_retry

        result = send_email_with_retry.__wrapped__(
            subject='Test',
            body='Hello',
            recipient='supplier@example.com',
        )
        self.assertEqual(result['recipient'], 'supplier@example.com')

    @patch('apps.purchasing.email_tasks._trigger_escalation')
    @patch('django.core.mail.EmailMessage.send')
    def test_retriable_error_raises_for_retry(self, mock_send, mock_escalation):
        """Retriable errors should raise so Celery can retry."""
        from apps.purchasing.email_tasks import send_email_with_retry

        mock_send.side_effect = smtplib.SMTPServerDisconnected('lost')
        with self.assertRaises(smtplib.SMTPServerDisconnected):
            send_email_with_retry.__wrapped__(
                subject='Test',
                body='Hello',
                recipient='a@b.com',
                po_id=3,
            )

    @patch('apps.purchasing.email_tasks._trigger_escalation')
    @patch('django.core.mail.EmailMessage.send')
    def test_connection_error_raises_for_retry(self, mock_send, mock_escalation):
        from apps.purchasing.email_tasks import send_email_with_retry

        mock_send.side_effect = ConnectionError('reset')
        with self.assertRaises(ConnectionError):
            send_email_with_retry.__wrapped__(
                subject='Test',
                body='Hello',
                recipient='a@b.com',
                po_id=6,
            )

    @patch('apps.purchasing.email_tasks._trigger_escalation')
    @patch('django.core.mail.EmailMessage.send')
    def test_timeout_error_raises_for_retry(self, mock_send, mock_escalation):
        from apps.purchasing.email_tasks import send_email_with_retry

        mock_send.side_effect = TimeoutError('timed out')
        with self.assertRaises(TimeoutError):
            send_email_with_retry.__wrapped__(
                subject='Test',
                body='Hello',
                recipient='a@b.com',
                po_id=7,
            )

    @patch('apps.purchasing.email_tasks._trigger_escalation')
    @patch('django.core.mail.EmailMessage.send')
    def test_smtp_connect_error_raises_for_retry(self, mock_send, mock_escalation):
        from apps.purchasing.email_tasks import send_email_with_retry

        mock_send.side_effect = smtplib.SMTPConnectError(421, b'conn refused')
        with self.assertRaises(smtplib.SMTPConnectError):
            send_email_with_retry.__wrapped__(
                subject='Test',
                body='Hello',
                recipient='a@b.com',
                po_id=4,
            )

    @patch('apps.purchasing.email_tasks._trigger_escalation')
    @patch('django.core.mail.EmailMessage.send')
    def test_smtp_response_error_raises_for_retry(self, mock_send, mock_escalation):
        from apps.purchasing.email_tasks import send_email_with_retry

        mock_send.side_effect = smtplib.SMTPResponseException(421, b'temp')
        with self.assertRaises(smtplib.SMTPResponseException):
            send_email_with_retry.__wrapped__(
                subject='Test',
                body='Hello',
                recipient='a@b.com',
                po_id=5,
            )

    @patch('apps.purchasing.email_tasks._trigger_escalation')
    def test_trigger_escalation_handles_po_not_found(self, mock_escalation):
        """_trigger_escalation should not raise when PO doesn't exist."""
        from apps.purchasing.email_tasks import _trigger_escalation

        # Should not raise
        _trigger_escalation(999999, 'test error')
        # _trigger_escalation catches the DoesNotExist internally

    def test_trigger_escalation_handles_notification_failure(self):
        """_trigger_escalation should not raise when notification creation fails."""
        from apps.inventory.models import SKU, Product, Supplier
        from apps.purchasing.email_tasks import _trigger_escalation
        from apps.purchasing.models import PurchaseOrder

        supplier = Supplier.objects.create(name='Test', contact_email='t@t.com')
        product = Product.objects.create(name='W', unit_price=1.0)
        sku = SKU.objects.create(product=product, code='SKU-ERR')
        po = PurchaseOrder.objects.create(
            sku=sku,
            supplier=supplier,
            quantity=1,
            total_cost=1.0,
            status='failed',
        )
        # Mock create_escalation_notification to raise
        with patch(
            'apps.notifications.service.create_escalation_notification',
            side_effect=Exception('db error'),
        ):
            # Should not raise
            _trigger_escalation(po.id, 'test error')
