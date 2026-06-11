from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.authentication.permissions import IsAdminOnly
from config.schema_serializers import ErrorResponseSerializer

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogView(ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event', 'user', 'entity_type']

    @extend_schema(
        responses={
            200: AuditLogSerializer(many=True),
            401: OpenApiResponse(response=ErrorResponseSerializer, description='Authentication required'),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Admin only'),
            429: OpenApiResponse(response=ErrorResponseSerializer, description='Too many requests'),
        },
        tags=['audit'],
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

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
