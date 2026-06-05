from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/forecasting/', include('apps.forecasting.urls')),
    path('api/purchasing/', include('apps.purchasing.urls')),
]
