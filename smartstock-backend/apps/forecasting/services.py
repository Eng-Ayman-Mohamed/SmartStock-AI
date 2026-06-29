import logging
import math

from django.core.cache import cache

from apps.inventory.models import StockLevel

from .ingestion import prepare_forecast_dataframe
from .prophet_engine import ProphetEngine
from .repositories import ForecastingRepository

logger = logging.getLogger(__name__)

DASHBOARD_CACHE_VERSION = '3'
MAX_DASHBOARD_SKUS = 500


class ForecastingService:
    def __init__(self, repo=None, engine=None):
        self.repo = repo or ForecastingRepository()
        self.engine = engine or ProphetEngine()

    def calculate_stockout_risk(self, sku_code: str) -> bool:
        try:
            stock = StockLevel.objects.select_related('sku__product__supplier').get(
                sku__code=sku_code
            )
            lead_time = getattr(stock.sku.product.supplier, 'default_lead_time_days', None) or 7
            forecasts = (
                self.repo.get_all().filter(sku=stock.sku).order_by('-forecast_date')[:lead_time]
            )
            total_predicted = sum(f.predicted_quantity for f in forecasts)
            safety_stock = stock.sku.product.safety_stock or 0
            return stock.quantity_available < total_predicted + safety_stock
        except StockLevel.DoesNotExist:
            logger.warning('No stock level found for SKU %s', sku_code)
            return False
        except Exception:
            logger.exception('Failed to calculate stockout risk for SKU %s', sku_code)
            return False

    def get_dashboard_data(self, page: int = 1, page_size: int = 6):
        cache_key = f'forecast_dashboard_data_v{DASHBOARD_CACHE_VERSION}'
        full_data = None
        try:
            full_data = cache.get(cache_key)
        except Exception:
            logger.exception('Dashboard cache read failed')
        if full_data is None:
            full_data = self._compute_dashboard()
            try:
                cache.set(cache_key, full_data, timeout=3600)
            except Exception:
                logger.exception('Dashboard cache write failed')

        all_skus = full_data['skus']
        total = len(all_skus)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_skus = all_skus[start:end]

        alerts = [
            sku
            for sku in all_skus
            if sku.get('stockout_risk')
            or sku.get('current_stock', 0) <= sku.get('reorder_point', 0)
        ]

        return {
            'skus': paginated_skus,
            'alerts': alerts,
            'total': total,
            'page': page,
            'per_page': page_size,
        }

    def _compute_dashboard(self):
        import datetime
        from collections import defaultdict

        from apps.inventory.models import StockLevel

        from .models import ForecastResult

        try:
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
                    if len(skus_map) >= MAX_DASHBOARD_SKUS:
                        continue  # Prevent unbounded cache entries
                    stock = stock_map.get(sku_id)
                    if stock:
                        supplier = stock.sku.product.supplier
                        lead_time = getattr(supplier, 'default_lead_time_days', None) or 7
                        sku_forecasts = forecasts_by_sku.get(sku_id, [])[:lead_time]
                        total_predicted = sum(f.predicted_quantity for f in sku_forecasts)
                        safety_stock = stock.sku.product.safety_stock or 0
                        stockout_risk = stock.quantity_available < total_predicted + safety_stock
                    else:
                        stockout_risk = False

                    mape = row.mape
                    # Prefer MAPE from Prophet rows over fallback rows
                    if mape is None and forecasts_by_sku.get(sku_id):
                        for f in forecasts_by_sku[sku_id]:
                            if f.mape is not None:
                                mape = f.mape
                                break
                    # Normalize MAPE: Prophet returns raw ratio (0.0-1.0),
                    # seed data returns percentage (2-25).
                    # If MAPE > 1, it's already a percentage; if <= 1, multiply by 100.
                    if mape is not None:
                        mape_pct = mape * 100 if mape <= 1.0 else mape
                        if math.isfinite(mape_pct):
                            confidence = max(0, min(100, round(100 - mape_pct)))
                        else:
                            confidence = None
                    else:
                        confidence = None

                    supplier_name = '—'
                    lead_time_days = 7
                    if stock:
                        supplier = stock.sku.product.supplier
                        if supplier:
                            supplier_name = supplier.name
                            lead_time_days = getattr(supplier, 'default_lead_time_days', None) or 7

                    skus_map[sku_id] = {
                        'id': row.sku.code,
                        'sku_code': row.sku.code,
                        'product_name': row.sku.product.name,
                        'reorder_point': stock.reorder_point if stock else 0,
                        'current_stock': stock.quantity_on_hand if stock else 0,
                        'stockout_risk': stockout_risk,
                        'supplier': supplier_name,
                        'lead_time_days': lead_time_days,
                        'mae': row.mae,
                        'mape': mape,
                        'model_version': row.model_version,
                        'confidence_score': confidence,
                        'predicted_demand_30d': 0,
                        'forecast': [],
                    }
                skus_map[sku_id]['forecast'].append(
                    {
                        'date': row.forecast_date.isoformat(),
                        'demand': round(row.predicted_quantity, 2),
                        'upper_bound': round(row.upper_bound, 2) if row.upper_bound else None,
                        'lower_bound': round(row.lower_bound, 2) if row.lower_bound else None,
                    }
                )
                skus_map[sku_id]['predicted_demand_30d'] += round(row.predicted_quantity, 2)

            return {'skus': list(skus_map.values())}
        except Exception:
            logger.exception('Failed to compute forecast dashboard')
            return {'skus': []}

    def get_forecast(self, sku_id: int):
        return self.repo.get_by_sku(sku_id)

    def get_forecast_by_sku_code_or_id(self, sku: str):
        return self.repo.get_by_sku_code_or_id(sku)

    def get_decision_forecast_data(self, product_id: int, forecast_days: int = 7) -> dict:
        forecast_days = max(1, int(forecast_days or 7))
        forecasts = list(self.repo.get_next_for_product(product_id, forecast_days))
        sku_code = forecasts[0].sku.code if forecasts else ''
        if not sku_code:
            sku = self.repo.get_primary_sku_for_product(product_id)
            sku_code = sku.code if sku else ''

        total_predicted = sum(float(f.predicted_quantity or 0) for f in forecasts)
        return {
            'sku_code': sku_code,
            'forecast_days': forecast_days,
            'total_predicted_demand': total_predicted,
        }

    def persist_reorder_flag(self, decision: dict):
        sku = self.repo.get_sku_by_code(decision['sku_code'])
        flag = self.repo.upsert_open_reorder_flag(
            sku_id=sku.id,
            data={
                'quantity_available': decision['quantity_available'],
                'total_predicted_demand': decision['total_predicted_demand'],
                'safety_stock': decision['safety_stock'],
                'lead_time_days': decision['lead_time_days'],
                'forecast_days': decision['forecast_days'],
                'reorder_required': decision['reorder_required'],
                'has_open_po': decision['has_open_po'],
                'open_po_id': decision.get('open_po_id'),
                'reasoning': decision['reasoning'],
            },
        )
        return flag

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
                'forecast_method': None,
                'mae': None,
                'mape': None,
            }

        result = self.engine.predict(df, periods=30)

        created = 0
        mae = result['mae']
        mape = result['mape']
        if mae is not None and not math.isfinite(mae):
            mae = None
        if mape is not None and not math.isfinite(mape):
            mape = None
        for pred in result['results']:
            self.repo.upsert(
                sku_id=sku.id,
                forecast_date=pred['forecast_date'],
                predicted_quantity=pred['predicted_quantity'],
                lower_bound=pred['lower_bound'],
                upper_bound=pred['upper_bound'],
                mae=mae,
                mape=mape,
                model_version=result['model_version'],
            )
            created += 1

        return {
            'sku': sku.code,
            'status': 'success',
            'forecast_days': created,
            'model_version': result['model_version'],
            'forecast_method': result.get('forecast_method', 'unknown'),
            'mae': mae,
            'mape': mape,
        }
