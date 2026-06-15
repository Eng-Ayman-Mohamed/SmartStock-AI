from django.urls import path

from .views import (
    AlertEventsView,
    DashboardBannersView,
    DismissBannerView,
    EvaluationMetricsView,
    TriggerAlertEvaluationView,
)

# Monitoring API endpoints — mounted at /api/monitoring/ via config/urls.py
urlpatterns = [
    path('banners/', DashboardBannersView.as_view(), name='dashboard-banners'),
    path('banners/<int:banner_id>/dismiss/', DismissBannerView.as_view(), name='dismiss-banner'),
    path('alerts/', AlertEventsView.as_view(), name='alert-events'),
    path('alerts/evaluate/', TriggerAlertEvaluationView.as_view(), name='trigger-alert-evaluation'),
    path('evaluation/', EvaluationMetricsView.as_view(), name='evaluation-metrics'),
]
