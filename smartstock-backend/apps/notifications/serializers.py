from rest_framework import serializers

from .models import Notification


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
        return getattr(obj, '_is_read', False)


class NotificationListSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'type', 'severity', 'title', 'created_at', 'is_read']

    def get_is_read(self, obj):
        return getattr(obj, '_is_read', False)
