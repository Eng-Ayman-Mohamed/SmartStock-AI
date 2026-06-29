"""Tests for LLMProviderManager, ProviderHealth, and FailoverChatLLM."""

import time
from unittest.mock import MagicMock, patch

from django.test import TestCase

from ai.llm.llm_provider_manager import (
    FailoverChatLLM,
    LLMProviderManager,
    ProviderHealth,
    ProviderStatus,
    get_provider_manager,
)


class ProviderHealthInitTest(TestCase):
    def test_default_status(self):
        h = ProviderHealth(name='groq')
        self.assertEqual(h.status, ProviderStatus.HEALTHY)
        self.assertEqual(h.consecutive_failures, 0)
        self.assertEqual(h.total_calls, 0)
        self.assertEqual(h.total_failures, 0)
        self.assertIsNone(h.last_failure_time)
        self.assertIsNone(h.last_success_time)
        self.assertEqual(h.avg_latency_ms, 0.0)
        self.assertIsNone(h.circuit_open_until)


class ProviderHealthRecordSuccessTest(TestCase):
    def test_resets_consecutive_failures(self):
        h = ProviderHealth(name='groq')
        h.consecutive_failures = 5
        h.status = ProviderStatus.DEGRADED
        h.record_success(100.0)
        self.assertEqual(h.consecutive_failures, 0)

    def test_increments_total_calls(self):
        h = ProviderHealth(name='groq')
        h.record_success(100.0)
        self.assertEqual(h.total_calls, 1)

    def test_sets_status_healthy(self):
        h = ProviderHealth(name='groq')
        h.status = ProviderStatus.DEGRADED
        h.record_success(100.0)
        self.assertEqual(h.status, ProviderStatus.HEALTHY)

    def test_clears_circuit_open_until(self):
        h = ProviderHealth(name='groq')
        h.circuit_open_until = time.time() + 100
        h.record_success(100.0)
        self.assertIsNone(h.circuit_open_until)

    def test_tracks_latency(self):
        h = ProviderHealth(name='groq')
        h.record_success(100.0)
        h.record_success(200.0)
        self.assertEqual(h.avg_latency_ms, 150.0)

    def test_latency_window_limit(self):
        h = ProviderHealth(name='groq', LATENCY_WINDOW=3)
        for i in range(5):
            h.record_success(float(i * 100))
        self.assertEqual(len(h._latencies), 3)
        self.assertEqual(h.avg_latency_ms, 300.0)


class ProviderHealthRecordFailureTest(TestCase):
    def test_increments_consecutive_failures(self):
        h = ProviderHealth(name='groq')
        h.record_failure()
        self.assertEqual(h.consecutive_failures, 1)

    def test_increments_total_failures(self):
        h = ProviderHealth(name='groq')
        h.record_failure()
        self.assertEqual(h.total_failures, 1)

    def test_sets_degraded_below_threshold(self):
        h = ProviderHealth(name='groq')
        h.record_failure()
        self.assertEqual(h.status, ProviderStatus.DEGRADED)

    def test_opens_circuit_at_threshold(self):
        h = ProviderHealth(name='groq', FAILURE_THRESHOLD=2)
        h.record_failure()
        h.record_failure()
        self.assertEqual(h.status, ProviderStatus.CIRCUIT_OPEN)
        self.assertIsNotNone(h.circuit_open_until)

    def test_records_last_failure_time(self):
        h = ProviderHealth(name='groq')
        before = time.time()
        h.record_failure()
        self.assertGreaterEqual(h.last_failure_time, before)


class ProviderHealthIsAvailableTest(TestCase):
    def test_healthy_is_available(self):
        h = ProviderHealth(name='groq')
        self.assertTrue(h.is_available())

    def test_degraded_is_available(self):
        h = ProviderHealth(name='groq')
        h.status = ProviderStatus.DEGRADED
        self.assertTrue(h.is_available())

    def test_circuit_open_not_available(self):
        h = ProviderHealth(name='groq')
        h.status = ProviderStatus.CIRCUIT_OPEN
        h.circuit_open_until = time.time() + 100
        self.assertFalse(h.is_available())

    def test_circuit_open_expired_becomes_degraded(self):
        h = ProviderHealth(name='groq')
        h.status = ProviderStatus.CIRCUIT_OPEN
        h.circuit_open_until = time.time() - 1
        self.assertTrue(h.is_available())
        self.assertEqual(h.status, ProviderStatus.DEGRADED)


class ProviderHealthScoreTest(TestCase):
    def test_healthy_provider(self):
        h = ProviderHealth(name='groq')
        h.record_success(100.0)
        score = h.score()
        self.assertAlmostEqual(score, 0.1, places=2)

    def test_circuit_open_provider(self):
        h = ProviderHealth(name='groq')
        h.status = ProviderStatus.CIRCUIT_OPEN
        h.circuit_open_until = time.time() + 100
        self.assertEqual(h.score(), float('inf'))


class ProviderHealthErrorRateTest(TestCase):
    def test_zero_calls(self):
        h = ProviderHealth(name='groq')
        self.assertEqual(h.error_rate, 0.0)

    def test_with_failures(self):
        h = ProviderHealth(name='groq')
        h.total_calls = 10
        h.total_failures = 3
        self.assertAlmostEqual(h.error_rate, 0.3)


class LLMProviderManagerInitTest(TestCase):
    def test_singleton(self):
        import ai.llm.llm_provider_manager as mod

        mod._manager = None
        m1 = get_provider_manager()
        m2 = get_provider_manager()
        self.assertIs(m1, m2)
        mod._manager = None


class LLMProviderManagerGetLLMTest(TestCase):
    def _make_manager(self):
        mgr = LLMProviderManager()
        mgr._initialized = True
        mgr._providers_config = {
            'groq': {
                'api_key_env': 'GROQ_API_KEY',
                'chat_model': 'llama-3.1-8b-instant',
                'base_url': None,
            },
            'openai': {
                'api_key_env': 'OPENAI_API_KEY',
                'chat_model': 'gpt-4o-mini',
                'base_url': None,
            },
        }
        mgr._health = {
            'groq': ProviderHealth(name='groq'),
            'openai': ProviderHealth(name='openai'),
        }
        return mgr

    def test_no_providers_available(self):
        mgr = self._make_manager()
        with patch.dict('os.environ', {}, clear=False):
            with patch('os.getenv', return_value=''):
                with self.assertRaises(RuntimeError):
                    mgr.get_llm()

    @patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'})
    @patch('langchain_openai.ChatOpenAI')
    def test_provider_override(self, mock_chat_openai):
        mgr = self._make_manager()
        mock_chat_openai.return_value = MagicMock()
        result = mgr.get_llm(provider_override='groq')
        self.assertIsInstance(result, FailoverChatLLM)

    @patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'})
    def test_all_providers_fail(self):
        mgr = self._make_manager()
        with patch.object(mgr, '_create_llm', side_effect=Exception('API key missing')):
            with self.assertRaises(RuntimeError):
                mgr.get_llm()


class LLMProviderManagerCreateLLMTest(TestCase):
    def test_missing_api_key(self):
        mgr = LLMProviderManager()
        mgr._providers_config = {
            'groq': {
                'api_key_env': 'GROQ_API_KEY',
                'chat_model': 'llama-3.1-8b-instant',
                'base_url': None,
            },
        }
        with patch.dict('os.environ', {}, clear=False):
            with patch('os.getenv', return_value=''):
                with self.assertRaises(ValueError):
                    mgr._create_llm('groq', temperature=0, model_override=None)

    @patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'})
    @patch('langchain_openai.ChatOpenAI')
    def test_groq_provider(self, mock_chat_openai):
        mgr = LLMProviderManager()
        mgr._providers_config = {
            'groq': {
                'api_key_env': 'GROQ_API_KEY',
                'chat_model': 'llama-3.1-8b-instant',
                'base_url': 'https://api.groq.com/openai/v1',
            },
        }
        mock_chat_openai.return_value = MagicMock()
        mgr._create_llm('groq', temperature=0, model_override=None)
        mock_chat_openai.assert_called_once()

    @patch.dict('os.environ', {'GOOGLE_API_KEY': 'test-key'})
    @patch('langchain_google_genai.ChatGoogleGenerativeAI')
    def test_gemini_provider(self, mock_chat_gemini):
        mgr = LLMProviderManager()
        mgr._providers_config = {
            'gemini': {
                'api_key_env': 'GOOGLE_API_KEY',
                'chat_model': 'gemini-2.0-flash',
                'base_url': None,
            },
        }
        mock_chat_gemini.return_value = MagicMock()
        mgr._create_llm('gemini', temperature=0, model_override=None)
        mock_chat_gemini.assert_called_once()

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('langchain_openai.ChatOpenAI')
    def test_model_override(self, mock_chat_openai):
        mgr = LLMProviderManager()
        mgr._providers_config = {
            'openai': {
                'api_key_env': 'OPENAI_API_KEY',
                'chat_model': 'gpt-4o-mini',
                'base_url': None,
            },
        }
        mock_chat_openai.return_value = MagicMock()
        mgr._create_llm('openai', temperature=0.5, model_override='gpt-4o')
        call_kwargs = mock_chat_openai.call_args[1]
        self.assertEqual(call_kwargs['model'], 'gpt-4o')
        self.assertEqual(call_kwargs['temperature'], 0.5)


class LLMProviderManagerRecordTest(TestCase):
    def test_record_success(self):
        mgr = LLMProviderManager()
        mgr._initialized = True
        mgr._health = {'groq': ProviderHealth(name='groq')}
        mgr.record_success('groq', 100.0)
        self.assertEqual(mgr._health['groq'].total_calls, 1)

    def test_record_failure(self):
        mgr = LLMProviderManager()
        mgr._initialized = True
        mgr._health = {'groq': ProviderHealth(name='groq')}
        mgr.record_failure('groq')
        self.assertEqual(mgr._health['groq'].total_failures, 1)

    def test_record_unknown_provider(self):
        mgr = LLMProviderManager()
        mgr._initialized = True
        mgr._health = {'groq': ProviderHealth(name='groq')}
        mgr.record_failure('unknown')
        self.assertEqual(mgr._health['groq'].total_failures, 0)


class LLMProviderManagerHealthReportTest(TestCase):
    def test_health_report(self):
        mgr = LLMProviderManager()
        mgr._initialized = True
        mgr._health = {'groq': ProviderHealth(name='groq')}
        report = mgr.get_health_report()
        self.assertIn('groq', report)
        self.assertEqual(report['groq']['status'], 'healthy')


class LLMProviderManagerResetTest(TestCase):
    def test_reset_single_provider(self):
        mgr = LLMProviderManager()
        mgr._initialized = True
        h = ProviderHealth(name='groq')
        h.consecutive_failures = 5
        h.status = ProviderStatus.CIRCUIT_OPEN
        mgr._health = {'groq': h}
        mgr.reset_circuit_breaker('groq')
        self.assertEqual(h.consecutive_failures, 0)
        self.assertEqual(h.status, ProviderStatus.HEALTHY)

    def test_reset_all_providers(self):
        mgr = LLMProviderManager()
        mgr._initialized = True
        h1 = ProviderHealth(name='groq')
        h1.consecutive_failures = 5
        h1.status = ProviderStatus.CIRCUIT_OPEN
        h2 = ProviderHealth(name='openai')
        h2.consecutive_failures = 3
        h2.status = ProviderStatus.DEGRADED
        mgr._health = {'groq': h1, 'openai': h2}
        mgr.reset_circuit_breaker()
        self.assertEqual(h1.status, ProviderStatus.HEALTHY)
        self.assertEqual(h2.status, ProviderStatus.HEALTHY)


class FailoverChatLLMTest(TestCase):
    def test_llm_type(self):
        llm = FailoverChatLLM(llm_pool=[], manager=MagicMock(), provider_names=[])
        self.assertEqual(llm._llm_type, 'failover-chat-llm')

    def test_identifying_params(self):
        llm = FailoverChatLLM(llm_pool=[], manager=MagicMock(), provider_names=['groq', 'openai'])
        params = llm._identifying_params
        self.assertEqual(params['primary'], 'groq')
        self.assertEqual(params['provider_pool'], ['groq', 'openai'])

    def test_bind_tools(self):
        mock_llm1 = MagicMock()
        mock_llm1.bind_tools.return_value = MagicMock()
        mock_llm2 = MagicMock()
        mock_llm2.bind_tools.side_effect = Exception('not supported')

        llm = FailoverChatLLM(
            llm_pool=[('groq', mock_llm1), ('openai', mock_llm2)],
            manager=MagicMock(),
            provider_names=['groq', 'openai'],
        )
        result = llm.bind_tools([MagicMock()])
        self.assertIsInstance(result, FailoverChatLLM)
        self.assertEqual(len(result.llm_pool), 2)

    def test_with_structured_output(self):
        mock_llm1 = MagicMock()
        mock_llm1.with_structured_output.return_value = MagicMock()
        mock_llm2 = MagicMock()
        mock_llm2.with_structured_output.side_effect = Exception('not supported')

        llm = FailoverChatLLM(
            llm_pool=[('groq', mock_llm1), ('openai', mock_llm2)],
            manager=MagicMock(),
            provider_names=['groq', 'openai'],
        )
        result = llm.with_structured_output(MagicMock())
        self.assertIsInstance(result, FailoverChatLLM)


class FailoverChatLLMGenerateTest(TestCase):
    def test_success_first_provider(self):
        mock_llm = MagicMock()
        mock_llm._generate.return_value = MagicMock()
        mock_manager = MagicMock()

        llm = FailoverChatLLM(
            llm_pool=[('groq', mock_llm)],
            manager=mock_manager,
            provider_names=['groq'],
        )
        llm._generate(messages=[])
        mock_manager.record_success.assert_called_once()
        call_args = mock_manager.record_success.call_args[0]
        self.assertEqual(call_args[0], 'groq')
        self.assertIsInstance(call_args[1], float)

    def test_failover_on_transient_error(self):
        mock_llm1 = MagicMock()
        mock_llm1._generate.side_effect = Exception('429 rate limit')
        mock_llm2 = MagicMock()
        mock_llm2._generate.return_value = MagicMock()
        mock_manager = MagicMock()

        llm = FailoverChatLLM(
            llm_pool=[('groq', mock_llm1), ('openai', mock_llm2)],
            manager=mock_manager,
            provider_names=['groq', 'openai'],
        )
        llm._generate(messages=[])
        mock_manager.record_failure.assert_called_once_with('groq')
        mock_manager.record_success.assert_called_once()
        call_args = mock_manager.record_success.call_args[0]
        self.assertEqual(call_args[0], 'openai')

    def test_non_transient_error_raises(self):
        mock_llm = MagicMock()
        mock_llm._generate.side_effect = ValueError('bad input')
        mock_manager = MagicMock()

        llm = FailoverChatLLM(
            llm_pool=[('groq', mock_llm)],
            manager=mock_manager,
            provider_names=['groq'],
        )
        with self.assertRaises(ValueError):
            llm._generate(messages=[])

    def test_all_providers_fail(self):
        mock_llm1 = MagicMock()
        mock_llm1._generate.side_effect = Exception('503 service unavailable')
        mock_llm2 = MagicMock()
        mock_llm2._generate.side_effect = Exception('timeout')
        mock_manager = MagicMock()

        llm = FailoverChatLLM(
            llm_pool=[('groq', mock_llm1), ('openai', mock_llm2)],
            manager=mock_manager,
            provider_names=['groq', 'openai'],
        )
        with self.assertRaises(RuntimeError):
            llm._generate(messages=[])


class FailoverChatLLMStreamTest(TestCase):
    def test_stream_success(self):
        mock_chunk = MagicMock()
        mock_llm = MagicMock()
        mock_llm._stream.return_value = iter([mock_chunk])
        mock_manager = MagicMock()

        llm = FailoverChatLLM(
            llm_pool=[('groq', mock_llm)],
            manager=mock_manager,
            provider_names=['groq'],
        )
        chunks = list(llm._stream(messages=[]))
        self.assertEqual(len(chunks), 1)
        mock_manager.record_success.assert_called_once()

    def test_stream_failover(self):
        mock_llm1 = MagicMock()
        mock_llm1._stream.side_effect = Exception('429 rate limit')
        mock_llm2 = MagicMock()
        mock_llm2._stream.return_value = iter([MagicMock()])
        mock_manager = MagicMock()

        llm = FailoverChatLLM(
            llm_pool=[('groq', mock_llm1), ('openai', mock_llm2)],
            manager=mock_manager,
            provider_names=['groq', 'openai'],
        )
        chunks = list(llm._stream(messages=[]))
        self.assertEqual(len(chunks), 1)

    def test_stream_all_fail(self):
        mock_llm1 = MagicMock()
        mock_llm1._stream.side_effect = Exception('503')
        mock_llm2 = MagicMock()
        mock_llm2._stream.side_effect = Exception('timeout')
        mock_manager = MagicMock()

        llm = FailoverChatLLM(
            llm_pool=[('groq', mock_llm1), ('openai', mock_llm2)],
            manager=mock_manager,
            provider_names=['groq', 'openai'],
        )
        with self.assertRaises(RuntimeError):
            list(llm._stream(messages=[]))


class FailoverChatLLMIsTransientErrorTest(TestCase):
    def test_rate_limit(self):
        self.assertTrue(FailoverChatLLM._is_transient_error(Exception('429 too many requests')))

    def test_timeout(self):
        self.assertTrue(FailoverChatLLM._is_transient_error(Exception('connection timed out')))

    def test_overloaded(self):
        self.assertTrue(FailoverChatLLM._is_transient_error(Exception('model overloaded')))

    def test_quota(self):
        self.assertTrue(FailoverChatLLM._is_transient_error(Exception('quota exceeded')))

    def test_throttle(self):
        self.assertTrue(FailoverChatLLM._is_transient_error(Exception('request throttled')))

    def test_503(self):
        self.assertTrue(FailoverChatLLM._is_transient_error(Exception('503 service unavailable')))

    def test_502(self):
        self.assertTrue(FailoverChatLLM._is_transient_error(Exception('502 bad gateway')))

    def test_non_transient(self):
        self.assertFalse(FailoverChatLLM._is_transient_error(ValueError('invalid input')))

    def test_resource_exhausted(self):
        self.assertTrue(FailoverChatLLM._is_transient_error(Exception('resource_exhausted')))
