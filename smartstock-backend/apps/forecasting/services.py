import logging

from django.core.cache import cache

from apps.inventory.models import StockLevel

from .ingestion import prepare_forecast_dataframe
from .prophet_engine import ProphetEngine
from .repositories import ForecastingRepository

logger = logging.getLogger(__name__)


class ForecastingService:
    def __init__(self):
        self.repo = ForecastingRepository()
        self.engine = ProphetEngine()

    def calculate_stockout_risk(self, sku_code: str) -> bool:
        try:
            stock = StockLevel.objects.get(sku__code=sku_code)
            lead_time = stock.sku.product.supplier.default_lead_time_days or 7
            forecasts = self.repo.get_all().filter(sku__code=sku_code).order_by('-forecast_date')[:lead_time]
            total_predicted = sum(f.predicted_quantity for f in forecasts)
            return stock.quantity_available < total_predicted + stock.sku.product.safety_stock
        except Exception:
            logger.exception('Failed to calculate stockout risk for SKU %s', sku_code)
            return False

    def get_dashboard_data(self):
        cache_key = 'forecast_dashboard_data'
        data = cache.get(cache_key)
        if data is not None:
            return data
        data = self._compute_dashboard()
        cache.set(cache_key, data, timeout=3600)
        return data

    def _compute_dashboard(self):
        import datetime

        from .models import ForecastResult

        today = datetime.date.today()
        horizon = today + datetime.timedelta(days=30)

        rows = (
            ForecastResult.objects.filter(forecast_date__gte=today, forecast_date__lte=horizon)
            .select_related('sku__product', 'sku__stock_level')
            .order_by('sku', 'forecast_date')
        )

        skus_map = {}
        for row in rows:
            sku_id = row.sku.id
            if sku_id not in skus_map:
                stock = getattr(row.sku, 'stock_level', None)
                stockout_risk = self.calculate_stockout_risk(row.sku.code)
                skus_map[sku_id] = {
                    'id': row.sku.code,
                    'name': row.sku.product.name,
                    'threshold': stock.reorder_point if stock else 0,
                    'current_stock': stock.quantity_on_hand if stock else 0,
                    'stockout_risk': stockout_risk,
                    'supplier': '—',
                    'lead_time_days': 0,
                    'mae': row.mae,
                    'mape': row.mape,
                    'model_version': row.model_version,
                    'days': [],
                }
            skus_map[sku_id]['days'].append(
                {
                    'date': row.forecast_date.isoformat(),
                    'demand': round(row.predicted_quantity, 2),
                    'upper_bound': round(row.upper_bound, 2) if row.upper_bound else None,
                    'lower_bound': round(row.lower_bound, 2) if row.lower_bound else None,
                }
            )

        return {'skus': list(skus_map.values())}

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
                logger.exception('Forecast failed for SKU %s: %s', sku.code, e)
        return results

    def _forecast_for_sku(self, sku) -> dict:
        df = prepare_forecast_dataframe(sku.id)

        if df is None:
            logger.warning('Insufficient data for SKU %s; skipping', sku.code)
            return {
                'sku': sku.code,
                'status': 'skipped',
                'reason': 'no_data',
                'forecast_days': 0,
                'model_version': None,
                'mae': None,
                'mape': None,
            }

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
