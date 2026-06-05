from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ForecastResult
from .serializers import ForecastResultSerializer
from .services import ForecastingService
from django.db.models import Min
from rest_framework.permissions import IsAuthenticated
from apps.inventory.models import StockLevel
import datetime


class ForecastResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ForecastResult.objects.select_related('sku__product').all()
    serializer_class = ForecastResultSerializer


class TriggerForecastView(APIView):
    def post(self, request):
        service = ForecastingService()
        result = service.run_forecast()
        return Response({"status": "forecast triggered", "result": result})

class ForecastDashboardView(APIView):
    permission_classes = []

    def get(self, request):
        today = datetime.date.today()
        horizon = today + datetime.timedelta(days=30)

        # fetch next 30 days of forecasts, newest model_version per sku/date
        rows = (
            ForecastResult.objects
            .filter(forecast_date__gte=today, forecast_date__lte=horizon)
            .select_related('sku__product', 'sku__stock_level')
            .order_by('sku', 'forecast_date')
        )

        # group rows by SKU
        skus_map = {}
        for row in rows:
            sku_id = row.sku.id
            if sku_id not in skus_map:
                stock = getattr(row.sku, 'stock_level', None)
                skus_map[sku_id] = {
                    "id": row.sku.code,
                    "name": row.sku.product.name,
                    "threshold": stock.reorder_point if stock else 0,
                    "current_stock": stock.quantity if stock else 0,
                    "supplier": "—",  # extend when supplier model added
                    "lead_time_days": 0,
                    "days": [],
                }
            skus_map[sku_id]["days"].append({
                "date": row.forecast_date.isoformat(),
                "demand": round(row.predicted_quantity, 2),
            })

        return Response({"skus": list(skus_map.values())})