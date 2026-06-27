import logging

from celery import shared_task
from django.core.cache import cache

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
)
def run_forecasting_agent(self, sku_ids: list[int] | None = None):
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

    try:
        cache.delete_pattern('forecast_dashboard_*')
    except Exception:
        logger.warning('Failed to invalidate forecast dashboard cache', exc_info=True)

    return {'dispatched': len(sku_ids), 'group_id': str(result.id)}


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    rate_limit='10/m',
)
def run_forecast_single_sku(self, sku_id: int):
    """Forecast a single SKU in parallel."""
    from ai.agents.tracking import complete_agent_run, create_agent_run
    from apps.audit.models import AgentRun

    from .services import ForecastingService

    agent_run = create_agent_run('forecast_single_sku')
    status = AgentRun.Status.COMPLETED
    error = ''

    try:
        service = ForecastingService()
        result = service.run_forecast(sku_id=sku_id)
    except Exception as e:
        status = AgentRun.Status.FAILED
        error = str(e)
        result = []
    finally:
        complete_agent_run(agent_run.id, status=status, error_message=error)

    if status == AgentRun.Status.FAILED:
        return {'sku_id': sku_id, 'status': 'failed', 'error': error}

    return {'sku_id': sku_id, 'status': 'success', 'result': result}
