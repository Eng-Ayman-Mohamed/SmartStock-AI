import logging
from typing import Any

from celery import shared_task
from django.utils import timezone

from infrastructure.email import (
    MAX_RETRIES,
    NON_RETRIABLE_EXCEPTIONS,
    RETRIABLE_EXCEPTIONS,
    RETRY_COUNTDOWN,
    send_email_core,
)

logger = logging.getLogger(__name__)


def is_retriable(exc: Exception) -> bool:
    """Check if an exception type qualifies for retry."""
    if isinstance(exc, NON_RETRIABLE_EXCEPTIONS):
        return False
    return isinstance(exc, RETRIABLE_EXCEPTIONS)


@shared_task(
    bind=True,
    max_retries=MAX_RETRIES,
    default_retry_delay=30,
    acks_late=True,
)
def send_email_with_retry(
    self: Any,
    subject: str,
    body: str,
    recipient: str,
    po_id: int | None = None,
    message_id: str | None = None,
) -> dict[str, Any]:
    """Send email with retry + PO-specific escalation.

    Delegates actual send to infrastructure.email.send_email_core.
    Celery retries on transient failures; permanent failures escalate.
    """
    retry_number = self.request.retries
    attempts = retry_number + 1

    try:
        result = send_email_core(subject=subject, body=body, recipient=recipient, message_id=message_id)
    except RETRIABLE_EXCEPTIONS as exc:
        if retry_number < MAX_RETRIES:
            countdown = RETRY_COUNTDOWN[min(retry_number, len(RETRY_COUNTDOWN) - 1)]
            raise self.retry(exc=exc, countdown=countdown)

        _trigger_escalation(po_id, f'{type(exc).__name__}: {exc}')
        return {
            'status': 'permanently_failed',
            'message_id': message_id,
            'recipient': recipient,
            'po_id': po_id,
            'error': f'{type(exc).__name__}: {exc}',
            'attempts': attempts,
        }

    base = {
        **result,
        'attempts': attempts,
        'po_id': po_id,
        'recipient': recipient,
    }

    if result['status'] == 'sent':
        return base

    _trigger_escalation(po_id, result.get('error', 'Email delivery failed'))
    return {**base, 'status': 'permanently_failed'}


def _trigger_escalation(po_id: int | None, error_reason: str) -> None:
    """Trigger an escalation notification for a permanently failed email."""
    if po_id is None:
        return
    try:
        from apps.audit.signals import log_event
        from apps.notifications.service import create_escalation_notification
        from apps.purchasing.models import PurchaseOrder

        po = PurchaseOrder.objects.get(pk=po_id)
        create_escalation_notification(
            po=po,
            reason='email_delivery_failed',
            message=(
                f'Email delivery for PO-{po_id} has permanently failed after '
                f'{MAX_RETRIES} retries.\n'
                f'Supplier: {po.supplier.name if po.supplier else "Unknown"}\n'
                f'Error: {error_reason}\n'
                f'Action required: Please contact the supplier manually.\n'
                f'Timestamp: {timezone.now().isoformat()}'
            ),
        )
        log_event(
            event='EMAIL_DELIVERY_FAILED',
            user=po.requested_by,
            entity_id=po_id,
            data_snapshot={
                'supplier': po.supplier.name if po.supplier else '',
                'error': error_reason,
                'retries': MAX_RETRIES,
            },
        )
    except Exception:
        logger.exception('Failed to create escalation for PO-%s', po_id)
