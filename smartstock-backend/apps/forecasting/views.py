from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.authentication.permissions import IsViewerOrAbove, IsAdminOnly
from .models import ForecastResult
from .serializers import ForecastResultSerializer
from .services import ForecastingService
from django.db.models import Min
from apps.inventory.models import StockLevel
import datetime


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
            ForecastResult.objects
            .filter(**filters)
            .select_related('sku__product')
            .order_by('forecast_date')[:30]
        )
        if not rows:
            return Response(
                {"status": "error", "message": f"No forecast found for SKU {sku}."},
                status=status.HTTP_404_NOT_FOUND,
            )

        first = rows[0]
        return Response({
            "sku_id": first.sku_id,
            "sku_code": first.sku.code,
            "product_name": first.sku.product.name,
            "forecasts": [
                {
                    "date": row.forecast_date.isoformat(),
                    "predicted_quantity": row.predicted_quantity,
                    "lower_bound": row.lower_bound,
                    "upper_bound": row.upper_bound,
                    "mae": row.mae,
                    "mape": row.mape,
                    "model_version": row.model_version,
                }
                for row in rows
            ],
        })


class TriggerForecastView(APIView):
    permission_classes = [IsAdminOnly]

    def post(self, request):
        sku_id = request.data.get('sku_id')
        service = ForecastingService()
        result = service.run_forecast(sku_id=sku_id)
        return Response({"status": "forecast_triggered", "forecasts": result})


class ForecastDashboardView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request):
        today = datetime.date.today()
        horizon = today + datetime.timedelta(days=30)

        rows = (
            ForecastResult.objects
            .filter(forecast_date__gte=today, forecast_date__lte=horizon)
            .select_related('sku__product', 'sku__stock_level')
            .order_by('sku', 'forecast_date')
        )

        skus_map = {}
        for row in rows:
            sku_id = row.sku.id
            if sku_id not in skus_map:
                stock = getattr(row.sku, 'stock_level', None)
                skus_map[sku_id] = {
                    "id": row.sku.code,
                    "name": row.sku.product.name,
                    "threshold": stock.reorder_point if stock else 0,
                    "current_stock": stock.quantity_on_hand if stock else 0,
                    "supplier": "—",
                    "lead_time_days": 0,
                    "mae": row.mae,
                    "mape": row.mape,
                    "model_version": row.model_version,
                    "days": [],
                }
            skus_map[sku_id]["days"].append({
                "date": row.forecast_date.isoformat(),
                "demand": round(row.predicted_quantity, 2),
            })

        return Response({"skus": list(skus_map.values())})
