from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ForecastResult
from .serializers import ForecastResultSerializer
from .services import ForecastingService


class ForecastResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ForecastResult.objects.select_related('sku__product').all()
    serializer_class = ForecastResultSerializer


class TriggerForecastView(APIView):
    def post(self, request):
        service = ForecastingService()
        result = service.run_forecast()
        return Response({"status": "forecast triggered", "result": result})
