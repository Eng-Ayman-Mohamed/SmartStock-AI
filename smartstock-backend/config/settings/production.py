import logging
import os  # noqa: F811

from .base import *  # noqa: F403

logger = logging.getLogger(__name__)

DEBUG = False

# ---------------------------------------------------------------------------
# HTTPS / HSTS
# ---------------------------------------------------------------------------
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ---------------------------------------------------------------------------
# Cookies
# ---------------------------------------------------------------------------
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# ---------------------------------------------------------------------------
# Additional security headers
# ---------------------------------------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# ---------------------------------------------------------------------------
# Hosts — Render uses `.onrender.com` domains
# ---------------------------------------------------------------------------
_extra_hosts = os.environ.get('ALLOWED_HOSTS', '')
_extra_host_list = [h.strip() for h in _extra_hosts.split(',') if h.strip()] if _extra_hosts else []
ALLOWED_HOSTS = list(
    {
        *ALLOWED_HOSTS,  # noqa: F405
        '.onrender.com',
        'smartstock-api.onrender.com',
        *_extra_host_list,
    }
)

# ---------------------------------------------------------------------------
# CSRF / CORS — prefer env vars, fallback to Vercel production domain
# ---------------------------------------------------------------------------
_extra_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
_default_csrf = 'https://smartstock-ai.vercel.app,https://smart-stock-dev.vercel.app'
CSRF_TRUSTED_ORIGINS = [o.strip() for o in (_extra_csrf or _default_csrf).split(',') if o.strip()]

_cors_env = os.environ.get('CORS_ALLOWED_ORIGINS', '')
_default_cors = 'https://smartstock-ai.vercel.app,https://smart-stock-dev.vercel.app'
_cors_value = _cors_env or _default_cors
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_value.split(',') if o.strip()]
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Email (SendGrid / SMTP)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'apikey')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@smartstock.ai')

# ---------------------------------------------------------------------------
# Production error handling — never expose stack traces
# ---------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.environ.get('DJANGO_LOG_LEVEL', 'WARNING'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'WARNING'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
