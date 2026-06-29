"""Tests for apps/forecasting/tasks.py — Celery tasks."""

from unittest.mock import patch

from django.test import TestCase


class RunForecastingAgentTaskTest(TestCase):
    def test_no_sku_ids_queries_all(self):
        with patch('celery.group') as MockGroup, patch('apps.inventory.models.SKU') as MockSKU:
            MockSKU.objects.filter.return_value.values_list.return_value = [1, 2]
            mock_result = MockGroup.return_value.apply_async.return_value
            mock_result.id = 'group-123'

            from apps.forecasting.tasks import run_forecasting_agent

            result = run_forecasting_agent()
            self.assertEqual(result['dispatched'], 2)

    def test_empty_sku_ids_returns_zero(self):
        from apps.forecasting.tasks import run_forecasting_agent

        result = run_forecasting_agent(sku_ids=[])
        self.assertEqual(result['processed'], 0)
        self.assertEqual(result['skipped'], 0)
        self.assertEqual(result['failed'], 0)


class RunForecastSingleSkuTest(TestCase):
    @patch('apps.forecasting.services.ForecastingService')
    def test_success(self, MockService):
        mock_service = MockService.return_value
        mock_service.run_forecast.return_value = [{'sku': 'SKU001'}]

        from apps.forecasting.tasks import run_forecast_single_sku

        result = run_forecast_single_sku(sku_id=1)
        self.assertEqual(result['status'], 'success')

    @patch('apps.forecasting.services.ForecastingService')
    def test_failure(self, MockService):
        mock_service = MockService.return_value
        mock_service.run_forecast.side_effect = Exception('prophet fail')

        from apps.forecasting.tasks import run_forecast_single_sku

        result = run_forecast_single_sku(sku_id=1)
        self.assertEqual(result['status'], 'failed')

    @patch('django_redis.get_redis_connection')
    def test_cache_invalidation_does_not_crash(self, mock_get_redis):
        """Cache invalidation failure should not crash the task."""
        mock_conn = mock_get_redis.return_value
        mock_conn.delete_pattern.side_effect = Exception('redis fail')

        from apps.forecasting.tasks import run_forecasting_agent

        with patch('apps.forecasting.tasks.run_forecast_single_sku.s') as mock_single:
            mock_single.return_value = None
            with patch('celery.group') as MockGroup:
                mock_result = MockGroup.return_value.apply_async.return_value
                mock_result.id = 'g-1'
                result = run_forecasting_agent(sku_ids=[1])
                self.assertEqual(result['dispatched'], 1)
