# smartstock-backend/tests/integration/test_chat_stream.py
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.ai.models import ChatConversation, ChatMessage
from apps.authentication.models import CustomUser


@override_settings(LANGUAGE_CODE='en-us')
class ChatStreamRaceConditionTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            email='test@test.com', username='test@test.com', password='testpass123', role='viewer'
        )
        self.client.force_authenticate(user=self.user)
        self.conversation = ChatConversation.objects.create(
            user=self.user, title='Test Conv'
        )

    @patch('apps.ingestion.views.ChatStreamView._stream_rag')
    @patch('ai.llm.chain.prompt_injection_filter', return_value=(True, None))
    @patch('ai.llm.intent_classifier.classify_intent')
    def test_user_message_saved_when_stream_yields_nothing(
        self, mock_classify, mock_filter, mock_stream
    ):
        """Empty stream — user message should still be saved."""
        mock_classify.return_value = MagicMock(intent='rag', confidence=0.9)
        mock_stream.return_value = iter([])

        response = self.client.post(
            '/api/ai/chat/stream/',
            {
                'query': 'hello world',
                'mode': 'rag',
                'conversation_id': str(self.conversation.pk),
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        # Force consumption of the streaming response so side effects execute
        _ = list(response.streaming_content)
        self.assertTrue(
            ChatMessage.objects.filter(
                conversation=self.conversation, role='user', content='hello world'
            ).exists(),
            'User message should be saved even when stream yields nothing',
        )
