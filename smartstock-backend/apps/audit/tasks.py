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
