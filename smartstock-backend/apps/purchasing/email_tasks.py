import logging
import smtplib
import uuid
from typing import Any

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

logger = logging.getLogger(__name__)

# Transient SMTP errors that warrant retry
RETRIABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    smtplib.SMTPServerDisconnected,
    smtplib.SMTPConnectError,
    smtplib.SMTPHeloError,
    smtplib.SMTPResponseException,
    smtplib.SMTPException,
    ConnectionError,
    TimeoutError,
    OSError,
)

# Permanent errors that should NOT be retried
NON_RETRIABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    smtplib.SMTPAuthenticationError,
    smtplib.SMTPRecipientsRefused,
    smtplib.SMTPSenderRefused,
)

# Exponential delay schedule in seconds: 30s, 2min, 10min
RETRY_COUNTDOWN: list[int] = [30, 120, 600]
MAX_RETRIES: int = 3


def is_retriable(exc: Exception) -> bool:
    """Return True if the exception represents a transient failure."""
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
    """Send email with automatic retry for transient failures.

    Retry schedule: 30s, 2min, 10min.
    After 3 failed retries the delivery is marked permanently failed
    and an escalation notification is triggered.

    Args:
        subject: Email subject line.
        body: Email body text.
        recipient: Recipient email address.
        po_id: Optional purchase order ID for tracking.
        message_id: Optional unique message identifier.

    Returns:
        dict with 'status' ('sent' | 'permanently_failed') and metadata.
    """
    if not message_id:
        message_id = f'email-{uuid.uuid4().hex[:12]}'

    retry_number = self.request.retries
    try:
        logger.info(
            'Sending email %s to %s (attempt %d/%d, po_id=%s)',
            message_id,
            recipient,
            retry_number + 1,
            MAX_RETRIES + 1,
            po_id,
        )

        msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartstock.ai'),
            to=[recipient],
        )
        msg.send(fail_silently=False)

        logger.info(
            'Email sent successfully: %s to %s (po_id=%s)',
            message_id,
            recipient,
            po_id,
        )
        return {
            'status': 'sent',
            'message_id': message_id,
            'recipient': recipient,
            'po_id': po_id,
            'attempts': retry_number + 1,
        }

    except NON_RETRIABLE_EXCEPTIONS as exc:
        logger.error(
            'Email %s to %s failed permanently (non-retriable): %s (po_id=%s)',
            message_id,
            recipient,
            exc,
            po_id,
        )
        _trigger_escalation(po_id, str(exc))
        return {
            'status': 'permanently_failed',
            'message_id': message_id,
            'recipient': recipient,
            'po_id': po_id,
            'error': str(exc),
            'attempts': 1,
        }

    except RETRIABLE_EXCEPTIONS as exc:
        next_retry = retry_number + 1
        if next_retry < MAX_RETRIES:
            countdown = (
                RETRY_COUNTDOWN[retry_number]
                if retry_number < len(RETRY_COUNTDOWN)
                else RETRY_COUNTDOWN[-1]
            )
            logger.warning(
                'Email %s to %s failed (attempt %d/%d): %s. Scheduling retry %d in %ds (po_id=%s)',
                message_id,
                recipient,
                next_retry,
                MAX_RETRIES + 1,
                exc,
                next_retry + 1,
                countdown,
                po_id,
            )
            raise self.retry(exc=exc, countdown=countdown)
        else:
            logger.error(
                'Email delivery permanently failed after %d retries: '
                'email_id=%s recipient=%s po_id=%s exception=%s',
                MAX_RETRIES,
                message_id,
                recipient,
                po_id,
                exc,
            )
            _trigger_escalation(po_id, str(exc))
            return {
                'status': 'permanently_failed',
                'message_id': message_id,
                'recipient': recipient,
                'po_id': po_id,
                'error': str(exc),
                'attempts': MAX_RETRIES + 1,
            }

    except Exception as exc:
        logger.error(
            'Email %s to %s failed with unexpected error: %s (po_id=%s)',
            message_id,
            recipient,
            exc,
            po_id,
        )
        if is_retriable(exc) and retry_number < MAX_RETRIES:
            countdown = (
                RETRY_COUNTDOWN[retry_number]
                if retry_number < len(RETRY_COUNTDOWN)
                else RETRY_COUNTDOWN[-1]
            )
            raise self.retry(exc=exc, countdown=countdown)
        _trigger_escalation(po_id, str(exc))
        return {
            'status': 'permanently_failed',
            'message_id': message_id,
            'recipient': recipient,
            'po_id': po_id,
            'error': str(exc),
            'attempts': retry_number + 1,
        }


def _trigger_escalation(po_id: int | None, error_reason: str) -> None:
    """Trigger an escalation notification for a permanently failed email."""
    if po_id is None:
        return
    try:
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
        from apps.audit.signals import log_event

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
