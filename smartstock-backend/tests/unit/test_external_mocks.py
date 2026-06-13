from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase


class MockOpenAITest(TestCase):
    @patch('openai.OpenAI')
    def test_openai_client_initialization(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        from openai import OpenAI

        client = OpenAI(api_key='test-key')
        self.assertIsNotNone(client)

    @patch('openai.OpenAI')
    def test_openai_chat_completion(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='Hello'))]
        )
        from openai import OpenAI

        client = OpenAI(api_key='test-key')
        response = client.chat.completions.create(
            model='gpt-4',
            messages=[{'role': 'user', 'content': 'Hi'}],
        )
        self.assertEqual(response.choices[0].message.content, 'Hello')

    @patch('openai.OpenAI')
    def test_openai_error_handling(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception('API error')
        from openai import OpenAI

        client = OpenAI(api_key='test-key')
        with self.assertRaises(Exception):
            client.chat.completions.create(
                model='gpt-4',
                messages=[{'role': 'user', 'content': 'Hi'}],
            )


class MockCohereTest(TestCase):
    @patch('cohere.Client')
    def test_cohere_client_init(self, mock_cohere):
        mock_client = MagicMock()
        mock_cohere.return_value = mock_client
        from cohere import Client

        client = Client(api_key='test-key')
        self.assertIsNotNone(client)

    @patch('cohere.Client')
    def test_cohere_embed(self, mock_cohere):
        mock_client = MagicMock()
        mock_cohere.return_value = mock_client
        mock_client.embed.return_value = SimpleNamespace(embeddings=[[0.1, 0.2, 0.3]])
        from cohere import Client

        client = Client(api_key='test-key')
        result = client.embed(texts=['hello world'], model='embed-english-v3.0')
        self.assertEqual(len(result.embeddings), 1)


class MockLangfuseTest(TestCase):
    def test_langfuse_client_none_when_no_keys(self):
        from ai.observability.langfuse import get_langfuse_client

        with patch('ai.observability.langfuse._setting', return_value=None):
            import ai.observability.langfuse as lf_module

            lf_module._langfuse_client = None
            result = get_langfuse_client()
            self.assertIsNone(result)

    def test_langfuse_handler_none_when_no_keys(self):
        from ai.observability.langfuse import get_langfuse_callback_handler

        with patch('ai.observability.langfuse._setting', return_value=None):
            import ai.observability.langfuse as lf_module

            lf_module._langfuse_handler = None
            result = get_langfuse_callback_handler()
            self.assertIsNone(result)

    def test_trace_agent_run_no_client(self):
        from ai.observability.langfuse import trace_agent_run

        with patch('ai.observability.langfuse.get_langfuse_client', return_value=None):
            trace_agent_run('test_agent', {'input': 1}, {'output': 2}, [])
        self.assertTrue(True)

    def test_invoke_with_langfuse_no_callbacks(self):
        from ai.observability.langfuse import invoke_with_langfuse

        with patch('ai.observability.langfuse.get_langchain_callbacks', return_value=[]):
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = 'result'
            result = invoke_with_langfuse(mock_chain, {'payload': 'test'})
            self.assertEqual(result, 'result')

    def test_invoke_with_langfuse_with_callbacks(self):
        from ai.observability.langfuse import invoke_with_langfuse

        mock_handler = MagicMock()
        with patch(
            'ai.observability.langfuse.get_langchain_callbacks', return_value=[mock_handler]
        ):
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = 'result'
            invoke_with_langfuse(mock_chain, {'payload': 'test'})
            mock_chain.invoke.assert_called_once_with(
                {'payload': 'test'}, config={'callbacks': [mock_handler]}
            )


class MockLangChainTest(TestCase):
    @patch('langchain_openai.ChatOpenAI')
    def test_chat_openai_init(self, mock_chat):
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(api_key='test-key')
        self.assertIsNotNone(llm)

    @patch('langchain_openai.ChatOpenAI')
    def test_chat_openai_invoke(self, mock_chat):
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance
        mock_instance.invoke.return_value = SimpleNamespace(content='Response')
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(api_key='test-key')
        result = llm.invoke('Hello')
        self.assertEqual(result.content, 'Response')

    def test_prompt_template(self):
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages(
            [
                ('system', 'You are helpful.'),
                ('user', '{input}'),
            ]
        )
        messages = prompt.format_messages(input='Hello')
        self.assertEqual(len(messages), 2)
        self.assertIn('Hello', messages[1].content)


class MockProphetTest(TestCase):
    @patch('prophet.Prophet')
    def test_prophet_init(self, mock_prophet):
        mock_instance = MagicMock()
        mock_prophet.return_value = mock_instance
        from prophet import Prophet

        model = Prophet()
        self.assertIsNotNone(model)

    @patch('prophet.Prophet')
    def test_prophet_fit_predict(self, mock_prophet):
        import pandas as pd

        mock_instance = MagicMock()
        mock_prophet.return_value = mock_instance
        mock_instance.fit.return_value = None
        mock_instance.predict.return_value = pd.DataFrame(
            {
                'ds': pd.date_range('2025-01-01', periods=5),
                'yhat': [10.0] * 5,
            }
        )
        from prophet import Prophet

        model = Prophet()
        df = pd.DataFrame(
            {
                'ds': pd.date_range('2025-01-01', periods=100),
                'y': [10.0] * 100,
            }
        )
        model.fit(df)
        forecast = model.predict(df[['ds']])
        self.assertEqual(len(forecast), 5)


class MockRedisTest(TestCase):
    def test_cache_set_get(self):
        from django.core.cache import cache

        cache.set('test_key', 'test_value', timeout=60)
        result = cache.get('test_key')
        self.assertEqual(result, 'test_value')

    def test_cache_delete(self):
        from django.core.cache import cache

        cache.set('to_delete', 'value', timeout=60)
        cache.delete('to_delete')
        result = cache.get('to_delete')
        self.assertIsNone(result)

    def test_cache_delete_pattern_noop(self):
        from django.core.cache import cache

        cache.set('product_list_1', 'data1', timeout=60)
        cache.set('product_list_2', 'data2', timeout=60)
        cache.delete_pattern('product_list_*')
        self.assertEqual(cache.get('product_list_1'), 'data1')
        self.assertEqual(cache.get('product_list_2'), 'data2')


class MockEmailServiceTest(TestCase):
    def test_email_backend_locmem(self):
        from django.core import mail
        from django.test import override_settings

        with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            mail.send_mail(
                'Test Subject',
                'Test body',
                'from@example.com',
                ['to@example.com'],
            )
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, 'Test Subject')


class MockCeleryTest(TestCase):
    def test_eager_task_execution(self):
        from django.conf import settings

        self.assertTrue(settings.CELERY_TASK_ALWAYS_EAGER)

    def test_forecasting_task_runs_eagerly(self):
        from apps.forecasting.tasks import run_forecast_for_all_skus

        with patch('apps.forecasting.services.ForecastingService.run_forecast') as mock_run:
            mock_run.return_value = {'sku': 'TEST', 'status': 'skipped'}
            result = run_forecast_for_all_skus()
            self.assertIn('0/0', result)
