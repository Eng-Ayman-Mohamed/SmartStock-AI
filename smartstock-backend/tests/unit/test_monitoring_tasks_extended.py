"""Tests for monitoring/tasks.py — Celery task happy paths."""

from unittest.mock import patch

from django.test import TestCase

from apps.monitoring.models import AgentRunLog, TokenUsageLog


class EvaluateAllAlertsTaskTest(TestCase):
    @patch('apps.monitoring.alerts.evaluate_all_alerts')
    def test_success(self, mock_eval):
        mock_eval.return_value = [{'rule': 'low_stock', 'fired': 2}]
        from apps.monitoring.tasks import evaluate_all_alerts_task

        result = evaluate_all_alerts_task.run()
        self.assertEqual(result, [{'rule': 'low_stock', 'fired': 2}])


class RecordTokenUsageTaskTest(TestCase):
    @patch('apps.monitoring.metrics.DAILY_TOKEN_USAGE')
    @patch('apps.monitoring.metrics.TOKEN_USAGE_TOTAL')
    def test_first_record_creates(self, mock_total, mock_daily):
        from apps.monitoring.tasks import record_token_usage_task

        record_token_usage_task.run(total_tokens=100, input_tokens=60, output_tokens=40)
        self.assertTrue(TokenUsageLog.objects.exists())
        log = TokenUsageLog.objects.first()
        self.assertEqual(log.total_tokens, 100)

    @patch('apps.monitoring.metrics.DAILY_TOKEN_USAGE')
    @patch('apps.monitoring.metrics.TOKEN_USAGE_TOTAL')
    def test_second_record_updates(self, mock_total, mock_daily):
        TokenUsageLog.objects.create(total_tokens=50, input_tokens=30, output_tokens=20)
        from apps.monitoring.tasks import record_token_usage_task

        record_token_usage_task.run(total_tokens=30, input_tokens=10, output_tokens=20)
        log = TokenUsageLog.objects.first()
        log.refresh_from_db()
        self.assertEqual(log.total_tokens, 80)


class RecordAgentRunTaskTest(TestCase):
    @patch('apps.monitoring.metrics.AGENT_RUN_TOTAL')
    def test_success(self, mock_metric):
        from apps.monitoring.tasks import record_agent_run_task

        record_agent_run_task.run(
            agent_name='rag_agent', outcome='success', duration_ms=150, error_message=''
        )
        self.assertEqual(AgentRunLog.objects.count(), 1)
        log = AgentRunLog.objects.first()
        self.assertEqual(log.agent_name, 'rag_agent')
