from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
from django.test import TestCase

from apps.forecasting.prophet_engine import (
    ProphetEngine,
    _moving_average_forecast,
)


def _make_df(n: int) -> pd.DataFrame:
    """Create a deterministic time-series DataFrame with *n* rows."""
    rng = np.random.RandomState(42)
    dates = pd.date_range('2025-01-01', periods=n, freq='D')
    values = np.maximum(rng.normal(100, 20, n), 0)
    return pd.DataFrame({'ds': dates, 'y': values})


class ForecastMethodMetadataTest(TestCase):
    """Verify forecast_method is present in all responses."""

    def test_fallback_includes_forecast_method(self):
        df = _make_df(10)
        engine = ProphetEngine()
        result = engine.predict(df, periods=5)
        self.assertEqual(result['forecast_method'], 'moving_average')

    def test_schema_has_required_keys(self):
        """Fallback should return the same top-level keys as Prophet."""
        fallback = ProphetEngine().predict(_make_df(5), periods=3)
        fallback_keys = set(fallback.keys())
        self.assertIn('forecast_method', fallback_keys)
        self.assertIn('model_version', fallback_keys)
        self.assertIn('results', fallback_keys)
        self.assertIn('mae', fallback_keys)
        self.assertIn('mape', fallback_keys)


class ProphetFallbackDataPointThresholdTest(TestCase):
    """Test Prophet vs fallback decision based on data point count."""

    def test_5_points_fallback(self):
        df = _make_df(5)
        engine = ProphetEngine()
        result = engine.predict(df, periods=5)
        self.assertEqual(result['forecast_method'], 'moving_average')
        self.assertEqual(result['model_version'], 'moving_average_fallback')

    def test_10_points_fallback(self):
        df = _make_df(10)
        engine = ProphetEngine()
        result = engine.predict(df, periods=5)
        self.assertEqual(result['forecast_method'], 'moving_average')

    def test_20_points_fallback(self):
        df = _make_df(20)
        engine = ProphetEngine()
        result = engine.predict(df, periods=5)
        self.assertEqual(result['forecast_method'], 'moving_average')

    def test_29_points_fallback(self):
        df = _make_df(29)
        engine = ProphetEngine()
        result = engine.predict(df, periods=5)
        self.assertEqual(result['forecast_method'], 'moving_average')

    def test_30_points_tries_prophet(self):
        df = _make_df(30)
        engine = ProphetEngine()
        result = engine.predict(df, periods=5)
        # Prophet is not installed in test env, so it falls back
        self.assertIn(result['forecast_method'], ('prophet', 'moving_average'))

    def test_50_points_tries_prophet(self):
        df = _make_df(50)
        engine = ProphetEngine()
        result = engine.predict(df, periods=5)
        self.assertIn(result['forecast_method'], ('prophet', 'moving_average'))


class ProphetFallbackLoggedTest(TestCase):
    """Verify fallback logging behavior."""

    def test_fallback_logs_insufficient_data(self):
        df = _make_df(10)
        engine = ProphetEngine()
        with self.assertLogs('apps.forecasting.prophet_engine', level='INFO') as cm:
            engine.predict(df, periods=5)
        self.assertTrue(
            any('Fallback forecast used' in msg for msg in cm.output),
        )

    def test_fallback_logs_data_point_count(self):
        df = _make_df(15)
        engine = ProphetEngine()
        with self.assertLogs('apps.forecasting.prophet_engine', level='INFO') as cm:
            engine.predict(df, periods=5)
        self.assertTrue(any('15 data points' in msg for msg in cm.output))


class ProphetFallbackResponseSchemaTest(TestCase):
    """Verify the fallback response matches the expected schema."""

    def test_fallback_returns_results_list(self):
        df = _make_df(5)
        engine = ProphetEngine()
        result = engine.predict(df, periods=7)
        self.assertIsInstance(result['results'], list)
        self.assertEqual(len(result['results']), 7)

    def test_fallback_result_fields(self):
        df = _make_df(5)
        engine = ProphetEngine()
        result = engine.predict(df, periods=3)
        for item in result['results']:
            self.assertIn('forecast_date', item)
            self.assertIn('predicted_quantity', item)
            self.assertIn('lower_bound', item)
            self.assertIn('upper_bound', item)

    def test_fallback_bounds_are_symmetric(self):
        df = _make_df(10)
        engine = ProphetEngine()
        result = engine.predict(df, periods=5)
        for item in result['results']:
            self.assertAlmostEqual(
                item['lower_bound'],
                item['predicted_quantity'] * 0.8,
                delta=0.1,
            )
            self.assertAlmostEqual(
                item['upper_bound'],
                item['predicted_quantity'] * 1.2,
                delta=0.1,
            )

    def test_fallback_mae_mape_are_none(self):
        df = _make_df(10)
        engine = ProphetEngine()
        result = engine.predict(df, periods=5)
        self.assertIsNone(result['mae'])
        self.assertIsNone(result['mape'])

    def test_fallback_non_negative_predictions(self):
        df = _make_df(10)
        engine = ProphetEngine()
        result = engine.predict(df, periods=5)
        for item in result['results']:
            self.assertGreaterEqual(item['predicted_quantity'], 0)
            self.assertGreaterEqual(item['lower_bound'], 0)
            self.assertGreaterEqual(item['upper_bound'], 0)


class MovingAverageForecastTest(TestCase):
    """Test the _moving_average_forecast helper directly."""

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=['ds', 'y'])
        result = _moving_average_forecast(df, periods=5)
        self.assertEqual(len(result), 5)
        self.assertTrue((result['yhat'] == 0.0).all())

    def test_single_row(self):
        df = pd.DataFrame({'ds': pd.to_datetime(['2025-01-01']), 'y': [50.0]})
        result = _moving_average_forecast(df, periods=3)
        self.assertEqual(len(result), 3)
        self.assertTrue((result['yhat'] >= 0).all())

    def test_window_respects_data_length(self):
        df = _make_df(3)
        result = _moving_average_forecast(df, periods=2)
        self.assertEqual(len(result), 2)

    def test_constant_values(self):
        dates = pd.date_range('2025-01-01', periods=10, freq='D')
        df = pd.DataFrame({'ds': dates, 'y': [50.0] * 10})
        result = _moving_average_forecast(df, periods=3)
        for _, row in result.iterrows():
            self.assertAlmostEqual(row['yhat'], 50.0, places=1)


class ProphetProphetImportErrorTest(TestCase):
    """Test behavior when Prophet is not installed."""

    def test_fallback_when_prophet_import_fails(self):
        with patch.dict('sys.modules', {'prophet': None}):
            engine = ProphetEngine()
            df = _make_df(40)
            result = engine.predict(df, periods=5)
            self.assertEqual(result['forecast_method'], 'moving_average')

    def test_fallback_when_prophet_fit_fails(self):
        """When Prophet class raises on fit, engine falls back to MA."""
        mock_module = MagicMock()
        mock_class = MagicMock()
        mock_class.return_value.fit.side_effect = RuntimeError('fit failed')
        mock_module.Prophet = mock_class

        with patch.dict('sys.modules', {'prophet': mock_module}):
            engine = ProphetEngine()
            df = _make_df(40)
            result = engine.predict(df, periods=5)
            self.assertEqual(result['forecast_method'], 'moving_average')
