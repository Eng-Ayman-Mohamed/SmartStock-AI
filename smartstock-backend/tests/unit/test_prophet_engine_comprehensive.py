import math
import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from apps.forecasting.prophet_engine import (
    MIN_DATA_POINTS,
    ProphetEngine,
    _compute_accuracy,
    _moving_average_forecast,
)


def _make_df(values, start='2025-01-01'):
    return pd.DataFrame(
        {
            'ds': pd.date_range(start, periods=len(values)),
            'y': [float(v) for v in values],
        }
    )


class TestMovingAverageForecastEdgeCases(unittest.TestCase):
    def test_single_value_constant(self):
        df = _make_df([42.0])
        result = _moving_average_forecast(df, periods=5)
        self.assertEqual(len(result), 5)
        self.assertTrue((result['yhat'] == 42.0).all())

    def test_window_size_capped_at_7(self):
        df = _make_df([10.0] * 100)
        result = _moving_average_forecast(df, periods=3)
        self.assertAlmostEqual(result['yhat'].iloc[0], 10.0)

    def test_window_size_small_dataset(self):
        df = _make_df([20.0] * 3)
        result = _moving_average_forecast(df, periods=2)
        self.assertEqual(len(result), 2)
        self.assertTrue((result['yhat'] == 20.0).all())

    def test_bounds_are_symmetric(self):
        df = _make_df([100.0] * 14)
        result = _moving_average_forecast(df, periods=5)
        for _, row in result.iterrows():
            self.assertAlmostEqual(row['yhat_lower'], row['yhat'] * 0.8)
            self.assertAlmostEqual(row['yhat_upper'], row['yhat'] * 1.2)

    def test_periods_1(self):
        df = _make_df([50.0] * 14)
        result = _moving_average_forecast(df, periods=1)
        self.assertEqual(len(result), 1)

    def test_periods_365(self):
        df = _make_df([50.0] * 14)
        result = _moving_average_forecast(df, periods=365)
        self.assertEqual(len(result), 365)

    def test_nan_values_in_series(self):
        values = [10.0, float('nan'), 20.0, 30.0, 40.0]
        df = _make_df(values)
        result = _moving_average_forecast(df, periods=3)
        self.assertEqual(len(result), 3)
        self.assertFalse(result['yhat'].isna().any())

    def test_dates_are_consecutive(self):
        df = _make_df([10.0] * 14)
        result = _moving_average_forecast(df, periods=5)
        for i in range(1, len(result)):
            diff = (result['ds'].iloc[i] - result['ds'].iloc[i - 1]).days
            self.assertEqual(diff, 1)


class TestComputeAccuracyEdgeCases(unittest.TestCase):
    def test_perfect_prediction(self):
        df = pd.DataFrame({'ds': pd.date_range('2025-01-01', periods=50), 'y': [100.0] * 50})
        model = MagicMock()
        model.predict.return_value = pd.DataFrame({'yhat': [100.0] * 50})
        mae, mape = _compute_accuracy(df, model)
        self.assertAlmostEqual(mae, 0.0)
        self.assertAlmostEqual(mape, 0.0)

    def test_known_error_values(self):
        y_true = np.array([100.0, 200.0, 300.0])
        y_pred = np.array([110.0, 180.0, 330.0])
        df = pd.DataFrame({'ds': pd.date_range('2025-01-01', periods=3), 'y': y_true})
        model = MagicMock()
        model.predict.return_value = pd.DataFrame({'yhat': y_pred})
        mae, mape = _compute_accuracy(df, model)
        expected_mae = float(np.mean(np.abs(y_true - y_pred)))
        self.assertAlmostEqual(mae, expected_mae, places=5)

    def test_all_zeros_returns_inf_mape(self):
        df = pd.DataFrame({'ds': pd.date_range('2025-01-01', periods=5), 'y': [0.0] * 5})
        model = MagicMock()
        model.predict.return_value = pd.DataFrame({'yhat': [5.0] * 5})
        mae, mape = _compute_accuracy(df, model)
        self.assertIsNotNone(mae)
        self.assertEqual(mape, float('inf'))


class TestProphetEngineErrorHandling(unittest.TestCase):
    def setUp(self):
        self.engine = ProphetEngine()

    @patch('prophet.Prophet')
    def test_prophet_fit_failure_falls_back(self, mock_prophet_class):
        instance = mock_prophet_class.return_value
        instance.fit.side_effect = Exception('fit failed')
        df = _make_df([50.0] * 60)
        result = self.engine.predict(df, periods=30)
        self.assertEqual(result['model_version'], 'moving_average_fallback')

    @patch('prophet.Prophet')
    def test_prophet_refit_failure_uses_original(self, mock_prophet_class):
        call_count = [0]

        def side_effect_fit(df_train):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception('refit failed')
            return None

        instance = mock_prophet_class.return_value
        instance.fit.side_effect = side_effect_fit

        def mock_future(*args, **kwargs):
            periods = kwargs.get('periods', args[1] if len(args) > 1 else 30)
            return pd.DataFrame({'ds': pd.date_range('2025-06-01', periods=periods)})

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
        df = _make_df([50.0] * 60)
        result = self.engine.predict(df, periods=10)
        self.assertEqual(result['model_version'], 'prophet_1.1')

    def test_dataset_exactly_at_minimum(self):
        df = _make_df([50.0] * MIN_DATA_POINTS)
        result = self.engine.predict(df, periods=30)
        self.assertIn(result['model_version'], ['prophet_1.1', 'moving_average_fallback'])

    def test_unsorted_df_is_sorted(self):
        rng = np.random.RandomState(99)
        values = list(range(60))
        shuffled = rng.permutation(values)
        dates = pd.date_range('2025-01-01', periods=60)
        ds_shuffled = dates[shuffled]
        df = pd.DataFrame({'ds': ds_shuffled, 'y': [float(v) for v in values]})
        result = self.engine.predict(df, periods=5)
        self.assertEqual(len(result['results']), 5)

    def test_fallback_dates_are_after_last_data(self):
        df = _make_df([10.0] * 10, start='2025-06-01')
        result = self.engine.predict(df, periods=5)
        last_date = df['ds'].max().date()
        for r in result['results']:
            forecast_date = pd.Timestamp(r['forecast_date']).date()
            self.assertGreater(forecast_date, last_date)


class TestHoldoutEvaluation(unittest.TestCase):
    def setUp(self):
        self.engine = ProphetEngine()

    def _train_test_split(self, df, train_ratio=0.8):
        split_idx = int(len(df) * train_ratio)
        return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()

    def _make_seeded_df(self, n_days, base=50, noise_std=5, seed=42):
        rng = np.random.RandomState(seed)
        dates = pd.date_range('2025-01-01', periods=n_days)
        y = base + rng.randn(n_days) * noise_std
        y = np.maximum(y, 0)
        return pd.DataFrame({'ds': dates, 'y': y})

    def test_holdout_mae_is_finite(self):
        df = self._make_seeded_df(100)
        train, test = self._train_test_split(df)
        result = self.engine.predict(train, periods=len(test))
        predicted = [r['predicted_quantity'] for r in result['results']]
        mae = float(np.mean(np.abs(test['y'].values[: len(predicted)] - np.array(predicted))))
        self.assertTrue(math.isfinite(mae))
        self.assertGreaterEqual(mae, 0)

    def test_holdout_mape_is_finite(self):
        df = self._make_seeded_df(100, base=50)
        train, test = self._train_test_split(df)
        result = self.engine.predict(train, periods=len(test))
        predicted = [r['predicted_quantity'] for r in result['results']]
        actual = test['y'].values[: len(predicted)]
        nonzero = actual > 0
        if nonzero.sum() > 0:
            mape = float(
                np.mean(np.abs((actual[nonzero] - np.array(predicted)[nonzero]) / actual[nonzero]))
            )
            self.assertTrue(math.isfinite(mape))

    def test_holdout_no_nan_in_results(self):
        df = self._make_seeded_df(80, base=100, noise_std=10)
        train, test = self._train_test_split(df)
        result = self.engine.predict(train, periods=len(test))
        for r in result['results']:
            self.assertFalse(math.isnan(r['predicted_quantity']))
            self.assertFalse(math.isnan(r['lower_bound']))
            self.assertFalse(math.isnan(r['upper_bound']))

    def test_holdout_forecast_horizon_correct(self):
        df = self._make_seeded_df(60)
        train, test = self._train_test_split(df)
        horizon = len(test)
        result = self.engine.predict(train, periods=horizon)
        self.assertEqual(len(result['results']), horizon)

    def test_reproducibility_same_data(self):
        df = self._make_seeded_df(60)
        result1 = self.engine.predict(df.copy(), periods=30)
        result2 = self.engine.predict(df.copy(), periods=30)
        dates1 = [r['forecast_date'] for r in result1['results']]
        dates2 = [r['forecast_date'] for r in result2['results']]
        self.assertEqual(dates1, dates2)


if __name__ == '__main__':
    unittest.main()
