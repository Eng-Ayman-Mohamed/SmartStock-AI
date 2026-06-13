import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)

SUPPLIER_TIMEOUT_HOURS = 48


@shared_task
def check_supplier_timeouts() -> dict:
    """Detect supplier purchase orders that have exceeded the response timeout.

    Finds POs with status in ('email_sent', 'waiting_confirmation') where
    sent_at is older than 48 hours. Marks them as timed out and triggers
    escalation notifications.

    Returns:
        dict with count of timed-out POs and list of affected IDs.
    """
    from apps.purchasing.models import PurchaseOrder

    cutoff = timezone.now() - timedelta(hours=SUPPLIER_TIMEOUT_HOURS)

    stale_pos = PurchaseOrder.objects.filter(
        status__in=['email_sent', 'waiting_confirmation'],
        sent_at__isnull=False,
        sent_at__lte=cutoff,
    ).select_related('supplier', 'sku', 'requested_by')

    timed_out_ids: list[int] = []

    for po in stale_pos:
        try:
            po.status = 'timeout'
            po.notes = (
                (po.notes + '\n' if po.notes else '')
                + f'Timed out: no supplier response within {SUPPLIER_TIMEOUT_HOURS} hours '
                f'(detected at {timezone.now().isoformat()})'
            )
            po.save(update_fields=['status', 'notes', 'updated_at'])

            _create_audit_log(po)
            _trigger_escalation(po)

            timed_out_ids.append(po.id)

            logger.info(
                'Supplier timeout: PO-%s (supplier=%s, sent_at=%s)',
                po.id,
                po.supplier.name if po.supplier else 'Unknown',
                po.sent_at.isoformat() if po.sent_at else 'None',
            )
        except Exception:
            logger.exception('Failed to timeout PO-%s', po.id)

    result = {
        'timed_out_count': len(timed_out_ids),
        'timed_out_ids': timed_out_ids,
        'checked_at': timezone.now().isoformat(),
    }

    if timed_out_ids:
        logger.info(
            'Supplier timeout check complete: %d POs timed out (%s)',
            len(timed_out_ids),
            timed_out_ids,
        )
    else:
        logger.debug('Supplier timeout check complete: no timeouts found')

    return result


def _create_audit_log(po) -> None:
    """Create an audit log entry for the timeout event."""
    try:
        from apps.audit.models import AuditLog

        AuditLog.objects.create(
            event='SUPPLIER_TIMEOUT',
            entity_type='PurchaseOrder',
            entity_id=po.id,
            user=po.requested_by,
            data_snapshot={
                'supplier': po.supplier.name if po.supplier else '',
                'sku': po.sku.code if po.sku else '',
                'quantity': po.quantity,
                'sent_at': po.sent_at.isoformat() if po.sent_at else None,
                'timeout_hours': SUPPLIER_TIMEOUT_HOURS,
            },
        )
    except Exception:
        logger.exception('Failed to create audit log for PO-%s timeout', po.id)


def _trigger_escalation(po) -> None:
    """Trigger escalation notification for a timed-out PO."""
    try:
        from apps.notifications.service import create_escalation_notification

        create_escalation_notification(
            po=po,
            reason='supplier_timeout',
            message=(
                f'Supplier has not responded to PO-{po.id} within '
                f'{SUPPLIER_TIMEOUT_HOURS} hours.\n'
                f'Supplier: {po.supplier.name if po.supplier else "Unknown"}\n'
                f'SKU: {po.sku.code if po.sku else "Unknown"}\n'
                f'Quantity: {po.quantity}\n'
                f'Sent at: {po.sent_at.isoformat() if po.sent_at else "Unknown"}\n'
                f'Action required: Please follow up with the supplier.\n'
                f'Timestamp: {timezone.now().isoformat()}'
            ),
        )
    except Exception:
        logger.exception('Failed to create escalation for PO-%s', po.id)
