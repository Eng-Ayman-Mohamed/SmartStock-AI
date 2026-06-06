from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'forecasts', views.ForecastResultViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('trigger/', views.TriggerForecastView.as_view(), name='trigger-forecast'),
    path('dashboard/', views.ForecastDashboardView.as_view(), name='forecast-dashboard'),
]
