from django.core.cache import cache
from django.db import connections
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView


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


class HealthCheckView(APIView):
    """Liveness probe — always 200 as long as the process is alive.

    Use this to confirm the container is up and Django can serve requests.
    Body includes dep status for diagnostics, but the status code never
    drops to 503, so Railway (and similar orchestrators) keep routing traffic.
    """

    authentication_classes = []
    permission_classes = []

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'example': 'ok'},
                        'database': {'type': 'string', 'example': 'connected'},
                        'redis': {'type': 'string', 'example': 'connected'},
                    },
                },
                description='Service is healthy',
            ),
        },
        tags=['health'],
        auth=[],
    )
    def get(self, request):
        db_ok = _check_database()
        redis_ok = _check_redis()
        return Response(
            {
                'status': 'ok',
                'database': 'connected' if db_ok else 'disconnected',
                'redis': 'connected' if redis_ok else 'disconnected',
            },
            status=200,
        )


class ReadinessView(APIView):
    """Readiness probe — 200 only when all required dependencies are reachable.

    Use this as a stricter check for orchestrators that want to drain traffic
    when a dependency is down. Returns 503 + diagnostic body when DB or Redis
    is unreachable so callers can react.
    """

    authentication_classes = []
    permission_classes = []

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'example': 'ok'},
                        'database': {'type': 'string', 'example': 'connected'},
                        'redis': {'type': 'string', 'example': 'connected'},
                    },
                },
                description='All dependencies available',
            ),
            503: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'example': 'degraded'},
                        'database': {'type': 'string'},
                        'redis': {'type': 'string'},
                    },
                },
                description='One or more dependencies unavailable',
            ),
        },
        tags=['health'],
        auth=[],
    )
    def get(self, request):
        db_ok = _check_database()
        redis_ok = _check_redis()
        all_ok = db_ok and redis_ok
        return Response(
            {
                'status': 'ok' if all_ok else 'degraded',
                'database': 'connected' if db_ok else 'disconnected',
                'redis': 'connected' if redis_ok else 'disconnected',
            },
            status=200 if all_ok else 503,
        )
