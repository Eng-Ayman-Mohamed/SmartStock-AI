import logging
from datetime import timedelta

from django.utils import timezone

from .metrics import (
    AGENT_SUCCESS_RATE_GAUGE,
    get_current_error_rate,
    get_current_p95_latency,
    set_current_daily_token_budget,
)
from .models import (
    AgentRunLog,
    AlertEvent,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    TokenUsageLog,
)
from .notifications import send_alert_email, send_dashboard_notification

logger = logging.getLogger(__name__)


def _get_alert_config():
    from django.conf import settings

    return getattr(settings, 'LANGFUSE_ALERT_THRESHOLDS', {})


def evaluate_p95_latency():
    """Evaluate P95 latency alert."""
    rule, _ = AlertRule.objects.get_or_create(
        name='P95 Latency Alert',
        defaults={
            'description': 'Triggers when P95 request latency exceeds 3 seconds',
            'severity': AlertSeverity.WARNING,
            'metric_name': 'http_request_p95_latency_seconds',
            'threshold': 3.0,
            'evaluation_window_minutes': 5,
            'cooldown_minutes': 10,
        },
    )

    current_value = get_current_p95_latency()
    threshold = _get_alert_config().get('llm_latency_p95_ms_warning', 3000) / 1000.0

    return _evaluate_rule(rule, current_value, threshold)


def evaluate_error_rate():
    """Evaluate error rate alert."""
    rule, _ = AlertRule.objects.get_or_create(
        name='Error Rate Alert',
        defaults={
            'description': 'Triggers when application error rate exceeds 1%',
            'severity': AlertSeverity.CRITICAL,
            'metric_name': 'http_error_rate',
            'threshold': 0.01,
            'evaluation_window_minutes': 5,
            'cooldown_minutes': 10,
        },
    )

    current_value = get_current_error_rate()
    threshold = _get_alert_config().get('llm_api_error_rate_critical', 0.01)

    return _evaluate_rule(rule, current_value, threshold)


def evaluate_token_spend():
    """Evaluate daily token spend cap alert."""
    rule, _ = AlertRule.objects.get_or_create(
        name='Daily Token Spend Cap',
        defaults={
            'description': 'Triggers when daily token spending cap is reached',
            'severity': AlertSeverity.WARNING,
            'metric_name': 'ai_daily_token_spend',
            'threshold': 1_000_000,
            'evaluation_window_minutes': 60,
            'cooldown_minutes': 60,
        },
    )

    config = _get_alert_config()
    threshold = float(config.get('daily_token_budget_alert', 1_000_000))

    if rule.threshold != threshold:
        rule.threshold = threshold
        rule.save(update_fields=['threshold'])

    set_current_daily_token_budget(threshold)

    today = timezone.now().date()
    daily_total = TokenUsageLog.objects.filter(logged_at=today).values_list(
        'total_tokens', flat=True
    )
    current_value = sum(daily_total)

    return _evaluate_rule(rule, current_value, threshold)


def evaluate_agent_success_rate():
    """Evaluate agent success rate alert."""
    rule, _ = AlertRule.objects.get_or_create(
        name='Agent Success Rate Alert',
        defaults={
            'description': 'Triggers when AI agent success rate falls below 80%',
            'severity': AlertSeverity.CRITICAL,
            'metric_name': 'ai_agent_success_rate_current',
            'threshold': 0.80,
            'evaluation_window_minutes': 30,
            'cooldown_minutes': 15,
        },
    )

    config = _get_alert_config()
    threshold = float(config.get('agent_success_rate_minimum', 0.80))

    if rule.threshold != threshold:
        rule.threshold = threshold
        rule.save(update_fields=['threshold'])

    window_start = timezone.now() - timedelta(minutes=rule.evaluation_window_minutes)
    runs = AgentRunLog.objects.filter(created_at__gte=window_start)
    total = runs.count()

    if total == 0:
        AGENT_SUCCESS_RATE_GAUGE.set(1.0)
        return None

    successes = runs.filter(outcome='success').count()
    success_rate = successes / total
    AGENT_SUCCESS_RATE_GAUGE.set(success_rate)

    # Alert fires when success rate is BELOW threshold
    if success_rate < threshold:
        return _fire_alert(
            rule,
            success_rate,
            f'Agent success rate {success_rate:.2%} is below threshold {threshold:.2%}',
        )
    else:
        _resolve_if_was_firing(rule, success_rate)
        return None


def _evaluate_rule(rule, current_value, threshold):
    """Generic alert evaluation: fire when value > threshold, resolve when below."""
    if not rule.enabled:
        return None

    if current_value > threshold:
        # Check cooldown before firing
        last_fired = (
            AlertEvent.objects.filter(rule=rule, status=AlertStatus.FIRING)
            .order_by('-created_at')
            .first()
        )
        if last_fired:
            cooldown_end = last_fired.created_at + timedelta(minutes=rule.cooldown_minutes)
            if timezone.now() < cooldown_end:
                return None

        msg = f'{rule.metric_name} value {current_value:.4f} exceeds threshold {threshold:.4f}'
        return _fire_alert(rule, current_value, msg)
    else:
        _resolve_if_was_firing(rule, current_value)
        return None


def _fire_alert(rule, value, message):
    """Create a firing alert event, send notifications, and log to Langfuse."""
    event = AlertEvent.objects.create(
        rule=rule,
        status=AlertStatus.FIRING,
        triggered_value=value,
        message=message,
    )

    logger.warning('ALERT FIRING: %s — %s', rule.name, message)

    email_sent = False
    dashboard_notified = False
    try:
        email_sent = send_alert_email(event)
    except Exception as exc:
        logger.exception('Failed to send alert email for %s: %s', rule.name, exc)
    try:
        dashboard_notified = send_dashboard_notification(event)
    except Exception as exc:
        logger.exception('Failed to send dashboard notification for %s: %s', rule.name, exc)

    event.email_sent = email_sent
    event.dashboard_notified = dashboard_notified
    event.save(update_fields=['email_sent', 'dashboard_notified'])

    _log_alert_to_langfuse(rule, value, message, 'firing')

    return event


def _resolve_if_was_firing(rule, current_value):
    """Resolve the most recent firing alert if it exists."""
    last_firing = (
        AlertEvent.objects.filter(rule=rule, status=AlertStatus.FIRING)
        .order_by('-created_at')
        .first()
    )
    if last_firing:
        last_firing.status = AlertStatus.RESOLVED
        last_firing.resolved_at = timezone.now()
        last_firing.message += f' — Resolved. Current value: {current_value:.4f}'
        last_firing.save(update_fields=['status', 'resolved_at', 'message'])
        logger.info('ALERT RESOLVED: %s', rule.name)

        try:
            send_dashboard_notification(last_firing)
        except Exception as exc:
            logger.exception('Failed to send resolution notification: %s', exc)


def evaluate_all_alerts():
    """Run all alert evaluations. Called by Celery beat."""
    results = {}
    evaluators = [
        ('p95_latency', evaluate_p95_latency),
        ('error_rate', evaluate_error_rate),
        ('token_spend', evaluate_token_spend),
        ('agent_success_rate', evaluate_agent_success_rate),
    ]
    for name, evaluator in evaluators:
        try:
            result = evaluator()
            results[name] = 'fired' if result else 'ok'
        except Exception as exc:
            logger.exception('Alert evaluation failed for %s: %s', name, exc)
            results[name] = f'error: {exc}'
    return results


def _log_alert_to_langfuse(rule, value, message, status):
    """Log an alert event to Langfuse as a trace with a score."""
    try:
        from ai.observability.langfuse import get_langfuse_client

        client = get_langfuse_client()
        if client is None:
            return

        trace = client.trace(
            name=f'alert_{rule.name}',
            input={'metric_name': rule.metric_name, 'threshold': rule.threshold},
            output={'value': value, 'message': message, 'status': status},
            metadata={
                'severity': rule.severity,
                'alert_rule': rule.name,
            },
        )
        severity_score = {'critical': 1.0, 'warning': 0.5, 'info': 0.1}.get(rule.severity, 0.0)
        client.score(
            trace_id=trace.id,
            name='alert_severity',
            value=severity_score,
        )
        client.flush()
    except Exception as exc:
        logger.debug('Langfuse alert trace skipped: %s', exc)
