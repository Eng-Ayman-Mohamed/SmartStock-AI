from rest_framework import serializers

from .models import AgentRun, AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'


class AgentRunSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.FloatField(read_only=True, default=None)

    class Meta:
        model = AgentRun
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
