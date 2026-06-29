import logging
import os
import ssl
from datetime import timedelta
from pathlib import Path

import cloudinary
import cloudinary.api
import cloudinary.uploader
import dj_database_url
from celery.schedules import crontab

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    _is_test = 'test' in os.environ.get('DJANGO_SETTINGS_MODULE', '')
    if _is_test:
        SECRET_KEY = 'test-secret-key-not-for-production'
    else:
        from django.core.exceptions import ImproperlyConfigured

        raise ImproperlyConfigured('DJANGO_SECRET_KEY environment variable is required.')

DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

# Security: Determine if we're in a production environment
# In production, only set to False if explicitly configured
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development').lower()
# Detect production: explicit ENVIRONMENT var, or Railway's own env vars,
# or DEBUG being False (set in production.py which loads after this).
IS_PRODUCTION = (
    ENVIRONMENT == 'production'
    or bool(os.environ.get('RAILWAY_STATIC_URL'))
    or bool(os.environ.get('RAILWAY_PUBLIC_DOMAIN'))
)

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
    'rest_framework_simplejwt.token_blacklist',
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
    'apps.notifications',
    'apps.monitoring',
    'apps.ai.apps.AIConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # CSRF disabled — JWT-only auth (no session cookies, no CSRF tokens sent)
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.audit.middleware.AuditMiddleware',
    'apps.monitoring.middleware.PrometheusMetricsMiddleware',
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
        default=os.environ.get('DATABASE_URL', ''),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

if not DATABASES.get('default') or not DATABASES['default'].get('ENGINE'):
    _db_user = os.environ.get('DB_USER')
    _db_password = os.environ.get('DB_PASSWORD')
    _db_host = os.environ.get('DB_HOST', 'localhost')
    _db_port = os.environ.get('DB_PORT', '5432')
    _db_name = os.environ.get('DB_NAME')

    if not all([_db_user, _db_password, _db_name]):
        if 'test' not in os.environ.get('DJANGO_SETTINGS_MODULE', ''):
            from django.core.exceptions import ImproperlyConfigured

            raise ImproperlyConfigured(
                'Database credentials required. Set DATABASE_URL or '
                'DB_USER, DB_PASSWORD, DB_NAME environment variables.'
            )
        else:
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': _db_name,
                'USER': _db_user,
                'PASSWORD': _db_password,
                'HOST': _db_host,
                'PORT': _db_port,
                'CONN_MAX_AGE': 600,
                'CONN_HEALTH_CHECKS': True,
            }
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

AUTHENTICATION_BACKENDS = [
    'apps.authentication.authentication_backends.EmailAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

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
                    'refresh': {
                        'type': 'string',
                        'description': 'JWT refresh token (also set as HttpOnly cookie)',
                    },
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
        {'name': 'notifications', 'description': 'Notification center endpoints'},
        {'name': 'monitoring', 'description': 'Dashboard banners, alerts, and evaluation metrics'},
    ],
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
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
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'user': '100/minute',
        'login': '5/minute',
        'ai': '10/minute',
        'nlquery': '10/minute',
        'health': '60/minute',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=3),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_COOKIE': 'refresh_token',
    'TOKEN_OBTAIN_SERIALIZER': 'apps.authentication.serializers.CustomTokenObtainPairSerializer',
}
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://localhost:3000'
).split(',')
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
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ['Content-Disposition']

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': os.environ.get('REDIS_IGNORE_EXCEPTIONS', 'True').lower()
            == 'true',
        },
        'KEY_PREFIX': 'smartstock',
        'TIMEOUT': 300,
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {},
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '')

cloudinary.config(cloudinary_url=CLOUDINARY_URL)

LANGFUSE_PUBLIC_KEY = os.environ.get('LANGFUSE_PUBLIC_KEY', '')
LANGFUSE_SECRET_KEY = os.environ.get('LANGFUSE_SECRET_KEY', '')
LANGFUSE_HOST = os.environ.get('LANGFUSE_HOST', 'https://cloud.langfuse.com')
LANGFUSE_ALERT_THRESHOLDS = {
    'llm_latency_p95_ms_warning': 3000,
    'llm_api_error_rate_critical': 0.01,
    'daily_token_budget_alert': int(os.environ.get('LANGFUSE_DAILY_TOKEN_BUDGET', '1000000')),
    'agent_success_rate_minimum': 0.80,
}

# Validate required env vars at module level (not in AppConfig.ready) to catch
# missing configuration early, before any app attempts to use them.
if not os.environ.get('CI'):
    from config.validators import validate_required_env_vars  # noqa: E402

    try:
        validate_required_env_vars()
    except Exception:
        logger.warning('Environment validation skipped — settings may be incomplete.')

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')

_broker_url = os.environ.get('REDIS_URL') or os.environ.get(
    'CELERY_BROKER_URL', 'redis://localhost:6379/0'
)
_result_url = os.environ.get('REDIS_URL') or os.environ.get(
    'CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'
)

CELERY_BROKER_URL = _broker_url
CELERY_RESULT_BACKEND = _result_url

# SSL cert verification for rediss:// (Upstash, etc.)
# Accepts: 'none' (CERT_NONE), 'optional' (CERT_OPTIONAL), 'required' (CERT_REQUIRED)
# Default 'required' validates standard CA certs; set REDIS_SSL_CERT_REQS=none for self-signed.
_ssl_mode = os.environ.get('REDIS_SSL_CERT_REQS', 'required').lower()
_ssl_map = {
    'none': ssl.CERT_NONE,
    'optional': ssl.CERT_OPTIONAL,
    'required': ssl.CERT_REQUIRED,
}
_ssl_cert_reqs = _ssl_map.get(_ssl_mode, ssl.CERT_REQUIRED)

CELERY_BROKER_USE_SSL = (
    {'ssl_cert_reqs': _ssl_cert_reqs} if _broker_url.startswith('rediss://') else None
)

CELERY_REDIS_BACKEND_USE_SSL = (
    {'ssl_cert_reqs': _ssl_cert_reqs} if _result_url.startswith('rediss://') else None
)

CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Reduce Redis request churn (Upstash free-tier: 500K/month)
CELERY_BROKER_POOL_LIMIT = 10
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 200

CELERY_BEAT_SCHEDULE = {
    'purge-audit-logs-daily': {
        'task': 'apps.audit.tasks.purge_old_audit_logs',
        'schedule': timedelta(hours=24),
    },
    'check-supplier-timeouts': {
        'task': 'apps.purchasing.timeout_tasks.check_supplier_timeouts',
        'schedule': 3600,  # every hour
    },
    'evaluate-monitoring-alerts': {
        'task': 'apps.monitoring.tasks.evaluate_all_alerts_task',
        'schedule': 300,  # every 5 minutes
    },
    'run-forecast-daily': {
        'task': 'apps.forecasting.tasks.run_forecasting_agent',
        'schedule': crontab(hour=2, minute=0),  # 02:00 UTC daily
    },
    'daily-evaluation-metrics': {
        'task': 'apps.monitoring.evaluation_tasks.run_daily_evaluation_task',
        'schedule': crontab(hour=3, minute=0),  # 03:00 UTC daily
    },
    'cleanup-stale-agent-runs': {
        'task': 'apps.monitoring.tasks.cleanup_stale_agent_runs',
        'schedule': 300,  # every 5 minutes
    },
    'archive-old-agent-runs-daily': {
        'task': 'apps.monitoring.tasks.archive_old_agent_runs',
        'schedule': crontab(hour=4, minute=0),  # 04:00 UTC daily
    },
    'check-overdue-suppliers': {
        'task': 'apps.purchasing.tasks.check_overdue_suppliers',
        'schedule': 3600,  # every hour
    },
}

ESCALATION_RECIPIENT_EMAILS = [
    email.strip()
    for email in os.environ.get('ESCALATION_RECIPIENT_EMAILS', '').split(',')
    if email.strip()
]
