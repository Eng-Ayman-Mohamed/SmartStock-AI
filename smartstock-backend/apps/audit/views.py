from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.authentication.permissions import IsAdminOnly, IsManagerOrAbove, IsViewerOrAbove
from config.schema_serializers import ErrorResponseSerializer

from .models import AgentRun, AuditLog
from .serializers import AgentRunSerializer, AuditLogSerializer


class AuditLogView(ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event', 'user', 'entity_type']

    @extend_schema(
        responses={
            200: AuditLogSerializer(many=True),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
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


@extend_schema_view(
    list=extend_schema(
        responses={
            200: AgentRunSerializer(many=True),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
        },
        tags=['audit'],
    ),
    retrieve=extend_schema(
        responses={
            200: AgentRunSerializer,
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Agent run not found'
            ),
        },
        tags=['audit'],
    ),
    create=extend_schema(
        responses={
            201: AgentRunSerializer,
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description='Manager or above only'
            ),
        },
        tags=['audit'],
    ),
    update=extend_schema(
        responses={
            200: AgentRunSerializer,
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description='Manager or above only'
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Agent run not found'
            ),
        },
        tags=['audit'],
    ),
    partial_update=extend_schema(
        responses={
            200: AgentRunSerializer,
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description='Manager or above only'
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Agent run not found'
            ),
        },
        tags=['audit'],
    ),
    destroy=extend_schema(
        responses={
            204: None,
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(
                response=ErrorResponseSerializer, description='Manager or above only'
            ),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Agent run not found'
            ),
        },
        tags=['audit'],
    ),
)
class AgentRunViewSet(viewsets.ModelViewSet):
    queryset = AgentRun.objects.all()
    serializer_class = AgentRunSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsViewerOrAbove()]
        return [IsManagerOrAbove()]
