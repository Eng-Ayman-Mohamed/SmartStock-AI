import logging

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

logger = logging.getLogger(__name__)

MIN_DATA_POINTS = 30


def _moving_average_forecast(df: pd.DataFrame, periods: int = 30) -> pd.DataFrame:
    window = min(7, len(df))
    ma = df['y'].rolling(window=window).mean().iloc[-1]
    if pd.isna(ma):
        ma = df['y'].mean()
    forecast_dates = pd.date_range(
        start=df['ds'].max() + pd.Timedelta(days=1), periods=periods
    )
    forecast = pd.DataFrame({'ds': forecast_dates})
    forecast['yhat'] = max(ma, 0)
    forecast['yhat_lower'] = forecast['yhat'] * 0.8
    forecast['yhat_upper'] = forecast['yhat'] * 1.2
    return forecast


def _compute_accuracy(df: pd.DataFrame, model) -> tuple:
    if len(df) < 2:
        return None, None
    split_idx = max(1, int(len(df) * 0.9))
    train = df.iloc[:split_idx]
    test = df.iloc[split_idx:]
    if len(test) < 1:
        return None, None
    future = test[['ds']].copy()
    future.rename(columns={'ds': 'ds'}, inplace=True)
    forecast = model.predict(future)
    y_true = test['y'].values
    y_pred = forecast['yhat'].values
    y_true = np.maximum(y_true, 0)
    y_pred = np.maximum(y_pred, 0)
    mae = mean_absolute_error(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred)
    return float(mae), float(mape)


class ProphetEngine:
    def predict(self, df: pd.DataFrame, periods: int = 30) -> dict:
        if len(df) < MIN_DATA_POINTS:
            return self._fallback_predict(df, periods)

        try:
            from prophet import Prophet
        except ImportError:
            logger.warning("Prophet not installed; using moving average fallback")
            return self._fallback_predict(df, periods)

        df = df.sort_values('ds').reset_index(drop=True)
        df['y'] = df['y'].clip(lower=0)

        model = Prophet(
            weekly_seasonality=True,
            yearly_seasonality=len(df) >= 365,
            daily_seasonality=False,
        )
        model.fit(df[['ds', 'y']])

        future = model.make_future_dataframe(periods=periods)
        forecast = model.predict(future)
        forecast = forecast.iloc[-periods:]

        mae, mape = _compute_accuracy(df, model)

        results = []
        for _, row in forecast.iterrows():
            results.append({
                'forecast_date': row['ds'].date().isoformat(),
                'predicted_quantity': max(round(row['yhat'], 2), 0),
                'lower_bound': max(round(row['yhat_lower'], 2), 0),
                'upper_bound': max(round(row['yhat_upper'], 2), 0),
            })

        return {
            'results': results,
            'mae': mae,
            'mape': mape,
            'model_version': 'prophet_1.1',
        }

    def _fallback_predict(self, df: pd.DataFrame, periods: int = 30) -> dict:
        logger.info(
            "Insufficient data (%d points); using moving average fallback",
            len(df),
        )
        forecast = _moving_average_forecast(df, periods)
        results = []
        for _, row in forecast.iterrows():
            results.append({
                'forecast_date': row['ds'].date().isoformat(),
                'predicted_quantity': max(round(row['yhat'], 2), 0),
                'lower_bound': max(round(row['yhat_lower'], 2), 0),
                'upper_bound': max(round(row['yhat_upper'], 2), 0),
            })
        return {
            'results': results,
            'mae': None,
            'mape': None,
            'model_version': 'moving_average_fallback',
        }
