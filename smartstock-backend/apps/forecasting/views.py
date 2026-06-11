
from django.core.cache import cache
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsAdminOnly, IsViewerOrAbove

from .models import ForecastResult
from .serializers import ForecastResultSerializer
from .services import ForecastingService


class ForecastResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ForecastResult.objects.select_related('sku__product').all()
    serializer_class = ForecastResultSerializer
    permission_classes = [IsViewerOrAbove]


class ForecastBySKUView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request, sku):
        filters = {'sku__code__iexact': sku}
        if str(sku).isdigit():
            filters = {'sku_id': int(sku)}

        rows = list(
            ForecastResult.objects.filter(**filters).select_related('sku__product').order_by('forecast_date')[:30]
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

    def post(self, request):
        sku_id = request.data.get('sku_id')
        service = ForecastingService()
        result = service.run_forecast(sku_id=sku_id)
        cache.delete_pattern('forecast_dashboard_*')
        return Response({'status': 'forecast_triggered', 'forecasts': result})


class ForecastDashboardView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request):
        service = ForecastingService()
        data = service.get_dashboard_data()
        return Response(data)
