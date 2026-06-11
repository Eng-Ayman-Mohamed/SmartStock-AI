from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.authentication.permissions import IsAdminOnly, IsManagerOrAbove, IsViewerOrAbove

from .models import AgentRun, AuditLog
from .serializers import AgentRunSerializer, AuditLogSerializer


class AuditLogView(ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event', 'user', 'entity_type']

    def get_queryset(self):
        qs = super().get_queryset()
        user_id = self.request.query_params.get('user_id')
        if user_id:
            qs = qs.filter(user_id=user_id)
        created_after = self.request.query_params.get('created_after')
        if created_after:
            qs = qs.filter(timestamp__gte=created_after)
        created_before = self.request.query_params.get('created_before')
        if created_before:
            qs = qs.filter(timestamp__lte=created_before)
        return qs


class AgentRunViewSet(viewsets.ModelViewSet):
    queryset = AgentRun.objects.all()
    serializer_class = AgentRunSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsViewerOrAbove()]
        return [IsManagerOrAbove()]
