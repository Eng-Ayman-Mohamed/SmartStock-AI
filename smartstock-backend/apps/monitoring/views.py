import logging

from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class MetricsView(APIView):
    """Expose Prometheus metrics at /metrics/."""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        from django.http import HttpResponse
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

        return HttpResponse(
            generate_latest(),
            content_type=CONTENT_TYPE_LATEST,
        )


class DashboardBannersView(APIView):
    """Return active (non-dismissed) dashboard banners."""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        from .models import DashboardBanner

        banners = DashboardBanner.objects.filter(dismissed=False)[:20]
        data = [
            {
                'id': b.id,
                'title': b.title,
                'message': b.message,
                'level': b.level,
                'created_at': b.created_at.isoformat() if b.created_at else None,
            }
            for b in banners
        ]
        return Response({'status': 'success', 'data': data})


class DismissBannerView(APIView):
    """Dismiss a dashboard banner."""

    permission_classes = []
    authentication_classes = []

    def post(self, request, banner_id):
        from .models import DashboardBanner

        try:
            banner = DashboardBanner.objects.get(id=banner_id)
            banner.dismissed = True
            banner.save(update_fields=['dismissed'])
            return Response({'status': 'success', 'message': 'Banner dismissed'})
        except DashboardBanner.DoesNotExist:
            return Response({'status': 'error', 'message': 'Banner not found'}, status=404)


class AlertEventsView(APIView):
    """Return recent alert events."""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        from .models import AlertEvent

        events = AlertEvent.objects.select_related('rule').order_by('-created_at')[:50]
        data = [
            {
                'id': e.id,
                'rule_name': e.rule.name,
                'severity': e.rule.severity,
                'status': e.status,
                'triggered_value': e.triggered_value,
                'message': e.message,
                'email_sent': e.email_sent,
                'dashboard_notified': e.dashboard_notified,
                'created_at': e.created_at.isoformat(),
                'resolved_at': e.resolved_at.isoformat() if e.resolved_at else None,
            }
            for e in events
        ]
        return Response({'status': 'success', 'data': data})


class TriggerAlertEvaluationView(APIView):
    """Manually trigger alert evaluation (for testing/debugging)."""

    permission_classes = []
    authentication_classes = []

    def post(self, request):
        from .alerts import evaluate_all_alerts

        results = evaluate_all_alerts()
        return Response({'status': 'success', 'data': results})


class EvaluationMetricsView(APIView):
    """Expose evaluation metrics (Precision@5, Faithfulness, etc.)."""

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        import time

        from ai.evaluation.metrics import evaluate_golden_dataset, log_scores_to_langfuse

        start = time.time()
        results = evaluate_golden_dataset()
        duration_ms = (time.time() - start) * 1000

        log_scores_to_langfuse(results, duration_ms)

        return Response(
            {
                'status': 'success',
                'data': {
                    'precision_at_5': results.get('precision_at_5', 0.0),
                    'faithfulness': results.get('faithfulness', 0.0),
                    'total_queries': results.get('total_queries', 0),
                    'successful_queries': results.get('successful_queries', 0),
                    'evaluation_timestamp': time.time(),
                    'duration_ms': round(duration_ms),
                },
            }
        )
