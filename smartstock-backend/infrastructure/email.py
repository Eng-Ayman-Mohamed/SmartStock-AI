import logging
import smtplib
import uuid

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)

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

NON_RETRIABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    smtplib.SMTPAuthenticationError,
    smtplib.SMTPRecipientsRefused,
    smtplib.SMTPSenderRefused,
)

RETRY_COUNTDOWN: list[int] = [30, 120, 600]
MAX_RETRIES = 3


class EmailService:
    """Unified email service — sends all emails through Celery for retry/audit."""

    def send(self, subject: str, message: str, recipient: str) -> dict:
        """Queue an email for async delivery via Celery. Returns task info."""
        task = send_email_task.delay(subject=subject, body=message, recipient=recipient)
        logger.info('Email queued: task_id=%s recipient=%s', task.id, recipient)
        return {'task_id': task.id, 'status': 'queued', 'recipient': recipient}

    def send_sync(self, subject: str, message: str, recipient: str) -> dict:
        """Send email synchronously (for urgent/system emails that cannot wait)."""
        return _send_email_sync(subject, message, recipient)


def _send_email_sync(subject: str, body: str, recipient: str) -> dict:
    """Synchronous email send with audit logging."""
    message_id = f'email-{uuid.uuid4().hex[:12]}'
    try:
        msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartstock.ai'),
            to=[recipient],
        )
        msg.send(fail_silently=False)
        logger.info('Email sent: %s to %s', message_id, recipient)
        return {'status': 'sent', 'message_id': message_id, 'recipient': recipient}
    except Exception as exc:
        logger.exception('Email %s to %s failed: %s', message_id, recipient, exc)
        return {
            'status': 'failed',
            'message_id': message_id,
            'recipient': recipient,
            'error': str(exc),
        }


@shared_task(
    bind=True,
    max_retries=MAX_RETRIES,
    default_retry_delay=30,
    acks_late=True,
)
def send_email_task(self, subject: str, body: str, recipient: str) -> dict:
    """Celery task for email delivery with retry and exponential backoff."""
    message_id = f'email-{uuid.uuid4().hex[:12]}'
    retry_number = self.request.retries

    try:
        logger.info(
            'Sending email %s to %s (attempt %d/%d)',
            message_id,
            recipient,
            retry_number + 1,
            MAX_RETRIES + 1,
        )
        msg = EmailMessage(
            subject=subject,
            body=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartstock.ai'),
            to=[recipient],
        )
        msg.send(fail_silently=False)
        logger.info('Email sent: %s to %s', message_id, recipient)
        return {
            'status': 'sent',
            'message_id': message_id,
            'recipient': recipient,
            'attempts': retry_number + 1,
        }

    except NON_RETRIABLE_EXCEPTIONS as exc:
        logger.error('Email %s to %s permanently failed: %s', message_id, recipient, exc)
        return {
            'status': 'permanently_failed',
            'message_id': message_id,
            'recipient': recipient,
            'error': str(exc),
        }

    except RETRIABLE_EXCEPTIONS as exc:
        next_retry = retry_number + 1
        if next_retry < MAX_RETRIES:
            countdown = RETRY_COUNTDOWN[min(retry_number, len(RETRY_COUNTDOWN) - 1)]
            logger.warning(
                'Email %s to %s failed (attempt %d/%d). Retrying in %ds',
                message_id,
                recipient,
                next_retry,
                MAX_RETRIES + 1,
                countdown,
            )
            raise self.retry(exc=exc, countdown=countdown)
        logger.error(
            'Email %s to %s permanently failed after %d retries', message_id, recipient, MAX_RETRIES
        )
        return {
            'status': 'permanently_failed',
            'message_id': message_id,
            'recipient': recipient,
            'error': str(exc),
        }

    except Exception as exc:
        logger.error('Email %s to %s unexpected error: %s', message_id, recipient, exc)
        if retry_number < MAX_RETRIES:
            countdown = RETRY_COUNTDOWN[min(retry_number, len(RETRY_COUNTDOWN) - 1)]
            raise self.retry(exc=exc, countdown=countdown)
        return {
            'status': 'permanently_failed',
            'message_id': message_id,
            'recipient': recipient,
            'error': str(exc),
        }


@shared_task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=30, acks_late=True)
def send_verification_email_task(self, email: str, verify_url: str, first_name: str = '') -> dict:
    """Send email verification link via Celery with retry."""
    subject = 'Verify your SmartStock AI account'
    name = first_name or email
    body = (
        f'Hi {name},\n\n'
        f'Thank you for signing up for SmartStock AI.\n\n'
        f'Please verify your email address by clicking the link below:\n\n'
        f'{verify_url}\n\n'
        f'This link will expire in 24 hours.\n\n'
        f'If you did not create an account, you can safely ignore this email.\n\n'
        f'— The SmartStock AI Team'
    )
    return send_email_task(subject=subject, body=body, recipient=email)


@shared_task(bind=True, max_retries=MAX_RETRIES, default_retry_delay=30, acks_late=True)
def send_alert_email_task(self, subject: str, body: str) -> dict:
    """Send alert email to all configured escalation recipients via Celery."""
    recipients = getattr(settings, 'ESCALATION_RECIPIENT_EMAILS', [])
    if not recipients:
        logger.warning('No ESCALATION_RECIPIENT_EMAILS configured; skipping alert email')
        return {'status': 'skipped', 'reason': 'no_recipients'}
    results = []
    for recipient in recipients:
        result = send_email_task.delay(subject=subject, body=body, recipient=recipient)
        results.append({'recipient': recipient, 'task_id': result.id})
    return {'status': 'queued', 'results': results}
