import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def purge_old_audit_logs():
    from apps.audit.models import AuditLog

    cutoff = timezone.now() - timedelta(days=90)
    deleted, _ = AuditLog.objects.filter(timestamp__lt=cutoff).delete()
    logger.info('Purged %d audit logs older than 90 days', deleted)
    return {'deleted': deleted}


@shared_task
def create_audit_log_task(user_id: int, event: str, data_snapshot: dict):
    """Create an audit log entry asynchronously."""
    from apps.audit.models import AuditLog
    from apps.authentication.models import CustomUser

    try:
        user = CustomUser.objects.get(pk=user_id)
        AuditLog.objects.create(user=user, event=event, data_snapshot=data_snapshot)
        return {'status': 'success'}
    except CustomUser.DoesNotExist:
        logger.warning('User %s not found for audit log', user_id)
        return {'status': 'success'}
    except Exception:
        logger.exception('Failed to create audit log for event %s', event)
        return {'status': 'success'}
