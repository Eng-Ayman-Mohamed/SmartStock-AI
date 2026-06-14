from django.urls import path

from .views import HealthCheckView, ReadinessView

urlpatterns = [
    path('live/', HealthCheckView.as_view(), name='health-live'),
    path('ready/', ReadinessView.as_view(), name='health-ready'),
]
