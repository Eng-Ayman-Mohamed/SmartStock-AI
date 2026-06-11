import logging
import os
from datetime import timedelta
from pathlib import Path

import cloudinary
import cloudinary.api
import cloudinary.uploader
import dj_database_url

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-change-me-in-production')

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'core.apps.CoreConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
    'drf_spectacular',
    'django.contrib.postgres',
    'apps.health',
    'apps.authentication',
    'apps.inventory',
    'apps.forecasting',
    'apps.purchasing',
    'apps.audit.apps.AuditConfig',
    'apps.ingestion.apps.IngestionConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.audit.middleware.AuditMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default='postgres://{user}:{password}@{host}:{port}/{name}'.format(
            user=os.environ.get('DB_USER', 'smartstock'),
            password=os.environ.get('DB_PASSWORD', 'smartstock'),
            host=os.environ.get('DB_HOST', 'localhost'),
            port=os.environ.get('DB_PORT', '5432'),
            name=os.environ.get('DB_NAME', 'smartstock'),
        ),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'authentication.CustomUser'

SPECTACULAR_SETTINGS = {
    'TITLE': 'SmartStock AI API',
    'DESCRIPTION': 'Inventory forecasting and management API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
    },
    'AUTHENTICATION_WHITELIST': [],
    'SECURITY': [
        {'BearerJWT': []},
    ],

    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'BearerJWT': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
                'description': 'Enter your JWT access token obtained from /api/auth/login/',
            },
        },
        'schemas': {
            'AuthSuccessResponse': {
                'type': 'object',
                'properties': {
                    'access': {'type': 'string', 'description': 'JWT access token'},
                    'refresh': {'type': 'string', 'description': 'JWT refresh token (also set as HttpOnly cookie)'},
                },
            },
        },
    },
    'TAGS': [
        {'name': 'auth', 'description': 'Authentication and user management'},
        {'name': 'inventory', 'description': 'Products, SKUs, stock levels, suppliers, categories'},
        {'name': 'forecasting', 'description': 'Demand forecasting and predictions'},
        {'name': 'purchasing', 'description': 'Purchase orders and supplier management'},
        {'name': 'ai', 'description': 'AI-powered NL queries and document ingestion'},
        {'name': 'health', 'description': 'Service health and readiness probes'},
        {'name': 'audit', 'description': 'Audit logs and activity tracking'},
    ],
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': (
        'config.renderers.ResponseEnvelopeRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'config.exception_handler.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': (
        'core.throttles.SAFEAnonRateThrottle',
        'core.throttles.SAFEUserRateThrottle',
        'core.throttles.AIRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'user': '100/minute',
        'login': '5/minute',
        'ai': '10/minute',
        'nlquery': '10/minute',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_COOKIE': 'refresh_token',
    'AUTH_COOKIE_HTTP_ONLY': True,
    'AUTH_COOKIE_SECURE': os.environ.get('DJANGO_DEBUG', 'True') != 'True',
    'AUTH_COOKIE_SAMESITE': 'Strict',
    'TOKEN_OBTAIN_SERIALIZER': 'apps.authentication.serializers.CustomTokenObtainPairSerializer',
}
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:5173').split(',')
CORS_ALLOW_HEADERS = [
    'accept',
    'authorization',
    'content-type',
    'x-requested-with',
    'x-csrftoken',
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': 'smartstock',
        'TIMEOUT': 300,
    }
}

CACHE_MIDDLEWARE_SECONDS = 300

CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '')

cloudinary.config(cloudinary_url=CLOUDINARY_URL)

# Validate required env vars at module level (not in AppConfig.ready) to catch
# missing configuration early, before any app attempts to use them.
if not os.environ.get('CI'):
    from config.validators import validate_required_env_vars  # noqa: E402

    try:
        validate_required_env_vars()
    except Exception:
        logger.warning('Environment validation skipped — settings may be incomplete.')
