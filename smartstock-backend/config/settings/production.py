from .base import *

DEBUG = False

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

ALLOWED_HOSTS = list({*ALLOWED_HOSTS, '.up.railway.app'})

_extra_csrf = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
_default_csrf = 'https://smart-stock-dev.vercel.app'
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in (_extra_csrf or _default_csrf).split(',') if o.strip()
]

if not os.environ.get('CORS_ALLOWED_ORIGINS'):
    CORS_ALLOWED_ORIGINS = ['https://smart-stock-dev.vercel.app']
else:
    CORS_ALLOWED_ORIGINS = [o.strip() for o in os.environ['CORS_ALLOWED_ORIGINS'].split(',') if o.strip()]

CORS_ALLOW_CREDENTIALS = True

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@smartstock.ai')
