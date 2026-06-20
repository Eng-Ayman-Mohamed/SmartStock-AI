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
    @patch('apps.forecasting.tasks.cache')
    @patch('apps.forecasting.services.ForecastingService')
    def test_success(self, MockService, mock_cache):
        mock_service = MockService.return_value
        mock_service.run_forecast.return_value = [{'sku': 'SKU001'}]

        from apps.forecasting.tasks import run_forecast_single_sku

        result = run_forecast_single_sku(sku_id=1)
        self.assertEqual(result['status'], 'success')

    @patch('apps.forecasting.tasks.cache')
    @patch('apps.forecasting.services.ForecastingService')
    def test_failure(self, MockService, mock_cache):
        mock_service = MockService.return_value
        mock_service.run_forecast.side_effect = Exception('prophet fail')

        from apps.forecasting.tasks import run_forecast_single_sku

        result = run_forecast_single_sku(sku_id=1)
        self.assertEqual(result['status'], 'failed')

    @patch('apps.forecasting.tasks.cache')
    @patch('apps.forecasting.services.ForecastingService')
    def test_cache_invalidation(self, MockService, mock_cache):
        mock_service = MockService.return_value
        mock_service.run_forecast.return_value = [{'sku': 'SKU001', 'other': 'data'}]
        mock_cache.delete_pattern.side_effect = Exception('cache fail')

        from apps.forecasting.tasks import run_forecast_single_sku

        result = run_forecast_single_sku(sku_id=1)
        self.assertEqual(result['status'], 'success')
