import logging

from celery import shared_task
from django.core.cache import cache

logger = logging.getLogger(__name__)


@shared_task
def run_forecasting_agent(sku_ids: list[int] | None = None):
    """Run the Forecasting Agent via Celery.

    Args:
        sku_ids: Optional list of SKU IDs to forecast.
                 If None, forecasts all active SKUs.
                 Uses Celery group() for parallel execution.

    Returns:
        dict with agent run results.
    """
    from celery import group

    from apps.inventory.models import SKU

    if sku_ids is None:
        sku_ids = list(SKU.objects.filter(product__is_active=True).values_list('id', flat=True))

    if not sku_ids:
        return {'processed': 0, 'skipped': 0, 'failed': 0}

    logger.info('Dispatching %d parallel forecast tasks', len(sku_ids))
    job = group(run_forecast_single_sku.s(sku_id) for sku_id in sku_ids)
    result = job.apply_async()

    return {'dispatched': len(sku_ids), 'group_id': str(result.id)}


@shared_task(rate_limit='10/m')
def run_forecast_single_sku(sku_id: int):
    """Forecast a single SKU in parallel."""
    from .services import ForecastingService

    service = ForecastingService()
    try:
        result = service.run_forecast(sku_id=sku_id)
        try:
            cache.delete_pattern('forecast_dashboard_*')
            if result:
                sku_code = result[0].get('sku')
                if sku_code:
                    cache.delete(f'forecast_sku_{sku_code}')
        except Exception:
            logger.warning('Failed to invalidate forecast cache', exc_info=True)
        return {'sku_id': sku_id, 'status': 'success', 'result': result}
    except Exception as e:
        logger.exception('Forecast failed for SKU %s: %s', sku_id, e)
        return {'sku_id': sku_id, 'status': 'failed', 'error': str(e)}
