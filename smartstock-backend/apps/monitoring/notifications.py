import logging

from django.utils import timezone

logger = logging.getLogger(__name__)


def send_alert_email(alert_event) -> bool:
    """Send email notification for an alert event. Returns True on success."""
    from django.conf import settings
    from django.core.mail import send_mail

    recipients = getattr(settings, 'ESCALATION_RECIPIENT_EMAILS', [])
    if not recipients:
        logger.warning('No ESCALATION_RECIPIENT_EMAILS configured; skipping alert email')
        return False

    subject = f'[{alert_event.rule.severity.upper()}] {alert_event.rule.name}'
    body = (
        f'Alert: {alert_event.rule.name}\n'
        f'Severity: {alert_event.rule.get_severity_display()}\n'
        f'Status: {alert_event.get_status_display()}\n'
        f'Triggered Value: {alert_event.triggered_value}\n'
        f'Message: {alert_event.message}\n'
        f'Metric: {alert_event.rule.metric_name}\n'
        f'Threshold: {alert_event.rule.threshold}\n'
        f'Time: {timezone.now().isoformat()}\n'
    )

    if alert_event.status == 'resolved':
        subject = f'[RESOLVED] {alert_event.rule.name}'
        body += f'\nResolved at: {alert_event.resolved_at.isoformat() if alert_event.resolved_at else "N/A"}\n'

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartstock.ai'),
            recipient_list=recipients,
            fail_silently=False,
        )
        logger.info('Alert email sent: %s to %s', alert_event.rule.name, recipients)
        return True
    except Exception as exc:
        logger.exception('Failed to send alert email for %s: %s', alert_event.rule.name, exc)
        return False


def send_dashboard_notification(alert_event) -> bool:
    """Create a dashboard banner for an alert event. Returns True on success."""
    from .models import DashboardBanner

    try:
        banner = DashboardBanner.objects.create(
            title=f'{alert_event.rule.name}',
            message=alert_event.message,
            level=_severity_to_banner_level(alert_event.rule.severity),
            alert_event=alert_event,
        )
        logger.info('Dashboard banner created: %s', banner.title)
        return True
    except Exception as exc:
        logger.exception('Failed to create dashboard banner: %s', exc)
        return False


def _severity_to_banner_level(severity):
    from .models import AlertSeverity, DashboardBanner

    mapping = {
        AlertSeverity.INFO: DashboardBanner.Level.INFO,
        AlertSeverity.WARNING: DashboardBanner.Level.WARNING,
        AlertSeverity.CRITICAL: DashboardBanner.Level.ERROR,
    }
    return mapping.get(severity, DashboardBanner.Level.INFO)
