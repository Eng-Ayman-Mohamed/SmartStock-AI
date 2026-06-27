import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import CustomUser, EmailVerificationToken

logger = logging.getLogger(__name__)

VERIFICATION_TOKEN_TTL_HOURS = 24


def generate_verification_token(user: CustomUser) -> EmailVerificationToken:
    EmailVerificationToken.objects.filter(user=user).delete()
    return EmailVerificationToken.objects.create(
        user=user,
        expires_at=timezone.now() + timedelta(hours=VERIFICATION_TOKEN_TTL_HOURS),
    )


def send_verification_email(user: CustomUser, token: EmailVerificationToken) -> None:
    """Queue verification email via Celery for retry/audit. Falls back to sync."""
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    verify_url = f'{frontend_url}/verify-email?token={token.token}'

    try:
        from infrastructure.email import send_verification_email_task

        send_verification_email_task.delay(
            email=user.email,
            verify_url=verify_url,
            first_name=user.first_name or '',
        )
        logger.info('Verification email queued for %s', user.email)
    except Exception:
        logger.exception(
            'Failed to queue verification email for %s; falling back to sync', user.email
        )
        _send_verification_email_sync(user, verify_url)


def _send_verification_email_sync(user: CustomUser, verify_url: str) -> None:
    """Synchronous fallback for verification emails."""
    from django.core.mail import send_mail

    subject = 'Verify your SmartStock AI account'
    name = user.first_name or user.email
    message = (
        f'Hi {name},\n\n'
        f'Thank you for signing up for SmartStock AI.\n\n'
        f'Please verify your email address by clicking the link below:\n\n'
        f'{verify_url}\n\n'
        f'This link will expire in {VERIFICATION_TOKEN_TTL_HOURS} hours.\n\n'
        f'If you did not create an account, you can safely ignore this email.\n\n'
        f'— The SmartStock AI Team'
    )
    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@smartstock.ai')
        logger.info('Sending verification email from=%s to=%s (sync)', from_email, user.email)
        send_mail(
            subject=subject, message=message, from_email=from_email, recipient_list=[user.email]
        )
        logger.info('Verification email sent to %s (sync)', user.email)
    except Exception:
        logger.exception('Failed to send verification email to %s (sync)', user.email)
        raise


def verify_email_token(token_str: str) -> tuple[bool, str, int]:
    """Verify an email verification token.

    Returns (success, message, http_status).
    Idempotent: already-verified accounts return 200, not 400.
    """
    try:
        verification = EmailVerificationToken.objects.select_related('user').get(token=token_str)
    except EmailVerificationToken.DoesNotExist:
        return False, 'Invalid or expired verification link.', 400

    if verification.is_expired():
        verification.delete()
        return False, 'Verification link has expired. Please request a new one.', 400

    user = verification.user

    if user.email_verified:
        verification.delete()
        return True, 'Email already verified. You can now log in.', 200

    user.email_verified = True
    user.save(update_fields=['email_verified'])
    verification.delete()
    return True, 'Email verified successfully. You can now log in.', 200
