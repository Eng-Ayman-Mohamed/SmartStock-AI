"""Tests for apps/monitoring/alerts.py — alert evaluation functions."""

from unittest.mock import patch

from django.test import TestCase

from apps.monitoring.models import AlertEvent, AlertRule, AlertSeverity, AlertStatus


class EvaluateTokenSpendTest(TestCase):
    def test_below_threshold_returns_none(self):
        from apps.monitoring.alerts import evaluate_token_spend

        result = evaluate_token_spend()
        self.assertIsNone(result)

    def test_disabled_rule_returns_none(self):
        rule, _ = AlertRule.objects.get_or_create(
            name='Daily Token Spend Cap',
            defaults={
                'severity': AlertSeverity.WARNING,
                'metric_name': 'ai_daily_token_usage',
                'threshold': 1_000_000,
                'evaluation_window_minutes': 60,
                'cooldown_minutes': 60,
            },
        )
        rule.enabled = False
        rule.save(update_fields=['enabled'])

        from apps.monitoring.alerts import evaluate_token_spend

        result = evaluate_token_spend()
        self.assertIsNone(result)


class EvaluateAgentSuccessRateTest(TestCase):
    def test_no_runs_gauge_set_to_one(self):
        from apps.monitoring.alerts import evaluate_agent_success_rate

        with patch('apps.monitoring.alerts.AGENT_SUCCESS_RATE_GAUGE') as mock_gauge:
            result = evaluate_agent_success_rate()
            mock_gauge.set.assert_called_with(1.0)
            self.assertIsNone(result)

    def test_fires_when_rate_below_threshold(self):

        from apps.monitoring.alerts import evaluate_agent_success_rate

        for _ in range(8):
            from apps.monitoring.models import AgentRunLog

            AgentRunLog.objects.create(agent_name='test', outcome='failure', duration_ms=100)
        for _ in range(2):
            AgentRunLog.objects.create(agent_name='test', outcome='success', duration_ms=100)

        result = evaluate_agent_success_rate()
        self.assertIsNotNone(result)
        self.assertEqual(result.status, AlertStatus.FIRING)

    def test_resolves_when_rate_recovers(self):

        from apps.monitoring.alerts import evaluate_agent_success_rate

        rule, _ = AlertRule.objects.get_or_create(
            name='Agent Success Rate Alert',
            defaults={
                'severity': AlertSeverity.CRITICAL,
                'metric_name': 'ai_agent_success_rate_current',
                'threshold': 0.80,
                'evaluation_window_minutes': 30,
                'cooldown_minutes': 15,
            },
        )
        from apps.monitoring.models import AgentRunLog

        AlertEvent.objects.create(
            rule=rule,
            status=AlertStatus.FIRING,
            triggered_value=0.5,
            message='low rate',
        )
        for _ in range(10):
            AgentRunLog.objects.create(agent_name='test', outcome='success', duration_ms=100)

        result = evaluate_agent_success_rate()
        self.assertIsNone(result)
        rule.refresh_from_db()


class EvaluateAllAlertsTest(TestCase):
    def test_runs_all_evaluators(self):
        from apps.monitoring.alerts import evaluate_all_alerts

        results = evaluate_all_alerts()
        self.assertIn('token_spend', results)
        self.assertIn('agent_success_rate', results)

    def test_evaluator_exception_recorded(self):
        from apps.monitoring.alerts import evaluate_all_alerts

        with patch(
            'apps.monitoring.alerts.evaluate_token_spend',
            side_effect=Exception('db error'),
        ):
            results = evaluate_all_alerts()
            self.assertIn('error:', results['token_spend'])


class FireAlertNotificationTest(TestCase):
    @patch('apps.monitoring.alerts.send_dashboard_notification')
    @patch('apps.monitoring.alerts.send_alert_email')
    def test_fires_and_saves_notifications(self, mock_email, mock_dash):
        mock_email.return_value = True
        mock_dash.return_value = True
        from apps.monitoring.alerts import _fire_alert

        rule, _ = AlertRule.objects.get_or_create(
            name='Test Fire',
            defaults={
                'severity': AlertSeverity.WARNING,
                'metric_name': 'test_metric',
                'threshold': 100,
                'evaluation_window_minutes': 60,
                'cooldown_minutes': 60,
            },
        )
        event = _fire_alert(rule, 150, 'test message')
        self.assertEqual(event.status, AlertStatus.FIRING)
        self.assertTrue(event.email_sent)
        self.assertTrue(event.dashboard_notified)

    @patch('apps.monitoring.alerts.send_alert_email', side_effect=Exception('smtp fail'))
    @patch('apps.monitoring.alerts.send_dashboard_notification', return_value=False)
    def test_notification_failure_still_creates_event(self, mock_dash, mock_email):
        from apps.monitoring.alerts import _fire_alert

        rule, _ = AlertRule.objects.get_or_create(
            name='Test Fire 2',
            defaults={
                'severity': AlertSeverity.CRITICAL,
                'metric_name': 'test_metric_2',
                'threshold': 100,
                'evaluation_window_minutes': 60,
                'cooldown_minutes': 60,
            },
        )
        event = _fire_alert(rule, 200, 'fired')
        self.assertFalse(event.email_sent)


class ResolveAlertTest(TestCase):
    @patch('apps.monitoring.alerts.send_dashboard_notification')
    def test_resolves_firing_event(self, mock_dash):
        from apps.monitoring.alerts import _resolve_if_was_firing

        rule, _ = AlertRule.objects.get_or_create(
            name='Test Resolve',
            defaults={
                'severity': AlertSeverity.WARNING,
                'metric_name': 'test_resolve',
                'threshold': 100,
                'evaluation_window_minutes': 60,
                'cooldown_minutes': 60,
            },
        )
        event = AlertEvent.objects.create(
            rule=rule,
            status=AlertStatus.FIRING,
            triggered_value=150,
            message='was firing',
        )
        _resolve_if_was_firing(rule, 50)
        event.refresh_from_db()
        self.assertEqual(event.status, AlertStatus.RESOLVED)
        self.assertIsNotNone(event.resolved_at)
