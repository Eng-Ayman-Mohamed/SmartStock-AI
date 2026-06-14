import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def evaluate_all_alerts_task():
    """Periodically evaluate all alert rules. Scheduled via Celery beat."""
    from .alerts import evaluate_all_alerts

    results = evaluate_all_alerts()
    logger.info('Alert evaluation results: %s', results)
    return results


@shared_task
def record_token_usage_task(total_tokens: int, input_tokens: int = 0, output_tokens: int = 0):
    """Record token usage and update daily aggregate."""
    from django.utils import timezone

    from .metrics import DAILY_TOKEN_USAGE, TOKEN_USAGE_TOTAL
    from .models import TokenUsageLog

    today = timezone.now().date()

    TOKEN_USAGE_TOTAL.labels(type='total').inc(total_tokens)
    TOKEN_USAGE_TOTAL.labels(type='input').inc(input_tokens)
    TOKEN_USAGE_TOTAL.labels(type='output').inc(output_tokens)

    log, created = TokenUsageLog.objects.get_or_create(
        logged_at=today,
        defaults={
            'total_tokens': total_tokens,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
        },
    )
    if not created:
        log.total_tokens += total_tokens
        log.input_tokens += input_tokens
        log.output_tokens += output_tokens
        log.save(update_fields=['total_tokens', 'input_tokens', 'output_tokens'])

    daily_total = sum(
        TokenUsageLog.objects.filter(logged_at=today).values_list('total_tokens', flat=True)
    )
    DAILY_TOKEN_USAGE.set(daily_total)


@shared_task
def record_agent_run_task(
    agent_name: str, outcome: str, duration_ms: int = 0, error_message: str = ''
):
    """Record an agent run and update success rate metric."""
    from .metrics import AGENT_RUN_TOTAL
    from .models import AgentRunLog

    AgentRunLog.objects.create(
        agent_name=agent_name,
        outcome=outcome,
        duration_ms=duration_ms,
        error_message=error_message,
    )

    AGENT_RUN_TOTAL.labels(agent_name=agent_name, outcome=outcome).inc()
