from celery.result import AsyncResult
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsAdminOnly, IsViewerOrAbove
from config.schema_serializers import ErrorResponseSerializer

from .models import ForecastResult
from .serializers import ForecastResultSerializer
from .services import ForecastingService
from .tasks import run_forecasting_agent


@extend_schema_view(
    list=extend_schema(
        responses={
            200: ForecastResultSerializer(many=True),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['forecasting'],
    ),
    retrieve=extend_schema(
        responses={
            200: ForecastResultSerializer,
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Forecast not found'
            ),
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
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='No forecast found for SKU'
            ),
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
        service = ForecastingService()
        rows = list(service.get_forecast_by_sku_code_or_id(sku))
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


class RunForecastView(APIView):
    permission_classes = [IsAdminOnly]

    @extend_schema(
        request=inline_serializer(
            'RunForecastInput',
            {
                'sku_ids': serializers.ListField(
                    child=serializers.IntegerField(),
                    required=False,
                    help_text='Optional list of SKU IDs to forecast. Forecasts all if omitted.',
                ),
            },
        ),
        responses={
            202: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string', 'example': 'forecast_triggered'},
                        'job_id': {'type': 'string', 'example': 'fc8a2b7e-...'},
                    },
                },
                description='Forecast agent dispatched as async Celery task',
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            400: OpenApiResponse(
                response=ErrorResponseSerializer, description='Invalid sku_ids format'
            ),
        },
        examples=[
            OpenApiExample(
                'Run Forecast Request',
                value={'sku_ids': [1, 2, 3]},
                request_only=True,
            ),
        ],
        tags=['forecasting'],
    )
    def post(self, request):
        sku_ids = request.data.get('sku_ids')
        if sku_ids is not None:
            if not isinstance(sku_ids, list) or not all(type(s) is int for s in sku_ids):
                return Response(
                    {
                        'status': 'error',
                        'error': 'ValidationError',
                        'message': 'sku_ids must be a list of integers.',
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        task = run_forecasting_agent.delay(sku_ids=sku_ids)
        return Response(
            {'status': 'forecast_triggered', 'job_id': task.id},
            status=status.HTTP_202_ACCEPTED,
        )


class ForecastDashboardView(APIView):
    permission_classes = [IsViewerOrAbove]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response={'type': 'object'},
                description='Dashboard data with aggregated forecast metrics',
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
        },
        tags=['forecasting'],
    )
    def get(self, request):
        service = ForecastingService()
        data = service.get_dashboard_data()
        return Response(data)


class ForecastJobStatusView(APIView):
    permission_classes = [IsAdminOnly]

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'job_id': {'type': 'string'},
                        'status': {'type': 'string'},
                        'result': {'type': 'object'},
                    },
                },
                description='Job status and result if completed',
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
        },
        tags=['forecasting'],
    )
    def get(self, request, job_id):
        result = AsyncResult(job_id)
        response_data = {
            'job_id': job_id,
            'status': result.status,
        }
        if result.status == 'SUCCESS':
            response_data['result'] = result.result
        elif result.status == 'FAILURE':
            response_data['error'] = str(result.result)
        return Response(response_data)
