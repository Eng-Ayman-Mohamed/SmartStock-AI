import unittest
from unittest.mock import MagicMock, patch

import pandas as pd


class TestMovingAverageForecast(unittest.TestCase):
    def setUp(self):
        from apps.forecasting.prophet_engine import _moving_average_forecast

        self._moving_average_forecast = _moving_average_forecast

    def _make_df(self, values):
        return pd.DataFrame(
            {
                'ds': pd.date_range('2025-01-01', periods=len(values)),
                'y': values,
            }
        )

    def test_returns_30_forecast_rows(self):
        df = self._make_df([10] * 60)
        result = self._moving_average_forecast(df, periods=30)
        self.assertEqual(len(result), 30)

    def test_yhat_is_moving_average(self):
        df = self._make_df([100] * 14)
        result = self._moving_average_forecast(df, periods=5)
        self.assertTrue((result['yhat'] == 100).all())

    def test_yhat_clipped_at_zero(self):
        df = self._make_df([-5] * 14)
        result = self._moving_average_forecast(df, periods=5)
        self.assertTrue((result['yhat'] >= 0).all())
        self.assertTrue((result['yhat_lower'] >= 0).all())
        self.assertTrue((result['yhat_upper'] >= 0).all())

    def test_dates_continue_from_last(self):
        df = self._make_df([10] * 14)
        result = self._moving_average_forecast(df, periods=3)
        expected_start = df['ds'].max() + pd.Timedelta(days=1)
        self.assertEqual(result['ds'].iloc[0], expected_start)


class TestComputeAccuracy(unittest.TestCase):
    def setUp(self):
        from apps.forecasting.prophet_engine import _compute_accuracy

        self._compute_accuracy = _compute_accuracy

    def test_returns_mae_mape(self):
        df = pd.DataFrame(
            {
                'ds': pd.date_range('2025-01-01', periods=100),
                'y': [10.0] * 100,
            }
        )
        model = MagicMock()
        model.predict.return_value = pd.DataFrame({'yhat': [10.0] * 10})
        mae, mape = self._compute_accuracy(df, model)
        self.assertIsInstance(mae, float)
        self.assertIsInstance(mape, float)

    def test_returns_none_for_too_few_points(self):
        df = pd.DataFrame(
            {
                'ds': pd.date_range('2025-01-01', periods=1),
                'y': [10.0],
            }
        )
        model = MagicMock()
        mae, mape = self._compute_accuracy(df, model)
        self.assertIsNone(mae)
        self.assertIsNone(mape)


class TestProphetEngine(unittest.TestCase):
    def setUp(self):
        from apps.forecasting.prophet_engine import ProphetEngine

        self.engine = ProphetEngine()

    def _make_df(self, n_days, base_value=50):
        return pd.DataFrame(
            {
                'ds': pd.date_range('2025-01-01', periods=n_days),
                'y': [float(base_value)] * n_days,
            }
        )

    def test_fallback_with_few_points(self):
        df = self._make_df(10)
        result = self.engine.predict(df, periods=30)
        self.assertEqual(result['model_version'], 'moving_average_fallback')
        self.assertIsNone(result['mae'])
        self.assertIsNone(result['mape'])
        self.assertEqual(len(result['results']), 30)

    @patch('prophet.Prophet')
    def test_prophet_path_with_enough_points(self, mock_prophet):
        instance = mock_prophet.return_value
        instance.fit.return_value = None

        def mock_future(*args, **kwargs):
            periods = kwargs.get('periods', args[1] if len(args) > 1 else 30)
            return pd.DataFrame(
                {
                    'ds': pd.date_range('2025-04-01', periods=periods),
                }
            )

        instance.make_future_dataframe.side_effect = mock_future

        def mock_predict(df):
            return pd.DataFrame(
                {
                    'ds': df['ds'],
                    'yhat': [50.0] * len(df),
                    'yhat_lower': [40.0] * len(df),
                    'yhat_upper': [60.0] * len(df),
                }
            )

        instance.predict.side_effect = mock_predict

        df = self._make_df(60)
        result = self.engine.predict(df, periods=30)

        self.assertEqual(result['model_version'], 'prophet_1.1')
        self.assertEqual(len(result['results']), 30)
        mock_prophet.assert_called_once_with(
            weekly_seasonality=True,
            yearly_seasonality=len(df) >= 365,
            daily_seasonality=False,
        )

    @patch('prophet.Prophet')
    def test_results_clipped_at_zero(self, mock_prophet):
        instance = mock_prophet.return_value
        instance.fit.return_value = None

        def mock_future(*args, **kwargs):
            periods = kwargs.get('periods', args[1] if len(args) > 1 else 30)
            return pd.DataFrame(
                {
                    'ds': pd.date_range('2025-04-01', periods=periods),
                }
            )

        instance.make_future_dataframe.side_effect = mock_future

        def mock_predict(df):
            return pd.DataFrame(
                {
                    'ds': df['ds'],
                    'yhat': [-10.0] * len(df),
                    'yhat_lower': [-20.0] * len(df),
                    'yhat_upper': [-5.0] * len(df),
                }
            )

        instance.predict.side_effect = mock_predict

        df = self._make_df(60)
        result = self.engine.predict(df, periods=5)

        for r in result['results']:
            self.assertGreaterEqual(r['predicted_quantity'], 0)
            self.assertGreaterEqual(r['lower_bound'], 0)
            self.assertGreaterEqual(r['upper_bound'], 0)

    def test_import_error_fallback(self):
        real_import = __builtins__['__import__']

        def mock_import(name, *args, **kwargs):
            if name == 'prophet':
                raise ImportError('No prophet')
            return real_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mock_import):
            import importlib

            from apps.forecasting import prophet_engine

            importlib.reload(prophet_engine)
            engine = prophet_engine.ProphetEngine()
            df = self._make_df(60)
            result = engine.predict(df, periods=30)
            self.assertEqual(result['model_version'], 'moving_average_fallback')
            self.assertEqual(len(result['results']), 30)

    def test_empty_df_handling(self):
        df = pd.DataFrame({'ds': pd.Series(dtype='datetime64[ns]'), 'y': pd.Series(dtype='float64')})
        result = self.engine.predict(df, periods=30)
        self.assertEqual(result['model_version'], 'moving_average_fallback')
        self.assertEqual(len(result['results']), 30)
