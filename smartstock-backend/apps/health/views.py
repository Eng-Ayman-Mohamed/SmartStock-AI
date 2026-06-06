from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import connections
from django.core.cache import cache


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        db_ok = False
        redis_ok = False

        try:
            connections['default'].cursor()
            db_ok = True
        except Exception:
            pass

        try:
            cache.set('health_check', 'ok', timeout=5)
            val = cache.get('health_check')
            redis_ok = val == 'ok'
        except Exception:
            pass

        all_ok = db_ok and redis_ok
        status_code = 200 if all_ok else 503

        return Response(
            {
                'status': 'ok' if all_ok else 'degraded',
                'database': 'connected' if db_ok else 'disconnected',
                'redis': 'connected' if redis_ok else 'disconnected',
            },
            status=status_code,
        )
