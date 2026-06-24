import os  # noqa: F811

from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'  # noqa: F405

# Use real SMTP if credentials are provided, otherwise fall back to console
if os.environ.get('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
    EMAIL_USE_TLS = True
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'owael20003@gmail.com')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://smart-stock-dev.vercel.app')

# Log slow or problematic DB queries to the console
LOGGING['loggers']['django.db.backends'] = {  # noqa: F405
    'handlers': ['console'],
    'level': 'WARNING',
}
