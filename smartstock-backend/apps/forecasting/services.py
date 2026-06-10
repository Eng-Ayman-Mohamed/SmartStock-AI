import logging

import pandas as pd

from .repositories import ForecastingRepository
from .prophet_engine import ProphetEngine
from .ingestion import prepare_forecast_dataframe

logger = logging.getLogger(__name__)


class ForecastingService:
    def __init__(self):
        self.repo = ForecastingRepository()
        self.engine = ProphetEngine()

    def get_forecast(self, sku_id: int):
        return self.repo.get_by_sku(sku_id)

    def run_forecast(self, sku_id: int = None):
        if sku_id:
            skus = [self.repo.get_sku(sku_id)]
        else:
            skus = self.repo.get_all_skus()

        results = []
        for sku in skus:
            try:
                result = self._forecast_for_sku(sku)
                results.append(result)
            except Exception as e:
                logger.exception("Forecast failed for SKU %s: %s", sku.code, e)
        return results

    def _forecast_for_sku(self, sku) -> dict:
        df = prepare_forecast_dataframe(sku.id)

        if df is None:
            logger.warning("Insufficient data for SKU %s; using moving average fallback", sku.code)
            empty_df = pd.DataFrame({'ds': pd.Series(dtype='datetime64[ns]'), 'y': pd.Series(dtype='float64')})
            result = self.engine._fallback_predict(empty_df, periods=30)
        else:
            result = self.engine.predict(df, periods=30)

        created = 0
        for pred in result['results']:
            self.repo.upsert(
                sku_id=sku.id,
                forecast_date=pred['forecast_date'],
                predicted_quantity=pred['predicted_quantity'],
                lower_bound=pred['lower_bound'],
                upper_bound=pred['upper_bound'],
                mae=result['mae'],
                mape=result['mape'],
                model_version=result['model_version'],
            )
            created += 1

        return {
            'sku': sku.code,
            'status': 'success',
            'forecast_days': created,
            'model_version': result['model_version'],
            'mae': result['mae'],
            'mape': result['mape'],
        }
