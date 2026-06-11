import logging

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

logger = logging.getLogger(__name__)

MIN_DATA_POINTS = 30


def _moving_average_forecast(df: pd.DataFrame, periods: int = 30) -> pd.DataFrame:
    if df.empty:
        forecast_dates = pd.date_range(start=pd.Timestamp.today(), periods=periods)
        forecast = pd.DataFrame({'ds': forecast_dates})
        forecast['yhat'] = 0.0
        forecast['yhat_lower'] = 0.0
        forecast['yhat_upper'] = 0.0
        return forecast
    window = min(7, len(df))
    ma = df['y'].rolling(window=window).mean().iloc[-1]
    if pd.isna(ma):
        ma = df['y'].mean()
    forecast_dates = pd.date_range(start=df['ds'].max() + pd.Timedelta(days=1), periods=periods)
    forecast = pd.DataFrame({'ds': forecast_dates})
    forecast['yhat'] = max(ma, 0)
    forecast['yhat_lower'] = forecast['yhat'] * 0.8
    forecast['yhat_upper'] = forecast['yhat'] * 1.2
    return forecast


def _compute_accuracy(df: pd.DataFrame, model) -> tuple:
    if len(df) < 2:
        return None, None
    forecast = model.predict(df[['ds']])
    y_true = df['y'].values
    y_pred = forecast['yhat'].values
    y_true = np.maximum(y_true, 0)
    y_pred = np.maximum(y_pred, 0)
    mae = mean_absolute_error(y_true, y_pred)
    nonzero_mask = y_true > 0
    if nonzero_mask.sum() > 0:
        mape = float(np.mean(np.abs((y_true[nonzero_mask] - y_pred[nonzero_mask]) / y_true[nonzero_mask])))
    else:
        mape = float('inf')
    return float(mae), mape


class ProphetEngine:
    def predict(self, df: pd.DataFrame, periods: int = 30) -> dict:
        if len(df) < MIN_DATA_POINTS:
            return self._fallback_predict(df, periods)

        try:
            from prophet import Prophet as _Prophet
        except Exception:
            logger.warning('Prophet not available; using moving average fallback')
            return self._fallback_predict(df, periods)

        df = df.sort_values('ds').reset_index(drop=True)
        df['y'] = df['y'].clip(lower=0)

        split_idx = max(1, int(len(df) * 0.9))
        train_df = df.iloc[:split_idx]
        test_df = df.iloc[split_idx:]

        try:
            model = _Prophet(
                weekly_seasonality=True,
                yearly_seasonality=len(df) >= 365,
                daily_seasonality=False,
            )
            model.fit(train_df[['ds', 'y']])
        except Exception:
            logger.warning('Prophet model failed; using moving average fallback')
            return self._fallback_predict(df, periods)

        mae, mape = _compute_accuracy(test_df, model) if len(test_df) >= 2 else (None, None)

        try:
            model2 = _Prophet(
                weekly_seasonality=True,
                yearly_seasonality=len(df) >= 365,
                daily_seasonality=False,
            )
            model2.fit(df[['ds', 'y']])
        except Exception:
            logger.warning('Prophet refit failed; using original model for forecast')
            model2 = model

        future = model2.make_future_dataframe(periods=periods)
        forecast = model2.predict(future)
        forecast = forecast.iloc[-periods:]

        results = []
        for _, row in forecast.iterrows():
            results.append(
                {
                    'forecast_date': row['ds'].date().isoformat(),
                    'predicted_quantity': max(round(row['yhat'], 2), 0),
                    'lower_bound': max(round(row['yhat_lower'], 2), 0),
                    'upper_bound': max(round(row['yhat_upper'], 2), 0),
                }
            )

        return {
            'results': results,
            'mae': mae,
            'mape': mape,
            'model_version': 'prophet_1.1',
        }

    def _fallback_predict(self, df: pd.DataFrame, periods: int = 30) -> dict:
        logger.info(
            'Insufficient data (%d points); using moving average fallback',
            len(df),
        )
        forecast = _moving_average_forecast(df, periods)
        results = []
        for _, row in forecast.iterrows():
            results.append(
                {
                    'forecast_date': row['ds'].date().isoformat(),
                    'predicted_quantity': max(round(row['yhat'], 2), 0),
                    'lower_bound': max(round(row['yhat_lower'], 2), 0),
                    'upper_bound': max(round(row['yhat_upper'], 2), 0),
                }
            )
        return {
            'results': results,
            'mae': None,
            'mape': None,
            'model_version': 'moving_average_fallback',
        }
