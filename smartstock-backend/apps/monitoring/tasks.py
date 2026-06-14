"""Celery tasks for the monitoring subsystem.

All tasks use bind=True + max_retries for transient-failure resilience.
Token usage recording uses F() expressions for atomic DB updates.
"""

import logging

from celery import shared_task
from django.db.models import F, Sum

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30, acks_late=True)
def evaluate_all_alerts_task(self):
    """Periodically evaluate application-specific alert rules.

    Scheduled via Celery beat every 5 minutes.
    P95 latency and error-rate alerts are handled by Prometheus natively.
    """
    from .alerts import evaluate_all_alerts

    try:
        results = evaluate_all_alerts()
        logger.info('Alert evaluation results: %s', results)
        return results
    except Exception as exc:
        logger.exception('evaluate_all_alerts_task failed: %s', exc)
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error('evaluate_all_alerts_task exceeded max retries')


@shared_task(bind=True, max_retries=3, default_retry_delay=10, acks_late=True)
def record_token_usage_task(self, total_tokens: int, input_tokens: int = 0, output_tokens: int = 0):
    """Record token usage and update daily aggregate.

    Uses F() expressions for atomic updates to prevent race conditions
    when multiple Celery workers process token records concurrently.
    """
    from django.utils import timezone

    from .metrics import DAILY_TOKEN_USAGE, TOKEN_USAGE_TOTAL
    from .models import TokenUsageLog

    today = timezone.now().date()

    TOKEN_USAGE_TOTAL.labels(type='total').inc(total_tokens)
    TOKEN_USAGE_TOTAL.labels(type='input').inc(input_tokens)
    TOKEN_USAGE_TOTAL.labels(type='output').inc(output_tokens)

    try:
        log, created = TokenUsageLog.objects.get_or_create(
            logged_at=today,
            defaults={
                'total_tokens': total_tokens,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
            },
        )
        if not created:
            TokenUsageLog.objects.filter(pk=log.pk).update(
                total_tokens=F('total_tokens') + total_tokens,
                input_tokens=F('input_tokens') + input_tokens,
                output_tokens=F('output_tokens') + output_tokens,
            )

        daily_total = (
            TokenUsageLog.objects.filter(logged_at=today).aggregate(t=Sum('total_tokens'))['t'] or 0
        )
        DAILY_TOKEN_USAGE.set(daily_total)
    except Exception as exc:
        logger.exception('record_token_usage_task failed: %s', exc)
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error('record_token_usage_task exceeded max retries')


@shared_task(bind=True, max_retries=3, default_retry_delay=10, acks_late=True)
def record_agent_run_task(
    self, agent_name: str, outcome: str, duration_ms: int = 0, error_message: str = ''
):
    """Record an agent run and update success rate metric."""
    from .metrics import AGENT_RUN_TOTAL
    from .models import AgentRunLog

    try:
        AgentRunLog.objects.create(
            agent_name=agent_name,
            outcome=outcome,
            duration_ms=duration_ms,
            error_message=error_message,
        )

        AGENT_RUN_TOTAL.labels(agent_name=agent_name, outcome=outcome).inc()
    except Exception as exc:
        logger.exception('record_agent_run_task failed: %s', exc)
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error('record_agent_run_task exceeded max retries')
