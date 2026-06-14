from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'forecasts', views.ForecastResultViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('results/<str:sku>/', views.ForecastBySKUView.as_view(), name='forecast-by-sku'),
    path('run/', views.RunForecastView.as_view(), name='run-forecast'),
    path('run/<str:job_id>/', views.ForecastJobStatusView.as_view(), name='forecast-job-status'),
    path('dashboard/', views.ForecastDashboardView.as_view(), name='forecast-dashboard'),
]
