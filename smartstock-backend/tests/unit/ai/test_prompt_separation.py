"""
Tests for system / user role separation in the AI layer.

Ensures that:
  1. System prompts always use role="system" / SystemMessagePromptTemplate
  2. User input always uses role="user" / HumanMessagePromptTemplate
  3. System prompt and user input are never concatenated into a single message
"""

import pytest
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

from ai.llm.chain import _NL_PROMPT
from ai.llm.prompts import SYSTEM_PROMPT


class TestPromptRoleSeparation:
    """Verify the NL query chain's ChatPromptTemplate has correct role separation."""

    def test_nl_prompt_has_system_message(self):
        messages = _NL_PROMPT.messages
        system_msgs = [m for m in messages if isinstance(m, SystemMessagePromptTemplate)]
        assert len(system_msgs) >= 1, 'NL prompt must have at least one system message'

    def test_nl_prompt_has_user_message(self):
        messages = _NL_PROMPT.messages
        user_msgs = [m for m in messages if isinstance(m, HumanMessagePromptTemplate)]
        assert len(user_msgs) >= 1, 'NL prompt must have at least one user message'

    def test_system_message_is_systemmessagetemplate(self):
        messages = _NL_PROMPT.messages
        for msg in messages:
            if isinstance(msg, SystemMessagePromptTemplate):
                return
        pytest.fail('No SystemMessagePromptTemplate found in NL prompt')

    def test_user_message_is_humanmessagetemplate(self):
        messages = _NL_PROMPT.messages
        for msg in messages:
            if isinstance(msg, HumanMessagePromptTemplate):
                return
        pytest.fail('No HumanMessagePromptTemplate found in NL prompt')

    def test_system_prompt_is_string_not_empty(self):
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 50

    def test_system_prompt_contains_role_declaration(self):
        assert 'You are SmartStock AI' in SYSTEM_PROMPT

    def test_messages_are_separate_not_concatenated(self):
        """
        Verify that system and user messages are in separate templates,
        not concatenated into one string.
        """
        messages = _NL_PROMPT.messages
        system_idx = next(
            (i for i, m in enumerate(messages) if isinstance(m, SystemMessagePromptTemplate)),
            None,
        )
        user_idx = next(
            (i for i, m in enumerate(messages) if isinstance(m, HumanMessagePromptTemplate)),
            None,
        )
        assert system_idx is not None, 'No system message found'
        assert user_idx is not None, 'No user message found'
        assert user_idx > system_idx, 'User message must come after system message'


class TestIngestionRoleSeparation:
    """Verify the RAG prompt in services.py has correct role separation."""

    def test_rag_system_prompt_has_role_declaration(self):
        from apps.ingestion.services import RAGQueryService

        assert 'You are SmartStock AI' in RAGQueryService.RAG_SYSTEM_PROMPT

    def test_rag_chat_prompt_has_separate_roles(self):
        """Verify the production RAG prompt uses separate system/user messages.

        Intercepts ChatPromptTemplate.from_messages inside the production
        code path to verify the actual prompt construction.
        """
        from unittest.mock import patch

        original_from_messages = ChatPromptTemplate.from_messages
        captured = []

        def capture_prompt(messages, **kwargs):
            captured.append(messages)
            return original_from_messages(messages, **kwargs)

        with (
            patch.object(ChatPromptTemplate, 'from_messages', side_effect=capture_prompt),
            patch('apps.ingestion.services.RAGQueryService._get_llm'),
            patch('apps.ingestion.services.ChatOpenAI'),
            patch('apps.ingestion.services.OpenAIEmbeddings'),
            patch(
                'apps.ingestion.services.invoke_with_langfuse',
                return_value=('answer', {'total_tokens': 10}),
            ),
        ):
            from apps.ingestion.services import RAGQueryService

            service = RAGQueryService()
            service.call_llm_with_usage('test query', 'some context')

        assert len(captured) > 0, 'ChatPromptTemplate.from_messages was never called'
        messages = captured[0]
        assert len(messages) == 2
        assert messages[0][0] == 'system'
        assert messages[1][0] == 'user'
