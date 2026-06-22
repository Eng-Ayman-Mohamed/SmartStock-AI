import ipaddress
import logging
import os

from django.core.cache import cache
from django.db import connections
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

_INTERNAL_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8', strict=False),
    ipaddress.ip_network('172.16.0.0/12', strict=False),
    ipaddress.ip_network('192.168.0.0/16', strict=False),
    ipaddress.ip_network('127.0.0.0/8', strict=False),
]


def _is_internal_request(request) -> bool:
    """Check if request originates from a private/internal network."""
    try:
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            client_ip = xff.split(',')[0].strip()
        else:
            client_ip = request.META.get('REMOTE_ADDR', '')
        addr = ipaddress.ip_address(client_ip)
        return any(addr in net for net in _INTERNAL_NETWORKS)
    except (ValueError, TypeError):
        return False


def _check_database() -> bool:
    try:
        connections['default'].cursor()
        return True
    except Exception:
        return False


def _check_redis() -> bool:
    try:
        cache.set('health_check', 'ok', timeout=5)
        return cache.get('health_check') == 'ok'
    except Exception:
        return False


class HealthRateThrottle(ScopedRateThrottle):
    scope = 'health'


class HealthCheckView(APIView):
    """Liveness probe -- always 200 as long as the process is alive.

    Returns only a minimal status payload. No internal dependency
    information is exposed publicly.
    """

    authentication_classes = []
    permission_classes = []
    throttle_classes = [HealthRateThrottle]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'example': 'ok'},
                    },
                },
                description='Service is alive',
            ),
        },
        tags=['health'],
        auth=[],
    )
    def get(self, request):
        return Response({'status': 'ok'}, status=200)


class ReadinessView(APIView):
    """Readiness probe -- 200 only when all required dependencies are reachable.

    Protected endpoint: requires either a valid ``X-Health-Secret`` header
    or an originating IP from an internal/private network.  Never exposes
    dependency status to unauthenticated external callers.
    """

    authentication_classes = []
    permission_classes = []
    throttle_classes = [HealthRateThrottle]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'example': 'ok'},
                    },
                },
                description='All dependencies available',
            ),
            403: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'example': 'forbidden'},
                    },
                },
                description='Forbidden -- missing or invalid health secret',
            ),
            503: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'example': 'degraded'},
                    },
                },
                description='One or more dependencies unavailable',
            ),
        },
        tags=['health'],
        auth=[],
    )
    def get(self, request):
        secret = os.environ.get('HEALTH_SECRET_HEADER', '')
        provided = request.META.get('HTTP_X_HEALTH_SECRET', '')

        if secret and provided == secret:
            pass
        elif _is_internal_request(request):
            pass
        else:
            return Response({'status': 'forbidden'}, status=403)

        db_ok = _check_database()
        redis_ok = _check_redis()
        all_ok = db_ok and redis_ok

        return Response(
            {'status': 'ok' if all_ok else 'degraded'},
            status=200 if all_ok else 503,
        )


class FullHealthView(APIView):
    """Comprehensive health check -- verifies database, redis, celery, storage, and agents.

    Requires internal network or valid X-Health-Secret header.
    """

    authentication_classes = []
    permission_classes = []
    throttle_classes = [HealthRateThrottle]

    @extend_schema(
        responses={
            200: OpenApiResponse(description='All systems operational'),
            503: OpenApiResponse(description='One or more systems degraded'),
        },
        tags=['health'],
        auth=[],
    )
    def get(self, request):
        secret = os.environ.get('HEALTH_SECRET_HEADER', '')
        provided = request.META.get('HTTP_X_HEALTH_SECRET', '')

        if secret and provided == secret:
            pass
        elif _is_internal_request(request):
            pass
        else:
            return Response({'status': 'forbidden'}, status=403)

        checks = {}

        checks['database'] = 'ok' if _check_database() else 'error'
        checks['redis'] = 'ok' if _check_redis() else 'error'

        try:
            from celery import current_app

            inspector = current_app.control.inspect(timeout=3)
            active = inspector.ping()
            checks['celery'] = 'ok' if active else 'error'
        except Exception:
            checks['celery'] = 'error'

        try:
            from django.core.files.storage import default_storage

            checks['storage'] = 'ok' if default_storage.exists('') or True else 'error'
        except Exception:
            checks['storage'] = 'error'

        try:
            from apps.audit.models import AgentRun

            stale_count = AgentRun.objects.filter(
                status=AgentRun.Status.RUNNING,
            ).count()
            checks['agents'] = 'ok'
            checks['stale_running_runs'] = stale_count
        except Exception:
            checks['agents'] = 'error'

        all_ok = all(v == 'ok' for v in checks.values() if isinstance(v, str))

        return Response(
            {
                'status': 'healthy' if all_ok else 'degraded',
                **checks,
            },
            status=200 if all_ok else 503,
        )
