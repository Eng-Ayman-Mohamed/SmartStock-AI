from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
