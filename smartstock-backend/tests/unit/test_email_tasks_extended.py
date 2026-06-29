import smtplib
from unittest.mock import patch

from django.test import TestCase

from apps.purchasing.email_tasks import (
    _trigger_escalation,
    is_retriable,
    send_email_with_retry,
)
from infrastructure.email import MAX_RETRIES


class IsRetriableTest(TestCase):
    def test_smtp_server_disconnected_is_retriable(self):
        self.assertTrue(is_retriable(smtplib.SMTPServerDisconnected()))

    def test_smtp_connect_error_is_retriable(self):
        exc = smtplib.SMTPConnectError(421, b'Service unavailable')
        self.assertTrue(is_retriable(exc))

    def test_smtp_auth_error_not_retriable(self):
        self.assertFalse(is_retriable(smtplib.SMTPAuthenticationError(500, b'bad')))

    def test_smtp_recipients_refused_not_retriable(self):
        self.assertFalse(is_retriable(smtplib.SMTPRecipientsRefused({})))

    def test_connection_error_is_retriable(self):
        self.assertTrue(is_retriable(ConnectionError('timeout')))

    def test_timeout_error_is_retriable(self):
        self.assertTrue(is_retriable(TimeoutError()))

    def test_generic_exception_not_retriable(self):
        self.assertFalse(is_retriable(ValueError('nope')))


class TriggerEscalationTest(TestCase):
    def test_no_po_id_does_nothing(self):
        _trigger_escalation(None, 'error')

    @patch('apps.purchasing.email_tasks.logger')
    def test_exception_in_escalation_is_logged(self, mock_logger):
        with patch(
            'apps.notifications.service.create_escalation_notification',
            side_effect=Exception('db error'),
        ):
            _trigger_escalation(999, 'error')
            mock_logger.exception.assert_called_once()


class SendEmailWithRetryTest(TestCase):
    @patch('infrastructure.email.EmailMessage')
    def test_send_success(self, MockEmail):
        result = send_email_with_retry.__wrapped__(
            subject='Test',
            body='body',
            recipient='a@b.com',
            po_id=1,
            message_id='msg-001',
        )
        self.assertEqual(result['status'], 'sent')
        self.assertEqual(result['attempts'], 1)
        self.assertEqual(result['recipient'], 'a@b.com')
        MockEmail.return_value.send.assert_called_once()

    @patch('infrastructure.email.EmailMessage')
    def test_send_generates_message_id(self, MockEmail):
        result = send_email_with_retry.__wrapped__(
            subject='Test',
            body='body',
            recipient='a@b.com',
        )
        self.assertIn('email-', result['message_id'])

    @patch(
        'infrastructure.email.EmailMessage',
        side_effect=smtplib.SMTPAuthenticationError(500, b'bad'),
    )
    def test_non_retriable_failure(self, MockEmail):
        result = send_email_with_retry.__wrapped__(
            subject='Test',
            body='body',
            recipient='a@b.com',
            po_id=1,
            message_id='msg-auth',
        )
        self.assertEqual(result['status'], 'permanently_failed')
        self.assertEqual(result['attempts'], 1)

    @patch('infrastructure.email.EmailMessage')
    def test_no_po_id_skips_escalation(self, MockEmail):
        result = send_email_with_retry.__wrapped__(
            subject='Test',
            body='body',
            recipient='a@b.com',
            po_id=None,
            message_id='msg-002',
        )
        self.assertEqual(result['status'], 'sent')
        self.assertEqual(result['attempts'], 1)
