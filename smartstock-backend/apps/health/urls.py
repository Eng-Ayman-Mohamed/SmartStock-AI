from django.urls import path

from .views import FullHealthView, HealthCheckView, ReadinessView

urlpatterns = [
    path('live/', HealthCheckView.as_view(), name='health-live'),
    path('ready/', ReadinessView.as_view(), name='health-ready'),
    path('full/', FullHealthView.as_view(), name='health-full'),
]
