import uuid

from core.base_repository import BaseRepository

from .models import ChatConversation, ChatMessage


class ConversationRepository(BaseRepository):
    """Repository for ChatConversation model."""

    def get_by_id(self, id: uuid.UUID):
        return ChatConversation.objects.get(pk=id)

    def get_all(self):
        return ChatConversation.objects.all()

    def create(self, data: dict):
        return ChatConversation.objects.create(**data)

    def update(self, id: uuid.UUID, data: dict):
        ChatConversation.objects.filter(pk=id).update(**data)
        return self.get_by_id(id)

    def delete(self, id: uuid.UUID):
        ChatConversation.objects.filter(pk=id).delete()

    def list_for_user(self, user):
        return ChatConversation.objects.filter(user=user).order_by('-updated_at')

    def get_with_messages(self, id: uuid.UUID, user):
        return (
            ChatConversation.objects.filter(pk=id, user=user).prefetch_related('messages').first()
        )


class ChatMessageRepository(BaseRepository):
    """Repository for ChatMessage model."""

    def get_by_id(self, id: uuid.UUID):
        return ChatMessage.objects.get(pk=id)

    def get_all(self):
        return ChatMessage.objects.all()

    def create(self, data: dict):
        return ChatMessage.objects.create(**data)

    def update(self, id: uuid.UUID, data: dict):
        ChatMessage.objects.filter(pk=id).update(**data)
        return self.get_by_id(id)

    def delete(self, id: uuid.UUID):
        ChatMessage.objects.filter(pk=id).delete()

    def get_history(self, conversation_id: uuid.UUID, limit: int = 20):
        return list(
            ChatMessage.objects.filter(conversation_id=conversation_id).order_by('-created_at')[
                :limit
            ]
        )
