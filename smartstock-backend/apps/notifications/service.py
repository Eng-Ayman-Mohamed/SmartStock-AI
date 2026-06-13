import logging
from typing import TYPE_CHECKING

from django.utils import timezone

if TYPE_CHECKING:
    from apps.purchasing.models import PurchaseOrder

from .models import EscalationNotification

logger = logging.getLogger(__name__)


def get_escalation_recipients() -> list[str]:
    """Return configured escalation email recipients."""
    from django.conf import settings

    return getattr(settings, 'ESCALATION_RECIPIENT_EMAILS', [])


def create_escalation_notification(
    po: 'PurchaseOrder',
    reason: str,
    channel: str = 'email',
    message: str = '',
) -> EscalationNotification:
    """Create an escalation notification for a PO.

    Prevents duplicate notifications for the same PO + reason combination
    within a 24-hour window.
    """
    cutoff = timezone.now() - timezone.timedelta(hours=24)
    existing = EscalationNotification.objects.filter(
        po=po,
        reason=reason,
        created_at__gte=cutoff,
    ).exists()
    if existing:
        logger.info(
            'Duplicate escalation skipped for PO-%s reason=%s (already notified within 24h)',
            po.id,
            reason,
        )
        return (
            EscalationNotification.objects.filter(po=po, reason=reason)
            .order_by('-created_at')
            .first()
        )

    recipients = get_escalation_recipients()
    recipient_email = (
        recipients[0] if recipients else (po.supplier.contact_email if po.supplier else '')
    )

    notification = EscalationNotification.objects.create(
        po=po,
        reason=reason,
        channel=channel,
        recipient_email=recipient_email,
        message=message or _build_default_message(po, reason),
    )

    logger.info(
        'Escalation notification created: PO-%s reason=%s id=%s',
        po.id,
        reason,
        notification.id,
    )

    _send_escalation_email(notification)

    return notification


def _send_escalation_email(notification: EscalationNotification) -> None:
    """Attempt to send the escalation email. Failures are logged but not raised."""
    if not notification.recipient_email:
        logger.warning(
            'No recipient email for escalation notification %s; skipping email',
            notification.id,
        )
        return

    try:
        from infrastructure.email import EmailService

        service = EmailService()
        subject = f'[Escalation] PO-{notification.po_id} - {notification.get_reason_display()}'
        service.send(
            subject=subject,
            message=notification.message,
            recipient=notification.recipient_email,
        )
        notification.status = 'sent'
        notification.sent_at = timezone.now()
        notification.save(update_fields=['status', 'sent_at'])
        logger.info('Escalation email sent for notification %s', notification.id)
    except Exception as exc:
        notification.status = 'failed'
        notification.error_message = str(exc)
        notification.save(update_fields=['status', 'error_message'])
        logger.exception('Failed to send escalation email for notification %s', notification.id)


def _build_default_message(po: 'PurchaseOrder', reason: str) -> str:
    """Build a default escalation message for a PO."""
    if reason in ('email_delivery_failed', 'EMAIL_DELIVERY_FAILED'):
        return (
            f'Email delivery for PO-{po.id} has permanently failed after 3 retries.\n'
            f'Supplier: {po.supplier.name if po.supplier else "Unknown"}\n'
            f'SKU: {po.sku.code if po.sku else "Unknown"}\n'
            f'Quantity: {po.quantity}\n'
            f'Action required: Please contact the supplier manually.\n'
            f'Timestamp: {timezone.now().isoformat()}'
        )
    if reason in ('supplier_timeout', 'SUPPLIER_TIMEOUT'):
        return (
            f'Supplier has not responded to PO-{po.id} within 48 hours.\n'
            f'Supplier: {po.supplier.name if po.supplier else "Unknown"}\n'
            f'SKU: {po.sku.code if po.sku else "Unknown"}\n'
            f'Quantity: {po.quantity}\n'
            f'Action required: Please follow up with the supplier.\n'
            f'Timestamp: {timezone.now().isoformat()}'
        )
    return (
        f'Escalation for PO-{po.id}: {reason}\n'
        f'Action required: Please review.\n'
        f'Timestamp: {timezone.now().isoformat()}'
    )
