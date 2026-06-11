from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.forecasting.views import ForecastBySKUView
from apps.inventory.views import NLQueryEndpointView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/forecasting/', include('apps.forecasting.urls')),
    path('api/forecasts/<str:sku>/', ForecastBySKUView.as_view(), name='forecast-by-sku-alias'),
    path('api/purchasing/', include('apps.purchasing.urls')),
    path('api/health/', include('apps.health.urls')),
    path('api/ai/', include('apps.ingestion.urls')),
    path('api/ai/nlquery/', NLQueryEndpointView.as_view(), name='nl-query-endpoint'),
    path('api/audit/logs/', include('apps.audit.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
