from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.permissions import IsViewerOrAbove

from .models import Notification, UserNotification
from .serializers import NotificationListSerializer, NotificationSerializer


@extend_schema_view(
    list=extend_schema(tags=["notifications"], summary="List notifications"),
    retrieve=extend_schema(tags=["notifications"], summary="Get notification"),
)
class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsViewerOrAbove]
    http_method_names = ["get", "post", "patch"]

    def get_queryset(self):
        qs = Notification.objects.all()
        notif_type = self.request.query_params.get("type")
        if notif_type:
            qs = qs.filter(type=notif_type)
        severity = self.request.query_params.get("severity")
        if severity:
            qs = qs.filter(severity=severity)
        date_from = self.request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        date_to = self.request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return NotificationListSerializer
        return NotificationSerializer

    @extend_schema(tags=["notifications"], summary="Mark notification as read")
    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        user_notification, _ = UserNotification.objects.get_or_create(
            user=request.user, notification=notification
        )
        user_notification.is_read = True
        user_notification.read_at = timezone.now()
        user_notification.save()
        return Response({"status": "success"})

    @extend_schema(tags=["notifications"], summary="Mark all notifications as read")
    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        unread_ids = Notification.objects.filter(
            user_notifications__user=request.user,
            user_notifications__is_read=False,
        ).values_list("id", flat=True)
        UserNotification.objects.filter(
            user=request.user, notification_id__in=unread_ids
        ).update(is_read=True, read_at=timezone.now())
        return Response({"status": "success"})

    @extend_schema(tags=["notifications"], summary="Dismiss notification")
    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        notification = self.get_object()
        UserNotification.objects.filter(
            user=request.user, notification=notification
        ).delete()
        return Response({"status": "success"})


@extend_schema(tags=["notifications"], summary="Get unread notification count")
class UnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            user_notifications__user=request.user,
            user_notifications__is_read=False,
        ).count()
        return Response({"count": count})
