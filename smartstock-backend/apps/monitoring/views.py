import logging
import time

from django.http import HttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsAdminOnly, IsManagerOrAbove
from config.schema_serializers import ErrorResponseSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    responses={
        200: OpenApiResponse(
            response={'type': 'string', 'format': 'text'},
            description='Prometheus metrics in text format',
        ),
    },
    tags=['monitoring'],
    auth=[],
)
class MetricsView(APIView):
    """Expose Prometheus metrics at /metrics/.

    Intentionally unauthenticated for Prometheus scraping.
    In production, restrict access via network policy or reverse proxy.
    """

    permission_classes = []
    authentication_classes = []

    def get(self, request):
        return HttpResponse(
            generate_latest(),
            content_type=CONTENT_TYPE_LATEST,
        )


@extend_schema(
    responses={
        200: inline_serializer(
            'DashboardBannersResponse',
            {
                'status': serializers.CharField(),
                'data': inline_serializer(
                    'DashboardBannerItem',
                    {
                        'id': serializers.IntegerField(),
                        'title': serializers.CharField(),
                        'message': serializers.CharField(),
                        'level': serializers.CharField(),
                        'created_at': serializers.DateTimeField(allow_null=True),
                    },
                    many=True,
                ),
            },
        ),
        401: OpenApiResponse(
            response=ErrorResponseSerializer, description='Authentication required'
        ),
    },
    tags=['monitoring'],
)
class DashboardBannersView(APIView):
    """Return active (non-dismissed) dashboard banners."""

    permission_classes = [IsAuthenticated]

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


@extend_schema(
    request=None,
    responses={
        200: OpenApiResponse(
            response={
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'success'},
                    'message': {'type': 'string', 'example': 'Banner dismissed'},
                },
            },
            description='Banner dismissed',
        ),
        401: OpenApiResponse(
            response=ErrorResponseSerializer, description='Authentication required'
        ),
        403: OpenApiResponse(response=ErrorResponseSerializer, description='Manager or above only'),
        404: OpenApiResponse(response=ErrorResponseSerializer, description='Banner not found'),
    },
    tags=['monitoring'],
)
class DismissBannerView(APIView):
    """Dismiss a dashboard banner."""

    permission_classes = [IsAuthenticated, IsManagerOrAbove]

    def post(self, request, banner_id):
        from .models import DashboardBanner

        try:
            banner = DashboardBanner.objects.get(id=banner_id)
            banner.dismissed = True
            banner.save(update_fields=['dismissed'])
            return Response({'status': 'success', 'message': 'Banner dismissed'})
        except DashboardBanner.DoesNotExist:
            return Response({'status': 'error', 'message': 'Banner not found'}, status=404)


@extend_schema(
    responses={
        200: inline_serializer(
            'AlertEventsResponse',
            {
                'status': serializers.CharField(),
                'data': inline_serializer(
                    'AlertEventItem',
                    {
                        'id': serializers.IntegerField(),
                        'rule_name': serializers.CharField(),
                        'severity': serializers.CharField(),
                        'status': serializers.CharField(),
                        'triggered_value': serializers.FloatField(),
                        'message': serializers.CharField(),
                        'email_sent': serializers.BooleanField(),
                        'dashboard_notified': serializers.BooleanField(),
                        'created_at': serializers.DateTimeField(),
                        'resolved_at': serializers.DateTimeField(allow_null=True),
                    },
                    many=True,
                ),
            },
        ),
        401: OpenApiResponse(
            response=ErrorResponseSerializer, description='Authentication required'
        ),
    },
    tags=['monitoring'],
)
class AlertEventsView(APIView):
    """Return recent alert events."""

    permission_classes = [IsAuthenticated]

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


@extend_schema(
    request=None,
    responses={
        200: inline_serializer(
            'TriggerAlertEvaluationResponse',
            {
                'status': serializers.CharField(),
                'data': serializers.DictField(child=serializers.JSONField()),
            },
        ),
        401: OpenApiResponse(
            response=ErrorResponseSerializer, description='Authentication required'
        ),
        403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
    },
    tags=['monitoring'],
)
class TriggerAlertEvaluationView(APIView):
    """Manually trigger alert evaluation (admin only)."""

    permission_classes = [IsAuthenticated, IsAdminOnly]

    def post(self, request):
        from .alerts import evaluate_all_alerts

        results = evaluate_all_alerts()
        return Response({'status': 'success', 'data': results})


@extend_schema(
    responses={
        200: inline_serializer(
            'EvaluationMetricsResponse',
            {
                'status': serializers.CharField(),
                'data': inline_serializer(
                    'EvaluationMetricsData',
                    {
                        'precision_at_5': serializers.FloatField(),
                        'faithfulness': serializers.FloatField(),
                        'total_queries': serializers.IntegerField(),
                        'successful_queries': serializers.IntegerField(),
                        'evaluation_timestamp': serializers.FloatField(),
                        'duration_ms': serializers.IntegerField(),
                    },
                ),
            },
        ),
        401: OpenApiResponse(
            response=ErrorResponseSerializer, description='Authentication required'
        ),
        403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
    },
    tags=['monitoring'],
)
class EvaluationMetricsView(APIView):
    """Expose evaluation metrics (admin only)."""

    permission_classes = [IsAuthenticated, IsAdminOnly]

    def get(self, request):
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
