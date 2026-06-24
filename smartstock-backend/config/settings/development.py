from .base import *  # noqa: F403

DEBUG = True

DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'  # noqa: F405

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Log slow or problematic DB queries to the console
LOGGING['loggers']['django.db.backends'] = {  # noqa: F405
    'handlers': ['console'],
    'level': 'WARNING',
}
