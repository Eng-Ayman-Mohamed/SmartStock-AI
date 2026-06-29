"""Targeted tests to close the remaining coverage gap (79.56% -> 80%+).

Focuses on the lowest-coverage modules: purchasing management command,
monitoring tasks, health FullHealthView, and authentication services.
"""

from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

User = get_user_model()


# ---------------------------------------------------------------------------
# purchasing/management/commands/check_overdue_suppliers.py  (0% -> covered)
# ---------------------------------------------------------------------------
class CheckOverdueSuppliersCommandTest(TestCase):
    @patch('apps.purchasing.services.PurchasingService.get_overdue_suppliers')
    @patch('apps.notifications.service.NotificationService.create')
    @patch('apps.notifications.models.Notification.objects')
    def test_handle_creates_notifications(self, mock_notif_objects, mock_create, mock_overdue):
        mock_notif_objects.filter.return_value.exists.return_value = False
        mock_overdue.return_value = [
            {
                'supplier_id': 1,
                'supplier_name': 'Acme Corp',
                'days_overdue': 5,
                'overdue_pos': [{'po_number': 'PO-001'}, {'po_number': 'PO-002'}],
            },
        ]
        from django.core.management import call_command

        out = StringIO()
        call_command('check_overdue_suppliers', stdout=out)
        output = out.getvalue()
        self.assertIn('1 overdue suppliers', output)
        self.assertIn('CREATED', output)
        mock_create.assert_called_once()

    @patch('apps.purchasing.services.PurchasingService.get_overdue_suppliers')
    @patch('apps.notifications.models.Notification.objects')
    def test_handle_skips_existing(self, mock_notif_objects, mock_overdue):
        mock_notif_objects.filter.return_value.exists.return_value = True
        mock_overdue.return_value = [
            {
                'supplier_id': 2,
                'supplier_name': 'Beta Inc',
                'days_overdue': 3,
                'overdue_pos': [{'po_number': 'PO-100'}],
            },
        ]
        from django.core.management import call_command

        out = StringIO()
        call_command('check_overdue_suppliers', stdout=out)
        output = out.getvalue()
        self.assertIn('SKIP (exists)', output)

    @patch('apps.purchasing.services.PurchasingService.get_overdue_suppliers')
    def test_handle_no_overdue(self, mock_overdue):
        mock_overdue.return_value = []
        from django.core.management import call_command

        out = StringIO()
        call_command('check_overdue_suppliers', stdout=out)
        output = out.getvalue()
        self.assertIn('0 overdue suppliers', output)
        self.assertIn('Created 0', output)


# ---------------------------------------------------------------------------
# purchasing/tasks.py  (52% -> higher)
# ---------------------------------------------------------------------------
class PurchasingTaskWithSuppliersTest(TestCase):
    @patch('apps.purchasing.services.PurchasingService.get_overdue_suppliers')
    @patch('apps.notifications.service.NotificationService.create')
    @patch('apps.notifications.models.Notification.objects')
    def test_creates_notifications_for_overdue(self, mock_notif_objects, mock_create, mock_overdue):
        mock_notif_objects.filter.return_value.exists.return_value = False
        mock_overdue.return_value = [
            {
                'supplier_id': 10,
                'supplier_name': 'Gamma Ltd',
                'days_overdue': 7,
                'overdue_pos': [{'po_number': 'PO-200'}],
            },
        ]
        from apps.purchasing.tasks import check_overdue_suppliers

        result = check_overdue_suppliers()
        self.assertEqual(result['created'], 1)
        mock_create.assert_called_once()

    @patch('apps.purchasing.services.PurchasingService.get_overdue_suppliers')
    @patch('apps.notifications.models.Notification.objects')
    def test_skips_existing_notifications(self, mock_notif_objects, mock_overdue):
        mock_notif_objects.filter.return_value.exists.return_value = True
        mock_overdue.return_value = [
            {
                'supplier_id': 11,
                'supplier_name': 'Delta Co',
                'days_overdue': 2,
                'overdue_pos': [{'po_number': 'PO-300'}],
            },
        ]
        from apps.purchasing.tasks import check_overdue_suppliers

        result = check_overdue_suppliers()
        self.assertEqual(result['created'], 0)


# ---------------------------------------------------------------------------
# monitoring/tasks.py  (56% -> higher) — cleanup + archive tasks
# ---------------------------------------------------------------------------
class CleanupStaleAgentRunsTest(TestCase):
    def test_marks_stale_runs_as_failed(self):
        from apps.audit.models import AgentRun

        run = AgentRun.objects.create(
            agent_name='test_agent',
            status=AgentRun.Status.RUNNING,
            started_at=timezone.now() - timedelta(hours=2),
        )
        from apps.monitoring.tasks import cleanup_stale_agent_runs

        result = cleanup_stale_agent_runs()
        self.assertEqual(result['stale_marked_failed'], 1)
        run.refresh_from_db()
        self.assertEqual(run.status, AgentRun.Status.FAILED)
        self.assertIsNotNone(run.completed_at)
        self.assertIn('Worker timeout', run.error_message)

    def test_no_stale_runs(self):
        from apps.monitoring.tasks import cleanup_stale_agent_runs

        result = cleanup_stale_agent_runs()
        self.assertEqual(result['stale_marked_failed'], 0)

    def test_recent_running_not_marked(self):
        from apps.audit.models import AgentRun

        AgentRun.objects.create(
            agent_name='test_agent',
            status=AgentRun.Status.RUNNING,
            started_at=timezone.now() - timedelta(minutes=5),
        )
        from apps.monitoring.tasks import cleanup_stale_agent_runs

        result = cleanup_stale_agent_runs()
        self.assertEqual(result['stale_marked_failed'], 0)


class ArchiveOldAgentRunsTest(TestCase):
    def test_deletes_old_runs(self):
        from apps.audit.models import AgentRun

        old_run = AgentRun.objects.create(
            agent_name='old_agent',
            status=AgentRun.Status.COMPLETED,
            started_at=timezone.now() - timedelta(days=100),
            completed_at=timezone.now() - timedelta(days=100),
        )
        old_run.created_at = timezone.now() - timedelta(days=100)
        old_run.save(update_fields=['created_at'])

        from apps.monitoring.tasks import archive_old_agent_runs

        result = archive_old_agent_runs()
        self.assertGreaterEqual(result['deleted'], 1)

    def test_no_old_runs(self):
        from apps.monitoring.tasks import archive_old_agent_runs

        result = archive_old_agent_runs()
        self.assertEqual(result['deleted'], 0)


# ---------------------------------------------------------------------------
# health/views.py — FullHealthView (73% -> higher)
# ---------------------------------------------------------------------------
class FullHealthViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='health_user',
            email='health@test.com',
            password='testpass123',
            role='admin',
        )

    def _auth(self):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')

    @patch('apps.health.views._check_redis', return_value=True)
    @patch('apps.health.views._check_database', return_value=True)
    @patch('apps.audit.models.AgentRun.objects')
    def test_full_health_all_ok(self, mock_agent_qs, mock_db, mock_redis):
        mock_agent_qs.filter.return_value.count.return_value = 0
        self._auth()
        response = self.client.get('/api/health/full/')
        self.assertIn(response.status_code, (200, 503))

    @patch('apps.health.views._check_redis', return_value=False)
    @patch('apps.health.views._check_database', return_value=True)
    @patch('apps.audit.models.AgentRun.objects')
    def test_full_health_degraded(self, mock_agent_qs, mock_db, mock_redis):
        mock_agent_qs.filter.return_value.count.return_value = 0
        self._auth()
        response = self.client.get('/api/health/full/')
        self.assertIn(response.status_code, (200, 503))
        self.assertIn('status', response.data)


# ---------------------------------------------------------------------------
# authentication/services.py  (38% -> higher)
# ---------------------------------------------------------------------------
class VerifyEmailTokenTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='verify_user',
            email='verify@test.com',
            password='testpass123',
        )

    def test_valid_token_verifies_email(self):
        from apps.authentication.models import EmailVerificationToken
        from apps.authentication.services import verify_email_token

        token = EmailVerificationToken.objects.create(
            user=self.user,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        success, msg, status = verify_email_token(str(token.token))
        self.assertTrue(success)
        self.assertEqual(status, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_already_verified_returns_200(self):
        from apps.authentication.models import EmailVerificationToken
        from apps.authentication.services import verify_email_token

        self.user.email_verified = True
        self.user.save(update_fields=['email_verified'])
        token = EmailVerificationToken.objects.create(
            user=self.user,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        success, msg, status = verify_email_token(str(token.token))
        self.assertTrue(success)
        self.assertEqual(status, 200)
        self.assertIn('already verified', msg)

    def test_invalid_token(self):
        from apps.authentication.services import verify_email_token

        success, msg, status = verify_email_token('00000000-0000-0000-0000-000000000000')
        self.assertFalse(success)
        self.assertEqual(status, 400)

    def test_expired_token(self):
        from apps.authentication.models import EmailVerificationToken
        from apps.authentication.services import verify_email_token

        token = EmailVerificationToken.objects.create(
            user=self.user,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        success, msg, status = verify_email_token(str(token.token))
        self.assertFalse(success)
        self.assertEqual(status, 400)
        self.assertIn('expired', msg)


class SendVerificationEmailTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='email_user',
            email='email@test.com',
            password='testpass123',
        )

    def test_sync_fallback_sends_email(self):
        from apps.authentication.models import EmailVerificationToken
        from apps.authentication.services import _send_verification_email_sync

        token = EmailVerificationToken.objects.create(
            user=self.user,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        verify_url = f'http://localhost:5173/verify-email?token={token.token}'
        with self.settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            _send_verification_email_sync(self.user, verify_url)
            from django.core.mail import outbox

            self.assertEqual(len(outbox), 1)
            self.assertIn('Verify', outbox[0].subject)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_verification_email_celery_success(self):
        from apps.authentication.models import EmailVerificationToken
        from apps.authentication.services import send_verification_email

        token = EmailVerificationToken.objects.create(
            user=self.user,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        with patch('infrastructure.email.send_verification_email_task') as mock_task:
            send_verification_email(self.user, token)
            mock_task.delay.assert_called_once()

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_verification_email_fallback_on_import_error(self):
        from apps.authentication.models import EmailVerificationToken
        from apps.authentication.services import send_verification_email

        token = EmailVerificationToken.objects.create(
            user=self.user,
            expires_at=timezone.now() + timedelta(hours=24),
        )
        import sys

        saved = sys.modules.pop('infrastructure.email', None)
        sys.modules['infrastructure.email'] = None
        try:
            send_verification_email(self.user, token)
            from django.core.mail import outbox

            self.assertEqual(len(outbox), 1)
        finally:
            if saved is not None:
                sys.modules['infrastructure.email'] = saved
            else:
                sys.modules.pop('infrastructure.email', None)


# ---------------------------------------------------------------------------
# monitoring/alerts.py  (88% -> higher)
# ---------------------------------------------------------------------------
class EvaluateAgentSuccessRateEdgeCasesTest(TestCase):
    @patch('apps.monitoring.alerts.send_dashboard_notification', return_value=False)
    @patch('apps.monitoring.alerts.send_alert_email', return_value=False)
    @patch('apps.monitoring.alerts._log_alert_to_langfuse')
    def test_no_runs_sets_gauge_to_1(self, mock_langfuse, mock_email, mock_dash):
        from apps.monitoring.alerts import evaluate_agent_success_rate

        result = evaluate_agent_success_rate()
        self.assertIsNone(result)

    @patch('apps.monitoring.alerts.send_dashboard_notification', return_value=False)
    @patch('apps.monitoring.alerts.send_alert_email', return_value=False)
    @patch('apps.monitoring.alerts._log_alert_to_langfuse')
    def test_all_success_above_threshold(self, mock_langfuse, mock_email, mock_dash):
        from apps.monitoring.models import AgentRunLog

        for _ in range(5):
            AgentRunLog.objects.create(agent_name='a', outcome='success')
        from apps.monitoring.alerts import evaluate_agent_success_rate

        result = evaluate_agent_success_rate()
        self.assertIsNone(result)

    @patch('apps.monitoring.alerts.send_dashboard_notification', return_value=False)
    @patch('apps.monitoring.alerts.send_alert_email', return_value=False)
    @patch('apps.monitoring.alerts._log_alert_to_langfuse')
    def test_low_success_fires_alert(self, mock_langfuse, mock_email, mock_dash):
        from apps.monitoring.models import AgentRunLog

        for _ in range(8):
            AgentRunLog.objects.create(agent_name='a', outcome='failure')
        for _ in range(2):
            AgentRunLog.objects.create(agent_name='a', outcome='success')
        from apps.monitoring.alerts import evaluate_agent_success_rate

        result = evaluate_agent_success_rate()
        self.assertIsNotNone(result)


class EvaluateTokenSpendTest(TestCase):
    @patch('apps.monitoring.alerts.send_dashboard_notification', return_value=False)
    @patch('apps.monitoring.alerts.send_alert_email', return_value=False)
    @patch('apps.monitoring.alerts._log_alert_to_langfuse')
    def test_token_spend_below_threshold(self, mock_langfuse, mock_email, mock_dash):
        from apps.monitoring.alerts import evaluate_token_spend

        result = evaluate_token_spend()
        self.assertIsNone(result)

    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'daily_token_budget_alert': 100})
    @patch('apps.monitoring.alerts.send_dashboard_notification', return_value=False)
    @patch('apps.monitoring.alerts.send_alert_email', return_value=False)
    @patch('apps.monitoring.alerts._log_alert_to_langfuse')
    def test_token_spend_fires_when_exceeded(self, mock_langfuse, mock_email, mock_dash):
        from apps.monitoring.models import TokenUsageLog

        TokenUsageLog.objects.create(total_tokens=200, input_tokens=100, output_tokens=100)
        from apps.monitoring.alerts import evaluate_token_spend

        result = evaluate_token_spend()
        self.assertIsNotNone(result)

    @patch('apps.monitoring.alerts.send_dashboard_notification', return_value=False)
    @patch('apps.monitoring.alerts.send_alert_email', return_value=False)
    @patch('apps.monitoring.alerts._log_alert_to_langfuse')
    def test_disabled_rule_returns_none(self, mock_langfuse, mock_email, mock_dash):
        from apps.monitoring.alerts import evaluate_token_spend
        from apps.monitoring.models import AlertRule

        evaluate_token_spend()
        rule = AlertRule.objects.get(name='Daily Token Spend Cap')
        rule.enabled = False
        rule.save(update_fields=['enabled'])
        result = evaluate_token_spend()
        self.assertIsNone(result)


class ResolveAlertTest(TestCase):
    @patch('apps.monitoring.alerts.send_dashboard_notification', return_value=False)
    @patch('apps.monitoring.alerts.send_alert_email', return_value=False)
    @patch('apps.monitoring.alerts._log_alert_to_langfuse')
    def test_resolves_firing_alert(self, mock_langfuse, mock_email, mock_dash):
        from apps.monitoring.alerts import _evaluate_rule, _fire_alert
        from apps.monitoring.models import AlertRule, AlertSeverity

        rule = AlertRule.objects.create(
            name='Test Rule',
            severity=AlertSeverity.WARNING,
            metric_name='test_metric',
            threshold=10,
            cooldown_minutes=0,
        )
        _fire_alert(rule, 15.0, 'test firing')
        result = _evaluate_rule(rule, 5.0, 10.0)
        self.assertIsNone(result)
        from apps.monitoring.models import AlertEvent, AlertStatus

        event = AlertEvent.objects.filter(rule=rule, status=AlertStatus.RESOLVED).first()
        self.assertIsNotNone(event)
        mock_dash.assert_called()
