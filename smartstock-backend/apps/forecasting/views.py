from django.core.cache import cache
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, extend_schema_view, inline_serializer
from rest_framework import serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsAdminOnly, IsViewerOrAbove
from config.schema_serializers import ErrorResponseSerializer

from .models import ForecastResult
from .serializers import ForecastResultSerializer
from .services import ForecastingService


@extend_schema_view(
    list=extend_schema(
        responses={
            200: ForecastResultSerializer(many=True),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['forecasting'],
    ),
    retrieve=extend_schema(
        responses={
            200: ForecastResultSerializer,
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='Forecast not found'),
        },
        tags=['forecasting'],
    ),
)
class ForecastResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ForecastResult.objects.select_related('sku__product').all()
    serializer_class = ForecastResultSerializer
    permission_classes = [IsViewerOrAbove]


class ForecastBySKUView(APIView):
    permission_classes = [IsViewerOrAbove]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'sku_id': {'type': 'integer'},
                        'sku_code': {'type': 'string'},
                        'product_name': {'type': 'string'},
                        'forecasts': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'date': {'type': 'string', 'format': 'date'},
                                    'predicted_quantity': {'type': 'number'},
                                    'lower_bound': {'type': 'number'},
                                    'upper_bound': {'type': 'number'},
                                    'mae': {'type': 'number'},
                                    'mape': {'type': 'number'},
                                    'model_version': {'type': 'string'},
                                },
                            },
                        },
                    },
                },
                description='Forecast for a specific SKU',
            ),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(response=ErrorResponseSerializer, description='No forecast found for SKU'),
        },
        examples=[
            OpenApiExample(
                'Forecast Response',
                value={
                    'sku_id': 1,
                    'sku_code': 'SKU001',
                    'product_name': 'Widget A',
                    'forecasts': [
                        {
                            'date': '2026-07-01',
                            'predicted_quantity': 150.0,
                            'lower_bound': 120.0,
                            'upper_bound': 180.0,
                            'mae': 5.2,
                            'mape': 3.5,
                            'model_version': 'prophet-1.1',
                        }
                    ],
                },
                response_only=True,
            ),
        ],
        tags=['forecasting'],
    )
    def get(self, request, sku):
        filters = {'sku__code__iexact': sku}
        if str(sku).isdigit():
            filters = {'sku_id': int(sku)}

        rows = list(
            ForecastResult.objects.filter(**filters)
            .select_related('sku__product')
            .order_by('forecast_date')[:30]
        )
        if not rows:
            return Response(
                {'status': 'error', 'message': f'No forecast found for SKU {sku}.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        first = rows[0]
        return Response(
            {
                'sku_id': first.sku_id,
                'sku_code': first.sku.code,
                'product_name': first.sku.product.name,
                'forecasts': [
                    {
                        'date': row.forecast_date.isoformat(),
                        'predicted_quantity': row.predicted_quantity,
                        'lower_bound': row.lower_bound,
                        'upper_bound': row.upper_bound,
                        'mae': row.mae,
                        'mape': row.mape,
                        'model_version': row.model_version,
                    }
                    for row in rows
                ],
            }
        )


class TriggerForecastView(APIView):
    permission_classes = [IsAdminOnly]

    @extend_schema(
        request=inline_serializer(
            'TriggerForecastInput',
            {
                'sku_id': serializers.IntegerField(
                    required=False,
                    help_text='Optional SKU ID to forecast for a specific product',
                ),
            },
        ),
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'example': 'forecast_triggered'},
                        'forecasts': {'type': 'array', 'items': {'type': 'object'}},
                    },
                },
                description='Forecast triggered successfully',
            ),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
        },
        examples=[
            OpenApiExample(
                'Trigger Forecast Request',
                value={'sku_id': 1},
                request_only=True,
            ),
        ],
        tags=['forecasting'],
    )
    def post(self, request):
        sku_id = request.data.get('sku_id')
        service = ForecastingService()
        result = service.run_forecast(sku_id=sku_id)
        cache.delete_pattern('forecast_dashboard_*')
        return Response({'status': 'forecast_triggered', 'forecasts': result})


class ForecastDashboardView(APIView):
    permission_classes = [IsViewerOrAbove]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response={'type': 'object'},
                description='Dashboard data with aggregated forecast metrics',
            ),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
        },
        tags=['forecasting'],
    )
    def get(self, request):
        service = ForecastingService()
        data = service.get_dashboard_data()
        return Response(data)
