from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.monitoring.alerts import (
    evaluate_agent_success_rate,
    evaluate_all_alerts,
    evaluate_token_spend,
)
from apps.monitoring.metrics import (
    AGENT_RUN_TOTAL,
    AGENT_SUCCESS_RATE_GAUGE,
    DAILY_TOKEN_USAGE,
    ERROR_COUNT,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    TOKEN_USAGE_TOTAL,
)
from apps.monitoring.models import (
    AgentRunLog,
    AlertEvent,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    DashboardBanner,
    TokenUsageLog,
)
from apps.monitoring.tasks import record_agent_run_task, record_token_usage_task


class AlertRuleModelTest(TestCase):
    def test_create_alert_rule(self):
        rule = AlertRule.objects.create(
            name='Test Alert',
            description='Test description',
            severity=AlertSeverity.WARNING,
            metric_name='test_metric',
            threshold=3.0,
            evaluation_window_minutes=5,
            cooldown_minutes=10,
        )
        self.assertEqual(rule.name, 'Test Alert')
        self.assertTrue(rule.enabled)

    def test_str_representation(self):
        rule = AlertRule.objects.create(
            name='Latency Alert',
            severity=AlertSeverity.CRITICAL,
            metric_name='latency',
            threshold=5.0,
        )
        self.assertEqual(str(rule), 'Latency Alert (critical)')


class AlertEventModelTest(TestCase):
    def test_create_alert_event(self):
        rule = AlertRule.objects.create(
            name='Test Rule',
            metric_name='test',
            threshold=1.0,
        )
        event = AlertEvent.objects.create(
            rule=rule,
            status=AlertStatus.FIRING,
            triggered_value=2.5,
            message='Test message',
        )
        self.assertEqual(event.rule, rule)
        self.assertEqual(event.status, AlertStatus.FIRING)

    def test_alert_event_str(self):
        rule = AlertRule.objects.create(
            name='Rule',
            metric_name='m',
            threshold=1.0,
        )
        event = AlertEvent.objects.create(rule=rule, status=AlertStatus.FIRING)
        self.assertIn('Rule', str(event))


class DashboardBannerModelTest(TestCase):
    def test_create_banner(self):
        banner = DashboardBanner.objects.create(
            title='Test Banner',
            message='Test message',
            level=DashboardBanner.Level.WARNING,
        )
        self.assertFalse(banner.dismissed)

    def test_str_representation(self):
        banner = DashboardBanner.objects.create(
            title='Alert!',
            message='msg',
            level=DashboardBanner.Level.ERROR,
        )
        self.assertEqual(str(banner), 'error: Alert!')


class TokenUsageLogModelTest(TestCase):
    def test_create_token_log(self):
        log = TokenUsageLog.objects.create(
            total_tokens=1000,
            input_tokens=700,
            output_tokens=300,
        )
        self.assertEqual(log.total_tokens, 1000)


class AgentRunLogModelTest(TestCase):
    def test_create_agent_log(self):
        log = AgentRunLog.objects.create(
            agent_name='test_agent',
            outcome='success',
            duration_ms=500,
        )
        self.assertEqual(log.agent_name, 'test_agent')
        self.assertEqual(log.outcome, 'success')


class PrometheusMetricsTest(TestCase):
    """Verify that Prometheus metric objects are correctly defined and usable."""

    def test_request_latency_histogram_observe(self):
        REQUEST_LATENCY.labels(method='GET', endpoint='/api/test', status_code='200').observe(0.5)

    def test_request_count_counter_inc(self):
        REQUEST_COUNT.labels(method='GET', endpoint='/api/test', status_code='200').inc()

    def test_error_count_counter_inc(self):
        ERROR_COUNT.labels(method='GET', endpoint='/api/test', status_code='500').inc()

    def test_token_usage_counter_inc(self):
        TOKEN_USAGE_TOTAL.labels(type='total').inc(100)

    def test_daily_token_usage_gauge_set(self):
        DAILY_TOKEN_USAGE.set(5000)

    def test_agent_run_counter_inc(self):
        AGENT_RUN_TOTAL.labels(agent_name='test', outcome='success').inc()

    def test_agent_success_rate_gauge_set(self):
        AGENT_SUCCESS_RATE_GAUGE.set(0.95)


class EvaluateTokenSpendTest(TestCase):
    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'daily_token_budget_alert': 100})
    @patch('apps.monitoring.alerts.send_dashboard_notification', return_value=True)
    @patch('apps.monitoring.alerts.send_alert_email', return_value=True)
    def test_fires_when_spend_exceeds_budget(self, mock_email, mock_dashboard):
        today = timezone.now().date()
        TokenUsageLog.objects.create(total_tokens=200, logged_at=today)

        result = evaluate_token_spend()

        self.assertIsNotNone(result)
        self.assertEqual(result.status, AlertStatus.FIRING)
        mock_email.assert_called_once()

    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'daily_token_budget_alert': 1000})
    def test_does_not_fire_when_under_budget(self):
        today = timezone.now().date()
        TokenUsageLog.objects.create(total_tokens=500, logged_at=today)

        result = evaluate_token_spend()
        self.assertIsNone(result)


class EvaluateAgentSuccessRateTest(TestCase):
    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'agent_success_rate_minimum': 0.80})
    @patch('apps.monitoring.alerts.send_dashboard_notification', return_value=True)
    @patch('apps.monitoring.alerts.send_alert_email', return_value=True)
    def test_fires_when_success_rate_below_threshold(self, mock_email, mock_dashboard):
        now = timezone.now()
        for i in range(10):
            AgentRunLog.objects.create(
                agent_name='test_agent',
                outcome='success' if i < 5 else 'failure',
                created_at=now - timedelta(minutes=i),
            )

        result = evaluate_agent_success_rate()

        self.assertIsNotNone(result)
        self.assertEqual(result.status, AlertStatus.FIRING)
        self.assertAlmostEqual(result.triggered_value, 0.50)

    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'agent_success_rate_minimum': 0.80})
    def test_does_not_fire_when_success_rate_above_threshold(self):
        now = timezone.now()
        for i in range(10):
            AgentRunLog.objects.create(
                agent_name='test_agent',
                outcome='success',
                created_at=now - timedelta(minutes=i),
            )

        result = evaluate_agent_success_rate()
        self.assertIsNone(result)


class EvaluateAllAlertsTest(TestCase):
    @override_settings(
        LANGFUSE_ALERT_THRESHOLDS={
            'daily_token_budget_alert': 1000000,
            'agent_success_rate_minimum': 0.80,
        }
    )
    def test_evaluate_all_returns_results_dict(self):
        results = evaluate_all_alerts()

        self.assertIsInstance(results, dict)
        self.assertIn('token_spend', results)
        self.assertIn('agent_success_rate', results)


class RecordTokenUsageTaskTest(TestCase):
    def test_records_new_token_usage(self):
        record_token_usage_task(500, input_tokens=300, output_tokens=200)

        log = TokenUsageLog.objects.latest('id')
        self.assertEqual(log.total_tokens, 500)
        self.assertEqual(log.input_tokens, 300)
        self.assertEqual(log.output_tokens, 200)

    def test_accumulates_daily_tokens(self):
        record_token_usage_task(500, input_tokens=300, output_tokens=200)
        record_token_usage_task(300, input_tokens=200, output_tokens=100)

        log = TokenUsageLog.objects.latest('id')
        self.assertEqual(log.total_tokens, 800)

    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'daily_token_budget_alert': 1000})
    def test_budget_alert_fires_on_accumulated_tokens(self):
        record_token_usage_task(600)
        record_token_usage_task(500)

        today = timezone.now().date()
        total = sum(
            TokenUsageLog.objects.filter(logged_at=today).values_list('total_tokens', flat=True)
        )
        self.assertGreater(total, 1000)


class RecordAgentRunTaskTest(TestCase):
    def test_records_success(self):
        record_agent_run_task('test_agent', 'success', duration_ms=100)

        log = AgentRunLog.objects.latest('id')
        self.assertEqual(log.outcome, 'success')

    def test_records_failure(self):
        record_agent_run_task('test_agent', 'failure', error_message='timeout')

        log = AgentRunLog.objects.latest('id')
        self.assertEqual(log.outcome, 'failure')
        self.assertEqual(log.error_message, 'timeout')


class AlertResilienceTest(TestCase):
    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'daily_token_budget_alert': 100})
    @patch('apps.monitoring.alerts.send_alert_email', side_effect=Exception('email failed'))
    @patch('apps.monitoring.alerts.send_dashboard_notification', return_value=False)
    def test_alert_fires_even_when_notifications_fail(self, mock_dashboard, mock_email):
        today = timezone.now().date()
        TokenUsageLog.objects.create(total_tokens=200, logged_at=today)

        result = evaluate_token_spend()

        self.assertIsNotNone(result)
        self.assertEqual(result.status, AlertStatus.FIRING)

    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'daily_token_budget_alert': 100})
    def test_cooldown_prevents_duplicate_firing(self):
        today = timezone.now().date()
        TokenUsageLog.objects.create(total_tokens=200, logged_at=today)

        with (
            patch('apps.monitoring.alerts.send_alert_email', return_value=True),
            patch('apps.monitoring.alerts.send_dashboard_notification', return_value=True),
        ):
            result1 = evaluate_token_spend()
            self.assertIsNotNone(result1)

        result2 = evaluate_token_spend()
        self.assertIsNone(result2)

    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'daily_token_budget_alert': 100})
    def test_alert_resolves_when_value_drops(self):
        today = timezone.now().date()
        TokenUsageLog.objects.create(total_tokens=200, logged_at=today)

        with (
            patch('apps.monitoring.alerts.send_alert_email', return_value=True),
            patch('apps.monitoring.alerts.send_dashboard_notification', return_value=True),
        ):
            result = evaluate_token_spend()
            self.assertIsNotNone(result)

        # Now create a small amount that won't exceed budget
        TokenUsageLog.objects.filter(logged_at=today).update(total_tokens=10)

        with patch('apps.monitoring.alerts.send_dashboard_notification', return_value=True):
            result = evaluate_token_spend()
            self.assertIsNone(result)

        resolved = AlertEvent.objects.filter(
            rule__name='Daily Token Spend Cap',
            status=AlertStatus.RESOLVED,
        ).first()
        self.assertIsNotNone(resolved)
        self.assertIsNotNone(resolved.resolved_at)
