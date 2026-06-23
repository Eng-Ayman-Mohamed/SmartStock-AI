# smartstock-backend/apps/ingestion/chat_pipeline.py
import logging
import uuid
from dataclasses import dataclass

from apps.audit.models import AuditLog
from apps.ai.services import ConversationService

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    engine: str
    conversation: object | None
    history: list


class ChatPipeline:
    """Shared pipeline for chat validation, classification, and conversation loading."""

    @staticmethod
    def validate_and_classify(query: str, mode: str, user) -> tuple[str, None]:
        """
        Validate query (prompt injection) and classify intent.
        Returns (engine, error_response_dict_or_None).
        """
        from ai.llm.chain import prompt_injection_filter

        try:
            is_safe, matched_pattern = prompt_injection_filter(query)
        except Exception:
            logger.exception('Prompt injection filter failed')
            is_safe, matched_pattern = False, 'filter_error'

        if not is_safe:
            AuditLog.objects.create(
                user=user,
                event='PROMPT_INJECTION_ATTEMPT',
                data_snapshot={
                    'query': query[:200],
                    'matched_pattern': matched_pattern,
                    'endpoint': 'chat',
                },
            )
            return None, {
                'status': 'error',
                'error': 'InvalidQueryError',
                'message': 'Query contains disallowed content.',
            }

        if mode == 'auto':
            from ai.llm.intent_classifier import classify_intent

            classification = classify_intent(query)
            if classification.confidence < 0.7:
                engine = 'nl_query'
            elif classification.intent == 'out_of_scope':
                engine = 'nl_query'
            else:
                engine = classification.intent
        else:
            engine = mode

        return engine, None

    @staticmethod
    def load_conversation(
        conversation_id: uuid.UUID | str | None, user, engine: str
    ) -> tuple[object | None, list, None]:
        """
        Load conversation and history.
        Returns (conversation, history, error_response_dict_or_None).
        """
        conv_service = ConversationService()
        conversation = None
        history = []

        if conversation_id:
            try:
                conversation = conv_service.get_conversation(conversation_id, user)
            except ValueError:
                return None, [], {
                    'status': 'error',
                    'message': 'Conversation not found.',
                }
            if engine == 'rag':
                history = conv_service.get_history_for_llm(conversation_id)

        return conversation, history, None

    @staticmethod
    def save_messages(
        conversation_id: uuid.UUID,
        query: str,
        result: dict,
        engine: str,
        mode: str,
        conversation,
    ):
        """Save user and assistant messages to conversation."""
        conv_service = ConversationService()
        is_new = conversation.messages.count() == 0
        conv_service.save_message(
            conversation_id=conversation_id,
            role='user',
            content=query,
            mode=mode,
        )
        conv_service.save_message(
            conversation_id=conversation_id,
            role='assistant',
            content=result.get('answer', ''),
            engine=engine,
            sources=result.get('sources', []),
            mode=mode,
        )
        if is_new:
            conv_service.auto_title(conversation_id, query)
