from rest_framework import serializers
from .models import Notification, UserNotification


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'type',
            'severity',
            'title',
            'message',
            'metadata',
            'is_read',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_read(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        user_notification = obj.user_notifications.filter(user=request.user).first()
        return user_notification.is_read if user_notification else False


class NotificationListSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'type', 'severity', 'title', 'created_at', 'is_read']

    def get_is_read(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        user_notification = obj.user_notifications.filter(user=request.user).first()
        return user_notification.is_read if user_notification else False
