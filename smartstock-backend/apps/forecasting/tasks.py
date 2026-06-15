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

    Returns:
        dict with agent run results.
    """
    from ai.agents.forecasting_agent import ForecastingAgent

    context = {}
    if sku_ids is not None:
        context['sku_ids'] = sku_ids

    logger.info('Running forecasting agent (SKUs: %s)', sku_ids if sku_ids else 'ALL')
    agent = ForecastingAgent()
    result = agent.run(context)
    logger.info(
        'Forecasting agent completed: %d processed, %d skipped, %d failed',
        result.get('processed', 0),
        result.get('skipped', 0),
        result.get('failed', 0),
    )
    try:
        cache.delete_pattern('forecast_dashboard_*')
    except Exception:
        logger.warning('Failed to invalidate forecast dashboard cache', exc_info=True)
    return result


@shared_task(rate_limit='10/m')
def run_forecast_single_sku(sku_id: int):
    """Forecast a single SKU in parallel."""
    from .services import ForecastingService

    service = ForecastingService()
    try:
        result = service.run_forecast(sku_id=sku_id)
        return {'sku_id': sku_id, 'status': 'success', 'result': result}
    except Exception as e:
        logger.exception('Forecast failed for SKU %s: %s', sku_id, e)
        return {'sku_id': sku_id, 'status': 'failed', 'error': str(e)}
