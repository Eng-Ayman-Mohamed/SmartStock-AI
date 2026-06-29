from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.monitoring.notifications import (
    _severity_to_banner_level,
    send_alert_email,
    send_dashboard_notification,
)


class SendAlertEmailTest(TestCase):
    def _make_alert_event(self, severity='warning', status='firing', name='Test Rule'):
        event = MagicMock()
        event.rule.severity = severity
        event.rule.name = name
        event.rule.get_severity_display.return_value = 'Warning'
        event.rule.metric_name = 'test_metric'
        event.rule.threshold = 100.0
        event.status = status
        event.get_status_display.return_value = 'Firing'
        event.triggered_value = 150.0
        event.message = 'Test alert message'
        event.resolved_at = None
        return event

    @patch('infrastructure.email.send_alert_email_task')
    def test_send_email_success(self, mock_task):
        mock_task.delay.return_value = MagicMock(id='task-123')
        event = self._make_alert_event()
        with self.settings(ESCALATION_RECIPIENT_EMAILS=['admin@example.com']):
            result = send_alert_email(event)
        self.assertTrue(result)
        mock_task.delay.assert_called_once()

    def test_no_recipients_skips(self):
        event = self._make_alert_event()
        with self.settings(ESCALATION_RECIPIENT_EMAILS=[]):
            result = send_alert_email(event)
        self.assertFalse(result)

    @patch('infrastructure.email.send_alert_email_task')
    def test_send_email_failure(self, mock_task):
        mock_task.delay.side_effect = Exception('Celery fail')
        event = self._make_alert_event()
        with self.settings(ESCALATION_RECIPIENT_EMAILS=['admin@example.com']):
            result = send_alert_email(event)
        self.assertFalse(result)

    @patch('infrastructure.email.send_alert_email_task')
    def test_resolved_status_changes_subject(self, mock_task):
        mock_task.delay.return_value = MagicMock(id='task-123')
        event = self._make_alert_event(status='resolved')
        event.resolved_at = MagicMock()
        event.resolved_at.isoformat.return_value = '2026-01-01T00:00:00'
        with self.settings(ESCALATION_RECIPIENT_EMAILS=['admin@example.com']):
            result = send_alert_email(event)
        self.assertTrue(result)
        call_kwargs = mock_task.delay.call_args
        subject = call_kwargs.kwargs.get('subject', call_kwargs[1].get('subject', ''))
        self.assertIn('[RESOLVED]', subject)

    @patch('infrastructure.email.send_alert_email_task')
    def test_critical_severity(self, mock_task):
        mock_task.delay.return_value = MagicMock(id='task-123')
        event = self._make_alert_event(severity='critical')
        with self.settings(ESCALATION_RECIPIENT_EMAILS=['admin@example.com']):
            result = send_alert_email(event)
        self.assertTrue(result)
        call_kwargs = mock_task.delay.call_args
        subject = call_kwargs.kwargs.get('subject', call_kwargs[1].get('subject', ''))
        self.assertIn('[CRITICAL]', subject)


class SendDashboardNotificationTest(TestCase):
    def _make_alert_event(self):
        event = MagicMock()
        event.rule.severity = 'warning'
        event.rule.name = 'Test Alert'
        event.message = 'Alert message'
        return event

    @patch('apps.monitoring.notifications.NotificationService')
    @patch('apps.monitoring.models.DashboardBanner.objects')
    def test_create_banner_success(self, mock_banner_mgr, mock_notification_svc):
        event = self._make_alert_event()
        result = send_dashboard_notification(event)
        self.assertTrue(result)
        mock_banner_mgr.create.assert_called_once()
        mock_notification_svc.create.assert_called_once()

    @patch(
        'apps.monitoring.models.DashboardBanner.objects.create',
        side_effect=Exception('DB error'),
    )
    def test_create_banner_failure(self, mock_create):
        event = self._make_alert_event()
        result = send_dashboard_notification(event)
        self.assertFalse(result)


class SeverityToBannerLevelTest(TestCase):
    def test_info_maps_to_info(self):
        from apps.monitoring.models import AlertSeverity, DashboardBanner

        result = _severity_to_banner_level(AlertSeverity.INFO)
        self.assertEqual(result, DashboardBanner.Level.INFO)

    def test_warning_maps_to_warning(self):
        from apps.monitoring.models import AlertSeverity, DashboardBanner

        result = _severity_to_banner_level(AlertSeverity.WARNING)
        self.assertEqual(result, DashboardBanner.Level.WARNING)

    def test_critical_maps_to_error(self):
        from apps.monitoring.models import AlertSeverity, DashboardBanner

        result = _severity_to_banner_level(AlertSeverity.CRITICAL)
        self.assertEqual(result, DashboardBanner.Level.ERROR)

    def test_unknown_severity_defaults_to_info(self):
        from apps.monitoring.models import DashboardBanner

        result = _severity_to_banner_level('unknown')
        self.assertEqual(result, DashboardBanner.Level.INFO)
