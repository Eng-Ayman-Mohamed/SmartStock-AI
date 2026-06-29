import os  # noqa: F811

from .base import *  # noqa: F403

DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() in ('true', '1', 'yes')

SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'false').lower() in ('true', '1', 'yes')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]
if not ALLOWED_HOSTS:
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured('ALLOWED_HOSTS environment variable is required in production.')

if 'healthcheck.railway.app' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('healthcheck.railway.app')
if 'backend' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('backend')

_extra_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS')
if not _extra_csrf:
    raise ImproperlyConfigured('CSRF_TRUSTED_ORIGINS environment variable is required in production.')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _extra_csrf.split(',') if o.strip()]

_cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS')
if not _cors_origins:
    raise ImproperlyConfigured('CORS_ALLOWED_ORIGINS environment variable is required in production.')
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in _cors_origins.split(',') if o.strip()
]

if not DEBUG:
    _cors_insecure = [
        o for o in CORS_ALLOWED_ORIGINS if 'localhost' in o or '127.0.0.1' in o or o == '*'
    ]
    if _cors_insecure:
        import logging as _logging

        _logging.getLogger('config.settings.production').warning(
            'Removing insecure CORS origins from production: %s', _cors_insecure
        )
        CORS_ALLOWED_ORIGINS = [o for o in CORS_ALLOWED_ORIGINS if o not in _cors_insecure]

CORS_ALLOW_CREDENTIALS = True

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').lower() in ('true', '1', 'yes')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@smartstock.ai')
FRONTEND_URL = os.environ.get('FRONTEND_URL')
if not FRONTEND_URL:
    raise ImproperlyConfigured('FRONTEND_URL environment variable is required in production.')

# Use separate Redis (Upstash) for Django cache — keeps REDIS_URL dedicated to Celery broker
# Fall back to REDIS_URL if CACHE_REDIS_URL is not set; use django_redis for
# IGNORE_EXCEPTIONS support so cache failures don't crash the worker.
_cache_url = os.environ.get('CACHE_REDIS_URL') or os.environ.get('REDIS_URL', '')
if _cache_url:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': _cache_url,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'IGNORE_EXCEPTIONS': True,
            },
            'KEY_PREFIX': 'smartstock',
            'TIMEOUT': 300,
        }
    }
else:
    import logging as _logging

    _logging.getLogger('config.settings.production').warning(
        'CACHE_REDIS_URL and REDIS_URL not set — using local memory cache'
    )
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
