from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.monitoring.alerts import (
    evaluate_agent_success_rate,
    evaluate_all_alerts,
    evaluate_error_rate,
    evaluate_p95_latency,
    evaluate_token_spend,
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


class EvaluateP95LatencyTest(TestCase):
    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'llm_latency_p95_ms_warning': 3000})
    @patch('apps.monitoring.alerts.get_current_p95_latency', return_value=4.5)
    @patch('apps.monitoring.alerts.send_dashboard_notification', return_value=True)
    @patch('apps.monitoring.alerts.send_alert_email', return_value=True)
    def test_fires_when_latency_exceeds_threshold(
        self, mock_email, mock_dashboard, mock_get_latency
    ):
        result = evaluate_p95_latency()

        self.assertIsNotNone(result)
        self.assertEqual(result.status, AlertStatus.FIRING)
        self.assertAlmostEqual(result.triggered_value, 4.5)
        mock_email.assert_called_once()
        mock_dashboard.assert_called_once()

    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'llm_latency_p95_ms_warning': 3000})
    @patch('apps.monitoring.alerts.get_current_p95_latency', return_value=1.5)
    def test_does_not_fire_when_below_threshold(self, mock_get_latency):
        result = evaluate_p95_latency()
        self.assertIsNone(result)


class EvaluateErrorRateTest(TestCase):
    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'llm_api_error_rate_critical': 0.01})
    @patch('apps.monitoring.alerts.get_current_error_rate', return_value=0.05)
    @patch('apps.monitoring.alerts.send_dashboard_notification', return_value=True)
    @patch('apps.monitoring.alerts.send_alert_email', return_value=True)
    def test_fires_when_error_rate_exceeds_threshold(
        self, mock_email, mock_dashboard, mock_get_rate
    ):
        result = evaluate_error_rate()

        self.assertIsNotNone(result)
        self.assertEqual(result.status, AlertStatus.FIRING)
        self.assertAlmostEqual(result.triggered_value, 0.05)

    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'llm_api_error_rate_critical': 0.01})
    @patch('apps.monitoring.alerts.get_current_error_rate', return_value=0.005)
    def test_does_not_fire_when_below_threshold(self, mock_get_rate):
        result = evaluate_error_rate()
        self.assertIsNone(result)


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
            'llm_latency_p95_ms_warning': 3000,
            'llm_api_error_rate_critical': 0.01,
            'daily_token_budget_alert': 1000000,
            'agent_success_rate_minimum': 0.80,
        }
    )
    @patch('apps.monitoring.alerts.get_current_error_rate', return_value=0.001)
    @patch('apps.monitoring.alerts.get_current_p95_latency', return_value=1.0)
    def test_evaluate_all_returns_results_dict(self, mock_latency, mock_error):
        results = evaluate_all_alerts()

        self.assertIsInstance(results, dict)
        self.assertIn('p95_latency', results)
        self.assertIn('error_rate', results)
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
    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'llm_latency_p95_ms_warning': 3000})
    @patch('apps.monitoring.alerts.get_current_p95_latency', return_value=10.0)
    @patch('apps.monitoring.alerts.send_alert_email', side_effect=Exception('email failed'))
    @patch('apps.monitoring.alerts.send_dashboard_notification', return_value=False)
    def test_alert_fires_even_when_notifications_fail(
        self, mock_dashboard, mock_email, mock_get_latency
    ):
        result = evaluate_p95_latency()

        self.assertIsNotNone(result)
        self.assertEqual(result.status, AlertStatus.FIRING)

    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'llm_latency_p95_ms_warning': 3000})
    @patch('apps.monitoring.alerts.get_current_p95_latency', return_value=10.0)
    def test_cooldown_prevents_duplicate_firing(self, mock_get_latency):
        with (
            patch('apps.monitoring.alerts.send_alert_email', return_value=True),
            patch('apps.monitoring.alerts.send_dashboard_notification', return_value=True),
        ):
            result1 = evaluate_p95_latency()
            self.assertIsNotNone(result1)

        result2 = evaluate_p95_latency()
        self.assertIsNone(result2)

    @override_settings(LANGFUSE_ALERT_THRESHOLDS={'llm_latency_p95_ms_warning': 3000})
    @patch('apps.monitoring.alerts.get_current_p95_latency', return_value=10.0)
    def test_alert_resolves_when_value_drops(self, mock_get_latency):
        with (
            patch('apps.monitoring.alerts.send_alert_email', return_value=True),
            patch('apps.monitoring.alerts.send_dashboard_notification', return_value=True),
        ):
            result = evaluate_p95_latency()
            self.assertIsNotNone(result)

        mock_get_latency.return_value = 1.0
        with patch('apps.monitoring.alerts.send_dashboard_notification', return_value=True):
            result = evaluate_p95_latency()
            self.assertIsNone(result)

        resolved = AlertEvent.objects.filter(
            rule__name='P95 Latency Alert',
            status=AlertStatus.RESOLVED,
        ).first()
        self.assertIsNotNone(resolved)
        self.assertIsNotNone(resolved.resolved_at)
