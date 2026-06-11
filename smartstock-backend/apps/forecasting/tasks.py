import logging

from celery import shared_task

from apps.inventory.models import SKU

logger = logging.getLogger(__name__)


@shared_task
def run_forecast_for_all_skus():
    """Trigger forecast computation for every active SKU."""
    from .services import ForecastingService

    sku_ids = list(SKU.objects.values_list('id', flat=True))
    logger.info('Running forecast for %d SKUs', len(sku_ids))
    service = ForecastingService()
    results = []
    for sku_id in sku_ids:
        try:
            service.run_forecast(sku_id=sku_id)
            results.append(sku_id)
        except Exception:
            logger.exception('Forecast failed for SKU %d', sku_id)
    return f'Forecasted {len(results)}/{len(sku_ids)} SKUs'
