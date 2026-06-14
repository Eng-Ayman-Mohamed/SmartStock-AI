import logging
import os

from django.core.exceptions import ImproperlyConfigured

REQUIRED_ENV_VARS = [
    'OPENAI_API_KEY',
    'COHERE_API_KEY',
    'DJANGO_SECRET_KEY',
    'DATABASE_URL',
    'REDIS_URL',
]

OPTIONAL_ENV_VARS = {
    'LANGFUSE_HOST': 'https://cloud.langfuse.com',
    'LANGFUSE_PUBLIC_KEY': '',
    'LANGFUSE_SECRET_KEY': '',
    'LANGFUSE_DAILY_TOKEN_BUDGET': '1000000',
    'ALLOWED_HOSTS': 'localhost,127.0.0.1',
    'CORS_ALLOWED_ORIGINS': 'http://localhost:5173',
    'CSRF_TRUSTED_ORIGINS': '',
    'CLOUDINARY_URL': '',
    'DJANGO_DEBUG': 'False',
    'EMAIL_HOST': '',
    'EMAIL_HOST_USER': '',
    'EMAIL_HOST_PASSWORD': '',
    'EMAIL_PORT': '587',
    'DEFAULT_FROM_EMAIL': 'noreply@smartstock.ai',
    'ESCALATION_RECIPIENT_EMAILS': '',
}

logger = logging.getLogger(__name__)


def _mask_value(value):
    if len(value) <= 4:
        return '***'
    return value[:2] + '***' + value[-2:]


def validate_required_env_vars():
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]

    if missing:
        raise ImproperlyConfigured(
            'Missing required environment variables: ' + ', '.join(sorted(missing))
        )

    for var in REQUIRED_ENV_VARS:
        logger.info('[CONFIG] %s: %s', var, _mask_value(os.getenv(var)))

    for var, default in OPTIONAL_ENV_VARS.items():
        value = os.getenv(var, default)
        logger.info('[CONFIG] %s: %s', var, value)
