import logging
import uuid

from .models import ChatConversation
from .repositories import ChatMessageRepository, ConversationRepository

logger = logging.getLogger(__name__)

HISTORY_LIMIT = 20


class ConversationService:
    """Business logic for chat conversations."""

    def __init__(self):
        self._conversation_repo = ConversationRepository()
        self._message_repo = ChatMessageRepository()

    def list_conversations(self, user):
        return self._conversation_repo.list_for_user(user)

    def get_conversation(self, conversation_id: uuid.UUID, user):
        conversation = self._conversation_repo.get_with_messages(conversation_id, user)
        if not conversation:
            raise ValueError('Conversation not found.')
        return conversation

    def create_conversation(self, user, title: str = 'New Conversation'):
        return self._conversation_repo.create({'user': user, 'title': title})

    def delete_conversation(self, conversation_id: uuid.UUID, user):
        conversation = self._conversation_repo.get_with_messages(conversation_id, user)
        if not conversation:
            raise ValueError('Conversation not found.')
        self._conversation_repo.delete(conversation_id)

    def rename_conversation(self, conversation_id: uuid.UUID, user, title: str):
        conversation = self._conversation_repo.get_with_messages(conversation_id, user)
        if not conversation:
            raise ValueError('Conversation not found.')
        return self._conversation_repo.update(conversation_id, {'title': title})

    def get_history(self, conversation_id: uuid.UUID, limit: int = HISTORY_LIMIT):
        messages = self._message_repo.get_history(conversation_id, limit=limit)
        return messages[::-1]  # Slice-reverse is clearer than reversed()

    def get_history_for_llm(self, conversation_id: uuid.UUID, limit: int = HISTORY_LIMIT):
        messages = self.get_history(conversation_id, limit=limit)
        return [{'role': m.role, 'content': m.content} for m in messages]

    def save_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        engine: str = '',
        mode: str = 'auto',
        sources: list | None = None,
    ):
        message = self._message_repo.create(
            {
                'conversation_id': conversation_id,
                'role': role,
                'content': content,
                'engine': engine,
                'mode': mode,
                'sources': sources or [],
            }
        )
        ChatConversation.objects.filter(pk=conversation_id).update(updated_at=message.created_at)
        return message

    def auto_title(self, conversation_id: uuid.UUID, first_message: str):
        title = first_message[:80].strip()
        if len(first_message) > 80:
            title += '...'
        self._conversation_repo.update(conversation_id, {'title': title})
