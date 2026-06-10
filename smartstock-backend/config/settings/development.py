from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'  # noqa: F405

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
