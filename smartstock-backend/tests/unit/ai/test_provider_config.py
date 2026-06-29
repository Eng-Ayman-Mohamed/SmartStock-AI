import os
import unittest
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase


class ProviderConfigGetProviderConfigTest(TestCase):
    def test_returns_openai_config_by_default(self):
        from ai.llm import provider_config

        with patch.object(provider_config, 'PROVIDER', 'openai'):
            config = provider_config.get_provider_config()
            self.assertEqual(config['chat_model'], 'gpt-4o')
            self.assertTrue(config['supports_vision'])

    def test_returns_groq_config(self):
        from ai.llm import provider_config

        with patch.object(provider_config, 'PROVIDER', 'groq'):
            config = provider_config.get_provider_config()
            self.assertEqual(config['chat_model'], 'llama-3.3-70b-versatile')
            self.assertTrue(config['supports_vision'])
            self.assertEqual(config['vision_model'], 'meta-llama/llama-4-scout-17b-16e-instruct')
            self.assertIsNone(config['embedding_model'])

    def test_returns_gemini_config(self):
        from ai.llm import provider_config

        with patch.object(provider_config, 'PROVIDER', 'gemini'):
            config = provider_config.get_provider_config()
            self.assertEqual(config['chat_model'], 'gemini-2.0-flash')
            self.assertTrue(config['supports_vision'])
            self.assertEqual(config['embedding_model'], 'gemini-embedding-001')


class ProviderConfigGetApiKeyTest(TestCase):
    def test_raises_when_key_missing(self):
        from ai.llm import provider_config

        with patch.object(provider_config, 'PROVIDER', 'openai'):
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(ValueError) as ctx:
                    provider_config.get_api_key()
                self.assertIn('OPENAI_API_KEY', str(ctx.exception))

    def test_returns_key_when_set(self):
        from ai.llm import provider_config

        with patch.object(provider_config, 'PROVIDER', 'openai'):
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key-123'}):
                key = provider_config.get_api_key()
                self.assertEqual(key, 'test-key-123')


class ProviderConfigGetChatLlmTest(TestCase):
    @patch('langchain_openai.ChatOpenAI')
    def test_returns_chat_llm(self, mock_cls):
        from ai.llm import provider_config

        with patch.object(provider_config, 'PROVIDER', 'openai'):
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                provider_config.get_chat_llm()
                mock_cls.assert_called_once()
                self.assertEqual(mock_cls.call_args.kwargs['model'], 'gpt-4o')

    @patch('langchain_openai.ChatOpenAI')
    def test_model_override(self, mock_cls):
        from ai.llm import provider_config

        with patch.object(provider_config, 'PROVIDER', 'openai'):
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                provider_config.get_chat_llm(model_override='custom-model')
                self.assertEqual(mock_cls.call_args.kwargs['model'], 'custom-model')

    @patch('langchain_openai.ChatOpenAI')
    def test_groq_sets_base_url(self, mock_cls):
        from ai.llm import provider_config

        with patch.object(provider_config, 'PROVIDER', 'groq'):
            with patch.dict(os.environ, {'GROQ_API_KEY': 'gsk-test'}):
                provider_config.get_chat_llm()
                self.assertEqual(
                    mock_cls.call_args.kwargs['base_url'],
                    'https://api.groq.com/openai/v1',
                )


class ProviderConfigGetChatLlmMiniTest(TestCase):
    def test_calls_get_chat_llm_with_mini_model(self):
        from ai.llm import provider_config

        with patch.object(provider_config, 'PROVIDER', 'openai'):
            with patch.object(provider_config, 'get_chat_llm') as mock:
                provider_config.get_chat_llm_mini()
                mock.assert_called_once_with(temperature=0, model_override='gpt-4o-mini')


class ProviderConfigGetEmbeddingsTest(TestCase):
    @patch('langchain_openai.OpenAIEmbeddings')
    def test_openai_embeddings(self, mock_cls):
        from ai.llm import provider_config

        with patch.object(provider_config, 'PROVIDER', 'openai'):
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                provider_config.get_embeddings()
                mock_cls.assert_called_once()

    @unittest.skipUnless(
        __import__('importlib', fromlist=['util']).util.find_spec('langchain_google_genai'),
        'langchain_google_genai not installed',
    )
    @patch('langchain_google_genai.GoogleGenerativeAIEmbeddings')
    def test_gemini_embeddings(self, mock_cls):
        from ai.llm import provider_config

        with patch.object(provider_config, 'PROVIDER', 'gemini'):
            with patch.dict(os.environ, {'GOOGLE_API_KEY': 'ai-test'}):
                provider_config.get_embeddings()
                mock_cls.assert_called_once()

    @unittest.skipUnless(
        __import__('importlib', fromlist=['util']).util.find_spec('langchain_google_genai'),
        'langchain_google_genai not installed',
    )
    @patch('langchain_google_genai.GoogleGenerativeAIEmbeddings')
    def test_groq_falls_back_to_gemini(self, mock_cls):
        from ai.llm import provider_config

        with patch.object(provider_config, 'PROVIDER', 'groq'):
            with patch.dict(os.environ, {'GOOGLE_API_KEY': 'ai-test', 'COHERE_API_KEY': ''}):
                provider_config.get_embeddings()
                mock_cls.assert_called_once()

    def test_groq_without_gemini_key_raises(self):
        from ai.llm import provider_config

        with patch.object(provider_config, 'PROVIDER', 'groq'):
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(ImproperlyConfigured) as ctx:
                    provider_config.get_embeddings()
                self.assertIn('GOOGLE_API_KEY', str(ctx.exception))


class ProviderConfigGetWhisperClientTest(TestCase):
    @unittest.skipUnless(
        __import__('importlib', fromlist=['util']).util.find_spec('groq'),
        'groq not installed',
    )
    @patch('groq.Groq')
    def test_groq_whisper(self, mock_cls):
        from ai.llm import provider_config

        with patch.object(provider_config, 'WHISPER_PROVIDER', 'groq'):
            with patch.dict(os.environ, {'GROQ_API_KEY': 'gsk-test'}):
                provider_config.get_whisper_client()
                mock_cls.assert_called_once()

    @patch('openai.OpenAI')
    def test_openai_whisper(self, mock_cls):
        from ai.llm import provider_config

        with patch.object(provider_config, 'WHISPER_PROVIDER', 'openai'):
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test'}):
                provider_config.get_whisper_client()
                mock_cls.assert_called_once()


class ProviderConfigGetVisionClientTest(TestCase):
    @patch('openai.OpenAI')
    def test_openai_vision(self, mock_cls):
        from ai.llm import provider_config

        with patch.object(provider_config, 'PROVIDER', 'openai'):
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test'}):
                provider_config.get_vision_client()
                mock_cls.assert_called_once()
                self.assertNotIn('base_url', mock_cls.call_args.kwargs)

    @patch('openai.OpenAI')
    def test_groq_vision_has_base_url(self, mock_cls):
        from ai.llm import provider_config

        with patch.object(provider_config, 'PROVIDER', 'groq'):
            with patch.dict(os.environ, {'GROQ_API_KEY': 'gsk-test'}):
                provider_config.get_vision_client()
                self.assertEqual(
                    mock_cls.call_args.kwargs['base_url'],
                    'https://api.groq.com/openai/v1',
                )
