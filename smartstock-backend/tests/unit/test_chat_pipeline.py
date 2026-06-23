# smartstock-backend/tests/unit/test_chat_pipeline.py
import uuid
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.ingestion.chat_pipeline import ChatPipeline


class TestChatPipelineValidation(TestCase):
    @patch('apps.ingestion.chat_pipeline.AuditLog.objects.create')
    @patch('ai.llm.chain.prompt_injection_filter', return_value=(False, 'test'))
    def test_injection_returns_error(self, mock_filter, mock_audit):
        engine, error = ChatPipeline.validate_and_classify('drop table', 'auto', MagicMock())
        self.assertIsNone(engine)
        self.assertIsNotNone(error)
        self.assertEqual(error['status'], 'error')
        mock_audit.assert_called_once()

    @patch('ai.llm.intent_classifier.classify_intent')
    @patch('ai.llm.chain.prompt_injection_filter', return_value=(True, None))
    def test_auto_mode_classifies_intent(self, mock_filter, mock_classify):
        mock_classify.return_value = MagicMock(intent='rag', confidence=0.9)
        engine, error = ChatPipeline.validate_and_classify('what is policy?', 'auto', MagicMock())
        self.assertEqual(engine, 'rag')
        self.assertIsNone(error)

    @patch('ai.llm.chain.prompt_injection_filter', return_value=(True, None))
    def test_explicit_mode_passes_through(self, mock_filter):
        engine, error = ChatPipeline.validate_and_classify('test', 'nl_query', MagicMock())
        self.assertEqual(engine, 'nl_query')
        self.assertIsNone(error)


class TestChatPipelineConversation(TestCase):
    def test_no_conversation_id(self):
        conv, history, error = ChatPipeline.load_conversation(None, MagicMock(), 'rag')
        self.assertIsNone(conv)
        self.assertEqual(history, [])
        self.assertIsNone(error)

    @patch('apps.ingestion.chat_pipeline.ConversationService')
    def test_invalid_conversation_returns_error(self, MockService):
        MockService.return_value.get_conversation.side_effect = ValueError
        conv, history, error = ChatPipeline.load_conversation(uuid.uuid4(), MagicMock(), 'rag')
        self.assertIsNotNone(error)
        self.assertIn('not found', error['message'])


class TestChatPipelineSaveMessages(TestCase):
    @patch('apps.ingestion.chat_pipeline.ConversationService')
    def test_save_messages_persists_both_messages(self, MockService):
        """User and assistant messages are saved with correct arguments."""
        mock_service = MockService.return_value
        conversation = MagicMock()
        conversation.messages.exists.return_value = False
        conv_id = uuid.uuid4()
        result = {'answer': 'Hello!', 'sources': ['doc1']}

        ChatPipeline.save_messages(conv_id, 'Hi', result, 'rag', 'auto', conversation)

        self.assertEqual(mock_service.save_message.call_count, 2)
        calls = mock_service.save_message.call_args_list
        # First call: user message
        self.assertEqual(calls[0].kwargs['role'], 'user')
        self.assertEqual(calls[0].kwargs['content'], 'Hi')
        # Second call: assistant message
        self.assertEqual(calls[1].kwargs['role'], 'assistant')
        self.assertEqual(calls[1].kwargs['content'], 'Hello!')
        self.assertEqual(calls[1].kwargs['sources'], ['doc1'])

    @patch('apps.ingestion.chat_pipeline.ConversationService')
    def test_save_messages_calls_auto_title_for_new_conversation(self, MockService):
        """auto_title is called when conversation has no existing messages."""
        mock_service = MockService.return_value
        conversation = MagicMock()
        conversation.messages.exists.return_value = False
        conv_id = uuid.uuid4()

        ChatPipeline.save_messages(conv_id, 'First question', {}, 'rag', 'auto', conversation)

        mock_service.auto_title.assert_called_once_with(conv_id, 'First question')

    @patch('apps.ingestion.chat_pipeline.ConversationService')
    def test_save_messages_skips_auto_title_for_existing_conversation(self, MockService):
        """auto_title is NOT called when conversation already has messages."""
        mock_service = MockService.return_value
        conversation = MagicMock()
        conversation.messages.exists.return_value = True
        conv_id = uuid.uuid4()

        ChatPipeline.save_messages(conv_id, 'Follow-up', {}, 'rag', 'auto', conversation)

        mock_service.auto_title.assert_not_called()
