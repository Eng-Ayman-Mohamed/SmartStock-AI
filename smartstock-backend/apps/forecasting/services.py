import logging

import pandas as pd

from .repositories import ForecastingRepository
from .prophet_engine import ProphetEngine

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
        sales = self.repo.get_sales_for_sku(sku.id)
        if not sales:
            logger.warning("No sales data for SKU %s; skipping", sku.code)
            return {'sku': sku.code, 'status': 'skipped', 'reason': 'no_data'}

        df = pd.DataFrame([
            {'ds': r.date, 'y': float(r.quantity_sold)}
            for r in sales
        ])
        df = df.sort_values('ds').drop_duplicates(subset='ds').reset_index(drop=True)

        full_range = pd.date_range(
            start=df['ds'].min(), end=df['ds'].max(), freq='D'
        )
        df = df.set_index('ds').reindex(full_range).fillna(0).rename_axis('ds').reset_index()

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
