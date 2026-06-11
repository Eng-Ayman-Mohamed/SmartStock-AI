from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AgentRunViewSet, AuditLogView

router = DefaultRouter()
router.register(r'agent-runs', AgentRunViewSet, basename='agent-run')

urlpatterns = [
    path('', AuditLogView.as_view(), name='audit-log-list'),
    path('', include(router.urls)),
]
