from rest_framework import serializers

from .models import ChatConversation, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'engine', 'mode', 'sources', 'created_at']
        read_only_fields = fields


class ChatConversationListSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatConversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'message_count']
        read_only_fields = fields

    def get_message_count(self, obj):
        return getattr(obj, '_msg_count', obj.messages.count())


class ChatConversationDetailSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatConversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'messages']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ChatConversationCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False, default='New Conversation')


class ChatConversationRenameSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
