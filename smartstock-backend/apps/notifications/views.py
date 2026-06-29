from django.core.cache import cache
from django.db.models import BooleanField, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsViewerOrAbove
from config.schema_serializers import ErrorResponseSerializer

from .models import Notification, UserNotification
from .serializers import NotificationListSerializer, NotificationSerializer


@extend_schema_view(
    list=extend_schema(
        responses={
            200: NotificationListSerializer(many=True),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
        },
        tags=['notifications'],
        summary='List notifications',
    ),
    retrieve=extend_schema(
        responses={
            200: NotificationSerializer,
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Notification not found'
            ),
        },
        tags=['notifications'],
        summary='Get notification',
    ),
    create=extend_schema(
        request=NotificationSerializer,
        responses={
            201: NotificationSerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description='Bad request'),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
        },
        tags=['notifications'],
        summary='Create notification',
    ),
    update=extend_schema(
        request=NotificationSerializer,
        responses={
            200: NotificationSerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description='Bad request'),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Notification not found'
            ),
        },
        tags=['notifications'],
        summary='Update notification',
    ),
    partial_update=extend_schema(
        request=NotificationSerializer,
        responses={
            200: NotificationSerializer,
            400: OpenApiResponse(response=ErrorResponseSerializer, description='Bad request'),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Notification not found'
            ),
        },
        tags=['notifications'],
        summary='Partially update notification',
    ),
)
class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsViewerOrAbove]
    http_method_names = ['get', 'post', 'patch']

    def get_queryset(self):
        """Return only notifications associated with the current user."""
        qs = (
            Notification.objects.filter(user_notifications__user=self.request.user)
            .prefetch_related('user_notifications')
            .distinct()
        )
        notif_type = self.request.query_params.get('type')
        if notif_type:
            qs = qs.filter(type=notif_type)
        severity = self.request.query_params.get('severity')
        if severity:
            qs = qs.filter(severity=severity)
        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer

    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {'status': {'type': 'string', 'example': 'success'}},
                },
                description='Notification marked as read',
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Notification not found'
            ),
        },
        tags=['notifications'],
        summary='Mark notification as read',
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        user_notification, _ = UserNotification.objects.get_or_create(
            user=request.user, notification=notification
        )
        user_notification.is_read = True
        user_notification.read_at = timezone.now()
        user_notification.save()
        cache.delete(f'unread_count_{request.user.id}')
        return Response({'status': 'success'})

    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {'status': {'type': 'string', 'example': 'success'}},
                },
                description='All notifications marked as read',
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
        },
        tags=['notifications'],
        summary='Mark all notifications as read',
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        UserNotification.objects.filter(
            user=request.user,
            is_read=False,
        ).update(is_read=True, read_at=timezone.now())
        cache.delete(f'unread_count_{request.user.id}')
        return Response({'status': 'success'})

    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {'status': {'type': 'string', 'example': 'success'}},
                },
                description='Notification dismissed',
            ),
            401: OpenApiResponse(
                response=ErrorResponseSerializer, description='Authentication required'
            ),
            403: OpenApiResponse(response=ErrorResponseSerializer, description='Forbidden'),
            404: OpenApiResponse(
                response=ErrorResponseSerializer, description='Notification not found'
            ),
        },
        tags=['notifications'],
        summary='Dismiss notification',
    )
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        notification = self.get_object()
        UserNotification.objects.filter(user=request.user, notification=notification).delete()
        cache.delete(f'unread_count_{request.user.id}')
        return Response({'status': 'success'})


@extend_schema(
    responses={
        200: OpenApiResponse(
            response={
                'type': 'object',
                'properties': {
                    'count': {'type': 'integer', 'description': 'Number of unread notifications'}
                },
            },
            description='Unread notification count',
        ),
        401: OpenApiResponse(
            response=ErrorResponseSerializer, description='Authentication required'
        ),
    },
    tags=['notifications'],
    summary='Get unread notification count',
)
class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cache_key = f'unread_count_{request.user.id}'
        count = cache.get(cache_key)
        if count is None:
            count = Notification.objects.filter(
                user_notifications__user=request.user,
                user_notifications__is_read=False,
            ).count()
            cache.set(cache_key, count, 60)
        return Response({'count': count})
