import unittest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

import pandas as pd
import numpy as np


class TestFillMissingDates(unittest.TestCase):
    def setUp(self):
        from apps.forecasting.ingestion import fill_missing_dates
        self.fill_missing_dates = fill_missing_dates

    def test_fills_single_gap(self):
        df = pd.DataFrame({
            'ds': pd.to_datetime(['2025-01-01', '2025-01-03', '2025-01-05']),
            'y': [10.0, 20.0, 30.0],
        })
        result = self.fill_missing_dates(df)
        self.assertEqual(len(result), 5)
        self.assertEqual(result['y'].iloc[1], 0.0)

    def test_continuous_date_range(self):
        df = pd.DataFrame({
            'ds': pd.to_datetime(['2025-01-01', '2025-01-10']),
            'y': [5.0, 15.0],
        })
        result = self.fill_missing_dates(df)
        self.assertEqual(len(result), 10)
        expected_dates = pd.date_range(start='2025-01-01', end='2025-01-10', freq='D')
        pd.testing.assert_series_equal(
            result['ds'].reset_index(drop=True),
            pd.Series(expected_dates),
            check_names=False,
        )

    def test_empty_df_passes_through(self):
        df = pd.DataFrame({'ds': pd.Series(dtype='datetime64[ns]'), 'y': pd.Series(dtype='float64')})
        result = self.fill_missing_dates(df)
        self.assertTrue(result.empty)

    def test_no_missing_dates(self):
        df = pd.DataFrame({
            'ds': pd.to_datetime(['2025-01-01', '2025-01-02', '2025-01-03']),
            'y': [1.0, 2.0, 3.0],
        })
        result = self.fill_missing_dates(df)
        self.assertEqual(len(result), 3)
        pd.testing.assert_series_equal(result['y'], df['y'], check_names=False)


class TestCapOutliers(unittest.TestCase):
    def setUp(self):
        from apps.forecasting.ingestion import cap_outliers
        self.cap_outliers = cap_outliers

    def test_outlier_capped_at_upper_bound(self):
        normal_data = [10.0] * 20 + [1000.0]
        df = pd.DataFrame({
            'ds': pd.date_range('2025-01-01', periods=len(normal_data)),
            'y': normal_data,
        })
        result = self.cap_outliers(df, sigma=3.0)
        original_max = max(normal_data)
        result_max = result['y'].max()
        self.assertLess(result_max, original_max)

    def test_lower_values_not_capped(self):
        df = pd.DataFrame({
            'ds': pd.date_range('2025-01-01', periods=10),
            'y': [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0],
        })
        result = self.cap_outliers(df, sigma=3.0)
        pd.testing.assert_series_equal(result['y'], df['y'], check_names=False)

    def test_empty_df_passes_through(self):
        df = pd.DataFrame({'ds': pd.Series(dtype='datetime64[ns]'), 'y': pd.Series(dtype='float64')})
        result = self.cap_outliers(df)
        self.assertTrue(result.empty)

    def test_all_same_values_no_change(self):
        df = pd.DataFrame({
            'ds': pd.date_range('2025-01-01', periods=10),
            'y': [50.0] * 10,
        })
        result = self.cap_outliers(df, sigma=3.0)
        pd.testing.assert_series_equal(result['y'], df['y'], check_names=False)

    def test_multiple_outliers_capped(self):
        values = [10.0] * 18 + [500.0, 600.0]
        df = pd.DataFrame({
            'ds': pd.date_range('2025-01-01', periods=len(values)),
            'y': values,
        })
        result = self.cap_outliers(df, sigma=3.0)
        for val in result['y']:
            self.assertLessEqual(val, 600.0)


class TestValidateMinimumData(unittest.TestCase):
    def setUp(self):
        from apps.forecasting.ingestion import validate_minimum_data
        self.validate_minimum_data = validate_minimum_data

    def test_passes_with_enough_records(self):
        df = pd.DataFrame({
            'ds': pd.date_range('2025-01-01', periods=30),
            'y': [10.0] * 30,
        })
        self.assertTrue(self.validate_minimum_data(df))

    def test_fails_with_too_few_records(self):
        df = pd.DataFrame({
            'ds': pd.date_range('2025-01-01', periods=29),
            'y': [10.0] * 29,
        })
        self.assertFalse(self.validate_minimum_data(df))

    def test_exact_threshold_passes(self):
        df = pd.DataFrame({
            'ds': pd.date_range('2025-01-01', periods=30),
            'y': [10.0] * 30,
        })
        self.assertTrue(self.validate_minimum_data(df, min_records=30))

    def test_empty_df_fails(self):
        df = pd.DataFrame({'ds': pd.Series(dtype='datetime64[ns]'), 'y': pd.Series(dtype='float64')})
        self.assertFalse(self.validate_minimum_data(df))


class TestLogInsufficientData(unittest.TestCase):
    def setUp(self):
        from apps.forecasting.ingestion import _log_insufficient_data
        self._log_insufficient_data = _log_insufficient_data

    @patch('apps.forecasting.ingestion.logger')
    def test_logs_structured_json(self, mock_logger):
        self._log_insufficient_data('SKU-001', 15)
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        extra = call_args[1]['extra']
        self.assertEqual(extra['event'], 'INSUFFICIENT_FORECAST_DATA')
        self.assertEqual(extra['sku_code'], 'SKU-001')
        self.assertEqual(extra['record_count'], 15)
        self.assertEqual(extra['threshold'], 30)
        self.assertEqual(extra['action'], 'fallback_to_moving_average')


class TestFetchSalesData(unittest.TestCase):
    def setUp(self):
        from apps.forecasting.ingestion import fetch_sales_data
        self.fetch_sales_data = fetch_sales_data

    @patch('apps.forecasting.ingestion._get_repo')
    def test_returns_dataframe_with_ds_y_columns(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        mock_sales = [
            MagicMock(date=date(2025, 1, 1), quantity_sold=10),
            MagicMock(date=date(2025, 1, 2), quantity_sold=20),
        ]
        mock_repo.get_sales_for_sku.return_value = mock_sales

        result = self.fetch_sales_data(1)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertListEqual(list(result.columns), ['ds', 'y'])
        self.assertEqual(len(result), 2)
        self.assertEqual(result['y'].iloc[0], 10.0)
        self.assertEqual(result['y'].iloc[1], 20.0)

    @patch('apps.forecasting.ingestion._get_repo')
    def test_sorted_by_date(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        mock_sales = [
            MagicMock(date=date(2025, 1, 3), quantity_sold=30),
            MagicMock(date=date(2025, 1, 1), quantity_sold=10),
            MagicMock(date=date(2025, 1, 2), quantity_sold=20),
        ]
        mock_repo.get_sales_for_sku.return_value = mock_sales

        result = self.fetch_sales_data(1)

        self.assertEqual(result['ds'].iloc[0], pd.Timestamp('2025-01-01'))
        self.assertEqual(result['ds'].iloc[1], pd.Timestamp('2025-01-02'))
        self.assertEqual(result['ds'].iloc[2], pd.Timestamp('2025-01-03'))

    @patch('apps.forecasting.ingestion._get_repo')
    def test_empty_sales_returns_empty_df(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        mock_repo.get_sales_for_sku.return_value = []

        result = self.fetch_sales_data(1)
        self.assertTrue(result.empty)


class TestPrepareForecastDataframe(unittest.TestCase):
    def setUp(self):
        from apps.forecasting.ingestion import prepare_forecast_dataframe
        self.prepare_forecast_dataframe = prepare_forecast_dataframe

    @patch('apps.forecasting.ingestion._get_repo')
    def test_returns_cleaned_dataframe_for_valid_sku(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo

        mock_sku = MagicMock()
        mock_sku.id = 1
        mock_sku.code = 'TEST-SKU'
        mock_repo.get_sku.return_value = mock_sku

        base = date.today() - timedelta(days=60)
        mock_sales = [
            MagicMock(date=base + timedelta(days=i), quantity_sold=10 + (i % 5))
            for i in range(60)
        ]
        mock_repo.get_sales_for_sku.return_value = mock_sales

        result = self.prepare_forecast_dataframe(1)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertListEqual(list(result.columns), ['ds', 'y'])
        self.assertGreaterEqual(len(result), 30)

    @patch('apps.forecasting.ingestion._get_repo')
    def test_returns_none_for_insufficient_data(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo

        mock_sku = MagicMock()
        mock_sku.id = 2
        mock_sku.code = 'SHORT-SKU'
        mock_repo.get_sku.return_value = mock_sku

        base = date.today() - timedelta(days=20)
        mock_sales = [
            MagicMock(date=base + timedelta(days=i), quantity_sold=10)
            for i in range(20)
        ]
        mock_repo.get_sales_for_sku.return_value = mock_sales

        result = self.prepare_forecast_dataframe(2)
        self.assertIsNone(result)

    @patch('apps.forecasting.ingestion._get_repo')
    def test_returns_none_for_no_data(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo

        mock_sku = MagicMock()
        mock_sku.id = 3
        mock_sku.code = 'EMPTY-SKU'
        mock_repo.get_sku.return_value = mock_sku
        mock_repo.get_sales_for_sku.return_value = []

        result = self.prepare_forecast_dataframe(3)
        self.assertIsNone(result)


class TestPrepareAllForecastData(unittest.TestCase):
    def setUp(self):
        from apps.forecasting.ingestion import prepare_all_forecast_data
        self.prepare_all_forecast_data = prepare_all_forecast_data

    @patch('apps.forecasting.ingestion._get_repo')
    def test_returns_tuple_of_dict_and_list(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        mock_repo.get_sales_for_all_skus.return_value = {}

        dataframes, excluded = self.prepare_all_forecast_data()

        self.assertIsInstance(dataframes, dict)
        self.assertIsInstance(excluded, list)

    @patch('apps.forecasting.ingestion._get_repo')
    def test_valid_sku_appears_in_dataframes(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo

        base = date.today() - timedelta(days=60)
        mock_sales = [
            MagicMock(date=base + timedelta(days=i), quantity_sold=10)
            for i in range(60)
        ]

        mock_repo.get_sales_for_all_skus.return_value = {
            'GOOD-SKU': mock_sales,
        }

        dataframes, excluded = self.prepare_all_forecast_data()

        self.assertIn('GOOD-SKU', dataframes)
        self.assertIsInstance(dataframes['GOOD-SKU'], pd.DataFrame)
        self.assertNotIn('GOOD-SKU', excluded)

    @patch('apps.forecasting.ingestion._get_repo')
    def test_insufficient_sku_appears_in_excluded(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo

        base = date.today() - timedelta(days=10)
        mock_sales = [
            MagicMock(date=base + timedelta(days=i), quantity_sold=10)
            for i in range(10)
        ]

        mock_repo.get_sales_for_all_skus.return_value = {
            'SHORT-SKU': mock_sales,
        }

        dataframes, excluded = self.prepare_all_forecast_data()

        self.assertNotIn('SHORT-SKU', dataframes)
        self.assertIn('SHORT-SKU', excluded)

    @patch('apps.forecasting.ingestion._get_repo')
    def test_empty_sku_appears_in_excluded(self, mock_get_repo):
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo

        mock_repo.get_sales_for_all_skus.return_value = {
            'EMPTY-SKU': [],
        }

        dataframes, excluded = self.prepare_all_forecast_data()

        self.assertNotIn('EMPTY-SKU', dataframes)
        self.assertIn('EMPTY-SKU', excluded)


if __name__ == '__main__':
    unittest.main()
