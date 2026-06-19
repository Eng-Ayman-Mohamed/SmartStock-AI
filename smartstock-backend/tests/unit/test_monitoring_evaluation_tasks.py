from unittest.mock import patch

from django.test import TestCase


class RunDailyEvaluationTaskTest(TestCase):
    @patch('apps.monitoring.metrics.EVALUATION_TIMESTAMP_GAUGE')
    @patch('apps.monitoring.metrics.EVALUATION_FAITHFULNESS_GAUGE')
    @patch('apps.monitoring.metrics.EVALUATION_PRECISION_GAUGE')
    @patch('ai.evaluation.metrics.log_scores_to_langfuse')
    @patch('ai.evaluation.metrics.evaluate_golden_dataset')
    def test_success_path(
        self,
        mock_evaluate,
        mock_langfuse,
        mock_precision,
        mock_faithfulness,
        mock_timestamp,
    ):
        mock_evaluate.return_value = {
            'precision_at_5': 0.85,
            'faithfulness': 0.90,
            'total_queries': 30,
            'successful_queries': 25,
        }

        from apps.monitoring.evaluation_tasks import run_daily_evaluation_task

        result = run_daily_evaluation_task()

        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['precision_at_5'], 0.85)
        self.assertEqual(result['faithfulness'], 0.90)
        self.assertEqual(result['total_queries'], 30)
        mock_precision.set.assert_called_once_with(0.85)
        mock_faithfulness.set.assert_called_once_with(0.90)
        mock_timestamp.set.assert_called_once()
        mock_langfuse.assert_called_once()

    @patch('apps.monitoring.metrics.EVALUATION_TIMESTAMP_GAUGE')
    @patch('apps.monitoring.metrics.EVALUATION_FAITHFULNESS_GAUGE')
    @patch('apps.monitoring.metrics.EVALUATION_PRECISION_GAUGE')
    @patch('ai.evaluation.metrics.log_scores_to_langfuse')
    @patch('ai.evaluation.metrics.evaluate_golden_dataset')
    def test_success_with_zero_queries(
        self,
        mock_evaluate,
        mock_langfuse,
        mock_precision,
        mock_faithfulness,
        mock_timestamp,
    ):
        mock_evaluate.return_value = {
            'precision_at_5': 0.0,
            'faithfulness': 0.0,
            'total_queries': 0,
            'successful_queries': 0,
        }

        from apps.monitoring.evaluation_tasks import run_daily_evaluation_task

        result = run_daily_evaluation_task()
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['total_queries'], 0)
