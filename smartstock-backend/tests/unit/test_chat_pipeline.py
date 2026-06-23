# smartstock-backend/tests/unit/test_chat_pipeline.py
import uuid
from unittest.mock import patch, MagicMock
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
        conv, history, error = ChatPipeline.load_conversation(
            uuid.uuid4(), MagicMock(), 'rag'
        )
        self.assertIsNotNone(error)
        self.assertIn('not found', error['message'])
