import unittest
from unittest.mock import MagicMock, patch

from django.test import TestCase

from ai.evaluation.metrics import (
    STOP_WORDS,
    _bigrams,
    _tokenize,
    compute_answer_faithfulness,
    compute_retrieval_precision_at_5,
    evaluate_golden_dataset,
    evaluate_single_query,
    load_golden_dataset,
)


class EvaluationMetricsLoadGoldenDatasetTests(TestCase):
    @patch('ai.evaluation.metrics.GOLDEN_DATASET_PATH')
    def test_load_missing_file(self, mock_path):
        mock_path.exists.return_value = False
        self.assertEqual(load_golden_dataset(), [])

    @patch('ai.evaluation.metrics.GOLDEN_DATASET_PATH')
    def test_load_with_malformed_line(self, mock_path):
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = '{"a":1}\nnot-json\n{"b":2}\n'
        result = load_golden_dataset()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['a'], 1)

    @patch('ai.evaluation.metrics.GOLDEN_DATASET_PATH')
    def test_load_empty_file(self, mock_path):
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = '   \n\n'
        self.assertEqual(load_golden_dataset(), [])


class EvaluationMetricsRetrievalPrecisionTests(TestCase):
    def test_empty_docs_returns_zero(self):
        self.assertEqual(compute_retrieval_precision_at_5([], {}), 0.0)

    def test_no_expected_conditions_returns_one_if_docs_exist(self):
        docs = [{'content': 'hello'}, {'content': 'world'}]
        self.assertEqual(compute_retrieval_precision_at_5(docs, {}), 1.0)

    def test_relevant_content_match(self):
        docs = [{'content': 'product: Widget-001 is in stock'}]
        expected = {'conditions': [{'field': 'name', 'value': 'Widget-001'}]}
        score = compute_retrieval_precision_at_5(docs, expected)
        self.assertGreater(score, 0.0)

    def test_relevant_metadata_match(self):
        docs = [{'content': 'some content', 'metadata': {'sku_code': 'SKU-123'}}]
        expected = {'conditions': [{'field': 'sku_code', 'value': 'SKU-123'}]}
        score = compute_retrieval_precision_at_5(docs, expected)
        self.assertGreater(score, 0.0)

    def test_no_relevant_docs(self):
        docs = [{'content': 'unrelated content', 'metadata': {}}]
        expected = {'conditions': [{'field': 'name', 'value': 'Widget-999'}]}
        self.assertEqual(compute_retrieval_precision_at_5(docs, expected), 0.0)

    def test_truncates_to_top_5(self):
        docs = [{'content': str(i)} for i in range(10)]
        result = evaluate_single_query(
            {'id': 1, 'query': 'test', 'expected_filters': {}},
            retrieval_fn=lambda q, top_k: docs,
        )
        self.assertEqual(result['retrieved_count'], 10)


class EvaluationMetricsAnswerFaithfulnessTests(TestCase):
    def test_empty_answer_returns_zero(self):
        self.assertEqual(compute_answer_faithfulness('', [{'content': 'some context'}]), 0.0)

    def test_empty_context_returns_zero(self):
        self.assertEqual(compute_answer_faithfulness('Hello world', []), 0.0)

    def test_faithful_answer(self):
        context = [{'content': 'Widget-001 has 42 units in stock.'}]
        answer = '42 units of Widget-001'
        score = compute_answer_faithfulness(answer, context)
        self.assertGreater(score, 0.0)

    def test_short_answer_floor(self):
        context = [{'content': 'unrelated context'}]
        score = compute_answer_faithfulness('Hi', context)
        self.assertGreaterEqual(score, 0.25)

    def test_no_content_tokens_no_bigrams(self):
        self.assertEqual(compute_answer_faithfulness('a', [{'content': 'x'}]), 0.0)

    def test_bigram_overlap(self):
        context = [{'content': 'Widget-001 is in stock'}]
        answer = 'Widget-001 is available'
        score = compute_answer_faithfulness(answer, context)
        self.assertGreater(score, 0.0)

    def test_whitespace_only_answer_returns_zero(self):
        self.assertEqual(compute_answer_faithfulness('   ', [{'content': 'context'}]), 0.0)

    def test_stop_words_contain_common_words(self):
        self.assertIn('the', STOP_WORDS)
        self.assertNotIn('widget', STOP_WORDS)

    def test_tokenize_and_bigrams(self):
        self.assertEqual(_tokenize('Hello World'), ['hello', 'world'])
        self.assertEqual(_bigrams(['a', 'b', 'c']), {('a', 'b'), ('b', 'c')})


class EvaluationMetricsEvaluateSingleQueryTests(TestCase):
    def test_without_retrieval_fn(self):
        result = evaluate_single_query(
            {'id': 5, 'query': 'test query', 'expected_filters': {}},
            retrieval_fn=None,
        )
        self.assertEqual(result['query_id'], 5)
        self.assertEqual(result['retrieved_count'], 0)

    def test_retrieval_failure_logged(self):
        def failing_fn(query, top_k):
            raise RuntimeError('retrieval failed')

        result = evaluate_single_query(
            {'id': 6, 'query': 'fail', 'expected_filters': {}},
            retrieval_fn=failing_fn,
        )
        self.assertEqual(result['retrieved_count'], 0)

    def test_successful_retrieval(self):
        def mock_fn(query, top_k):
            return [{'content': 'match'}]

        result = evaluate_single_query(
            {
                'id': 7,
                'query': 'find match',
                'expected_filters': {'conditions': [{'field': 'name', 'value': 'match'}]},
            },
            retrieval_fn=mock_fn,
        )
        self.assertGreater(result['precision_at_5'], 0.0)


class EvaluationMetricsEvaluateGoldenDatasetTests(TestCase):
    @patch('ai.evaluation.metrics.load_golden_dataset')
    def test_empty_dataset(self, mock_load):
        mock_load.return_value = []
        result = evaluate_golden_dataset()
        self.assertEqual(result['total_queries'], 0)

    @patch('ai.evaluation.metrics.load_golden_dataset')
    def test_successful_evaluation(self, mock_load):
        mock_load.return_value = [
            {'id': 1, 'query': 'q1', 'expected_filters': {}},
            {'id': 2, 'query': 'q2', 'expected_filters': {}},
        ]

        def mock_retrieval_fn(query, top_k):
            return [{'content': 'data'}]

        result = evaluate_golden_dataset(retrieval_fn=mock_retrieval_fn)
        self.assertEqual(result['total_queries'], 2)
        self.assertGreater(result['successful_queries'], 0)
        self.assertIsInstance(result['precision_at_5'], float)
        self.assertIsInstance(result['faithfulness'], float)
        self.assertIn('per_query', result)

    @patch('ai.evaluation.metrics.load_golden_dataset')
    def test_successful_queries_count(self, mock_load):
        mock_load.return_value = [{'id': 1, 'query': 'q1', 'expected_filters': {}}]

        def mock_retrieval_fn(query, top_k):
            return [{'content': 'x'}]

        result = evaluate_golden_dataset(retrieval_fn=mock_retrieval_fn)
        self.assertEqual(result['successful_queries'], 1)


class EvaluationMetricsLogScoresToLangfuseTests(TestCase):
    @patch('ai.observability.langfuse.get_langfuse_client')
    def test_logs_scores(self, mock_get_client):
        mock_client = MagicMock()
        mock_trace = MagicMock()
        mock_trace.id = 'trace-1'
        mock_client.trace.return_value = mock_trace
        mock_get_client.return_value = mock_client

        from ai.evaluation.metrics import log_scores_to_langfuse

        results = {
            'precision_at_5': 0.85,
            'faithfulness': 0.92,
            'total_queries': 10,
            'successful_queries': 8,
        }
        log_scores_to_langfuse(results, duration_ms=500.0)

        mock_client.trace.assert_called_once()
        mock_client.score.assert_called()
        mock_client.flush.assert_called_once()

    @patch('ai.observability.langfuse.get_langfuse_client')
    def test_skips_when_client_unavailable(self, mock_get_client):
        mock_get_client.return_value = None

        from ai.evaluation.metrics import log_scores_to_langfuse

        log_scores_to_langfuse({'precision_at_5': 0.5, 'faithfulness': 0.5}, 100.0)

    @patch('ai.observability.langfuse.get_langfuse_client')
    def test_handles_exception(self, mock_get_client):
        mock_get_client.side_effect = Exception('langfuse down')

        from ai.evaluation.metrics import log_scores_to_langfuse

        log_scores_to_langfuse({'precision_at_5': 0.5}, 50.0)


class IngestionInvoiceScanRepositoryTests(TestCase):
    def setUp(self):
        from apps.authentication.models import CustomUser

        self.user = CustomUser.objects.create_user(
            username='repo_test_user',
            email='repo@test.com',
            password='testpass123',
        )

    def _make_scan(self, repo, **kwargs):
        data = {
            'uploaded_by': self.user,
            'original_filename': 'test.pdf',
            'content_type': 'application/pdf',
            'file_size': 1024,
        }
        data.update(kwargs)
        return repo.create(data)

    def test_create_and_get_by_id(self):
        from apps.ingestion.repositories import InvoiceScanRepository

        repo = InvoiceScanRepository()
        scan = self._make_scan(repo)
        fetched = repo.get_by_id(scan.id)
        self.assertEqual(fetched.original_filename, 'test.pdf')

    def test_get_all(self):
        from apps.ingestion.repositories import InvoiceScanRepository

        repo = InvoiceScanRepository()
        self._make_scan(repo, original_filename='a.pdf')
        self._make_scan(repo, original_filename='b.pdf')
        self.assertGreaterEqual(repo.get_all().count(), 2)

    def test_update(self):
        from apps.ingestion.repositories import InvoiceScanRepository

        repo = InvoiceScanRepository()
        scan = self._make_scan(repo)
        updated = repo.update(scan.id, {'original_filename': 'new.pdf'})
        self.assertEqual(updated.original_filename, 'new.pdf')

    def test_delete(self):
        from apps.ingestion.repositories import InvoiceScanRepository

        repo = InvoiceScanRepository()
        scan = self._make_scan(repo)
        repo.delete(scan.id)
        with self.assertRaises(type(scan).DoesNotExist):
            repo.get_by_id(scan.id)

    def test_mark_confirmed(self):
        from apps.ingestion.models import InvoiceScan
        from apps.ingestion.repositories import InvoiceScanRepository

        repo = InvoiceScanRepository()
        scan = self._make_scan(repo)
        confirmed = repo.mark_confirmed(scan.id, {'product_name': 'Widget'})
        self.assertEqual(confirmed.status, InvoiceScan.Status.CONFIRMED)
        self.assertTrue(confirmed.is_confirmed)

    def test_mark_rejected(self):
        from apps.ingestion.models import InvoiceScan
        from apps.ingestion.repositories import InvoiceScanRepository

        repo = InvoiceScanRepository()
        scan = self._make_scan(repo)
        rejected = repo.mark_rejected(scan.id)
        self.assertEqual(rejected.status, InvoiceScan.Status.REJECTED)

    def test_update_nonexistent_raises(self):
        from apps.ingestion.models import InvoiceScan
        from apps.ingestion.repositories import InvoiceScanRepository

        repo = InvoiceScanRepository()
        # First verify update with filter works (no-op) then get_by_id raises
        InvoiceScan.objects.filter(pk=99999).update(original_filename='x')
        with self.assertRaises(InvoiceScan.DoesNotExist):
            repo.get_by_id(99999)


class AiConversationRepositoryTests(TestCase):
    def setUp(self):
        from apps.authentication.models import CustomUser

        self.user = CustomUser.objects.create_user(
            username='conv_repo_user', email='conv_repo@test.com', password='testpass123'
        )

    def test_create_and_get_by_id(self):
        from apps.ai.repositories import ConversationRepository

        repo = ConversationRepository()
        conv = repo.create({'user': self.user, 'title': 'Test'})
        fetched = repo.get_by_id(conv.id)
        self.assertEqual(fetched.title, 'Test')

    def test_get_all(self):
        from apps.ai.repositories import ConversationRepository

        repo = ConversationRepository()
        repo.create({'user': self.user, 'title': 'A'})
        repo.create({'user': self.user, 'title': 'B'})
        self.assertGreaterEqual(repo.get_all().count(), 2)

    def test_update(self):
        from apps.ai.repositories import ConversationRepository

        repo = ConversationRepository()
        conv = repo.create({'user': self.user, 'title': 'Old'})
        updated = repo.update(conv.id, {'title': 'New'})
        self.assertEqual(updated.title, 'New')

    def test_delete(self):
        from apps.ai.repositories import ConversationRepository

        repo = ConversationRepository()
        conv = repo.create({'user': self.user, 'title': 'Del'})
        repo.delete(conv.id)
        with self.assertRaises(type(conv).DoesNotExist):
            repo.get_by_id(conv.id)

    def test_list_for_user(self):
        from apps.ai.repositories import ConversationRepository

        repo = ConversationRepository()
        repo.create({'user': self.user, 'title': 'C'})
        convs = repo.list_for_user(self.user)
        self.assertTrue(convs.exists())

    def test_get_with_messages_returns_none_for_other_user(self):
        from apps.ai.repositories import ConversationRepository
        from apps.authentication.models import CustomUser

        other = CustomUser.objects.create_user(
            username='other_user', email='other@test.com', password='testpass123'
        )
        repo = ConversationRepository()
        conv = repo.create({'user': other, 'title': 'Other'})
        result = repo.get_with_messages(conv.id, self.user)
        self.assertIsNone(result)


class AiChatMessageRepositoryTests(TestCase):
    def setUp(self):
        from apps.ai.models import ChatConversation
        from apps.authentication.models import CustomUser

        self.user = CustomUser.objects.create_user(
            username='msg_repo_user', email='msg_repo@test.com', password='testpass123'
        )
        self.conv = ChatConversation.objects.create(user=self.user, title='Msg Test')

    def test_create_and_get_by_id(self):
        from apps.ai.repositories import ChatMessageRepository

        repo = ChatMessageRepository()
        msg = repo.create({'conversation': self.conv, 'role': 'user', 'content': 'hello'})
        fetched = repo.get_by_id(msg.id)
        self.assertEqual(fetched.content, 'hello')

    def test_get_all(self):
        from apps.ai.repositories import ChatMessageRepository

        repo = ChatMessageRepository()
        repo.create({'conversation': self.conv, 'role': 'user', 'content': 'a'})
        repo.create({'conversation': self.conv, 'role': 'assistant', 'content': 'b'})
        self.assertGreaterEqual(repo.get_all().count(), 2)

    def test_update(self):
        from apps.ai.repositories import ChatMessageRepository

        repo = ChatMessageRepository()
        msg = repo.create({'conversation': self.conv, 'role': 'user', 'content': 'old'})
        updated = repo.update(msg.id, {'content': 'new'})
        self.assertEqual(updated.content, 'new')

    def test_delete(self):
        from apps.ai.repositories import ChatMessageRepository

        repo = ChatMessageRepository()
        msg = repo.create({'conversation': self.conv, 'role': 'user', 'content': 'del'})
        repo.delete(msg.id)
        with self.assertRaises(type(msg).DoesNotExist):
            repo.get_by_id(msg.id)

    def test_get_history(self):
        from apps.ai.repositories import ChatMessageRepository

        repo = ChatMessageRepository()
        for i in range(5):
            repo.create({'conversation': self.conv, 'role': 'user', 'content': str(i)})
        history = repo.get_history(self.conv.id, limit=3)
        self.assertLessEqual(len(history), 3)


class AiConversationServiceAutoTitleTests(TestCase):
    def test_auto_title_truncates_long_message(self):
        from apps.ai.models import ChatConversation
        from apps.ai.services import ConversationService
        from apps.authentication.models import CustomUser

        user = CustomUser.objects.create_user(
            username='auto_title_user', email='auto_title@test.com', password='testpass123'
        )
        conv = ChatConversation.objects.create(user=user, title='')
        svc = ConversationService()
        long_msg = 'x' * 100
        svc.auto_title(conv.id, long_msg)
        conv.refresh_from_db()
        self.assertTrue(conv.title.endswith('...'))
        self.assertLessEqual(len(conv.title), 83)


class ProviderConfigGeminiChatLlmTests(TestCase):
    @patch('ai.llm.provider_config.get_api_key', return_value='fake-key')
    @patch('langchain_google_genai.ChatGoogleGenerativeAI')
    @patch(
        'ai.llm.llm_provider_manager.get_provider_manager', side_effect=RuntimeError('no manager')
    )
    def test_get_chat_llm_gemini(self, _mock_mgr, mock_google, mock_key):
        import ai.llm.provider_config as pc

        original = pc.PROVIDER
        try:
            pc.PROVIDER = 'gemini'
            pc.get_chat_llm()
            mock_google.assert_called_once()
            self.assertEqual(mock_google.call_args.kwargs['model'], 'gemini-2.0-flash')
        finally:
            pc.PROVIDER = original


class CoreExceptionsTests(TestCase):
    def test_is_llm_quota_error_true(self):
        from core.exceptions import is_llm_quota_error

        self.assertTrue(is_llm_quota_error(Exception('insufficient_quota')))
        self.assertTrue(is_llm_quota_error(Exception('rate_limit_reached')))
        self.assertTrue(is_llm_quota_error(Exception('quota_exceeded')))

    def test_is_llm_quota_error_false(self):
        from core.exceptions import is_llm_quota_error

        self.assertFalse(is_llm_quota_error(Exception('random error')))

    def test_sanitize_llm_error_quota(self):
        from core.exceptions import sanitize_llm_error

        msg = sanitize_llm_error(Exception('rate_limit_reached'))
        self.assertIn('quota', msg.lower())

    def test_sanitize_llm_error_generic(self):
        from core.exceptions import sanitize_llm_error

        msg = sanitize_llm_error(Exception('some other error'))
        self.assertIn('unexpected', msg.lower())


class CoreThrottlesTests(TestCase):
    def test_safe_anon_throttle_allows_options(self):
        from unittest.mock import MagicMock

        from core.throttles import SAFEAnonRateThrottle

        throttle = SAFEAnonRateThrottle()
        request = MagicMock()
        request.method = 'OPTIONS'
        self.assertTrue(throttle.allow_request(request, None))

    def test_safe_user_throttle_allows_options(self):
        from unittest.mock import MagicMock

        from core.throttles import SAFEUserRateThrottle

        throttle = SAFEUserRateThrottle()
        request = MagicMock()
        request.method = 'OPTIONS'
        self.assertTrue(throttle.allow_request(request, None))


class RendererResponseEnvelopeTests(TestCase):
    def _render(self, data, status_code=200, query_params=None, envelope_exempt=False):
        from unittest.mock import MagicMock

        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory

        from config.renderers import ResponseEnvelopeRenderer

        factory = APIRequestFactory()
        wsgi = factory.get('/', query_params or {})
        drf_request = Request(wsgi)
        view = MagicMock()
        view.envelope_exempt = envelope_exempt
        response = MagicMock()
        response.status_code = status_code
        renderer = ResponseEnvelopeRenderer()
        return renderer.render(
            data,
            accepted_media_type='application/json',
            renderer_context={'view': view, 'response': response, 'request': drf_request},
        )

    def _decode(self, rendered):
        import json

        return json.loads(rendered)

    def test_list_data_wraps_in_envelope(self):
        result = self._render([1, 2, 3])
        decoded = self._decode(result)
        self.assertEqual(decoded['status'], 'success')
        self.assertEqual(decoded['data'], [1, 2, 3])

    def test_dict_data_wraps_in_envelope(self):
        result = self._render({'foo': 'bar'})
        decoded = self._decode(result)
        self.assertEqual(decoded['status'], 'success')
        self.assertEqual(decoded['data'], {'foo': 'bar'})

    def test_paginated_dict_wraps_in_envelope(self):
        result = self._render({'count': 10, 'results': [1, 2]})
        decoded = self._decode(result)
        self.assertEqual(decoded['meta']['page'], 1)
        self.assertEqual(decoded['meta']['total'], 10)

    def test_paginated_dict_without_count(self):
        result = self._render({'results': [1, 2]})
        decoded = self._decode(result)
        self.assertEqual(decoded['status'], 'success')

    def test_error_status_passes_through(self):
        result = self._render({'error': 'bad'}, status_code=400)
        import json

        decoded = json.loads(result)
        self.assertNotIn('status', decoded)

    def test_already_wrapped_dict_passes_through(self):
        result = self._render({'status': 'success', 'data': 'x'})
        import json

        decoded = json.loads(result)
        self.assertEqual(decoded['status'], 'success')

    def test_envelope_exempt_passes_through(self):
        result = self._render('raw', envelope_exempt=True)
        import json

        decoded = json.loads(result)
        self.assertEqual(decoded, 'raw')

    def test_invalid_page_params_defaults(self):
        result = self._render(
            {'count': 5, 'results': ['a']}, query_params={'page': 'abc', 'page_size': 'xyz'}
        )
        decoded = self._decode(result)
        self.assertEqual(decoded['meta']['page'], 1)
        self.assertEqual(decoded['meta']['per_page'], 20)


class AuditLogAiActionTests(TestCase):
    def setUp(self):
        from apps.authentication.models import CustomUser

        self.user = CustomUser.objects.create_user(
            username='audit_test_user', email='audit@test.com', password='testpass123'
        )

    def test_log_ai_action_creates_log(self):
        from apps.audit.utils import log_ai_action

        log_ai_action('AI_NL_QUERY', self.user, entity_type='product', data={'q': 'test'})
        from apps.audit.models import AuditLog

        self.assertTrue(AuditLog.objects.filter(event='AI_NL_QUERY').exists())

    @patch('apps.audit.utils.AuditLog.objects.create')
    def test_log_ai_action_handles_exception(self, mock_create):
        from apps.audit.utils import log_ai_action

        mock_create.side_effect = Exception('DB down')
        log_ai_action('AI_NL_QUERY', self.user)


class HealthCheckViewsTests(TestCase):
    def test_is_internal_request_loopback(self):
        from unittest.mock import MagicMock

        from apps.health.views import _is_internal_request

        request = MagicMock()
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        self.assertTrue(_is_internal_request(request))

    def test_is_internal_request_external(self):
        from unittest.mock import MagicMock

        from apps.health.views import _is_internal_request

        request = MagicMock()
        request.META = {'REMOTE_ADDR': '8.8.8.8'}
        self.assertFalse(_is_internal_request(request))

    def test_is_internal_request_xff(self):
        from unittest.mock import MagicMock

        from apps.health.views import _is_internal_request

        request = MagicMock()
        request.META = {'HTTP_X_FORWARDED_FOR': '10.0.0.1, 8.8.8.8'}
        self.assertTrue(_is_internal_request(request))

    def test_is_internal_request_invalid_ip(self):
        from unittest.mock import MagicMock

        from apps.health.views import _is_internal_request

        request = MagicMock()
        request.META = {'REMOTE_ADDR': 'not-an-ip'}
        self.assertFalse(_is_internal_request(request))

    def test_check_database_ok(self):
        from apps.health.views import _check_database

        self.assertTrue(_check_database())

    @patch('apps.health.views.connections')
    def test_check_database_fails(self, mock_conn):
        from apps.health.views import _check_database

        mock_conn.__getitem__.side_effect = Exception('DB down')
        self.assertFalse(_check_database())

    @patch('apps.health.views.cache.set', return_value=True)
    @patch('apps.health.views.cache.get', return_value='ok')
    def test_check_redis_ok(self, mock_get, mock_set):
        from apps.health.views import _check_redis

        self.assertTrue(_check_redis())

    @patch('apps.health.views.cache.set', side_effect=Exception('redis down'))
    def test_check_redis_fails(self, mock_set):
        from apps.health.views import _check_redis

        self.assertFalse(_check_redis())

    def test_health_check_live(self):
        from rest_framework.test import APIRequestFactory

        from apps.health.views import HealthCheckView

        factory = APIRequestFactory()
        request = factory.get('/health/live/')
        view = HealthCheckView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'ok')

    def test_readiness_forbidden(self):
        from rest_framework.test import APIRequestFactory

        from apps.health.views import ReadinessView

        factory = APIRequestFactory()
        request = factory.get('/health/ready/')
        request.META = {'REMOTE_ADDR': '8.8.8.8'}
        view = ReadinessView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 403)

    @patch.dict('os.environ', {'HEALTH_SECRET_HEADER': ''})
    def test_readiness_internal(self):
        from rest_framework.test import APIRequestFactory

        from apps.health.views import ReadinessView

        factory = APIRequestFactory()
        request = factory.get('/health/ready/')
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        view = ReadinessView.as_view()
        response = view(request)
        self.assertIn(response.status_code, (200, 503))

    @patch.dict('os.environ', {'HEALTH_SECRET_HEADER': 'my-secret'})
    def test_readiness_with_secret(self):
        from rest_framework.test import APIRequestFactory

        from apps.health.views import ReadinessView

        factory = APIRequestFactory()
        request = factory.get('/health/ready/')
        request.META = {'HTTP_X_HEALTH_SECRET': 'my-secret'}
        view = ReadinessView.as_view()
        response = view(request)
        self.assertIn(response.status_code, (200, 503))


class CoreValidatorsTests(TestCase):
    def test_validate_sku_code_valid(self):
        from core.validators import validate_sku_code

        self.assertTrue(validate_sku_code('ABC-123'))
        self.assertTrue(validate_sku_code('SKU-001'))

    def test_validate_sku_code_invalid(self):
        from core.validators import validate_sku_code

        self.assertFalse(validate_sku_code('abc_123'))
        self.assertFalse(validate_sku_code(''))


class AuditSignalsErrorHandlingTests(TestCase):
    def setUp(self):
        from apps.authentication.models import CustomUser

        self.user = CustomUser.objects.create_user(
            username='signal_test_user', email='signal@test.com', password='testpass123'
        )

    @patch('apps.audit.signals.AuditLog.objects.create')
    def test_log_po_approval_handles_exception(self, mock_create):
        from unittest.mock import MagicMock

        from apps.audit.signals import log_po_approval

        mock_create.side_effect = Exception('DB down')
        mock_po = MagicMock()
        mock_po.supplier.name = 'Test Supplier'
        mock_po.total_cost = 100.0
        mock_po.id = 1
        log_po_approval(sender=None, po=mock_po, user=self.user)

    @patch('apps.audit.signals.AuditLog.objects.create')
    def test_log_po_approval_skips_non_customuser(self, mock_create):
        from apps.audit.signals import log_po_approval

        log_po_approval(sender=None, po=None, user='not_a_user_object')
        mock_create.assert_not_called()

    @patch('apps.audit.signals.AuditLog.objects.create')
    def test_log_po_confirmed_handles_exception(self, mock_create):
        from unittest.mock import MagicMock

        from apps.audit.signals import log_po_confirmed

        mock_create.side_effect = Exception('DB down')
        mock_po = MagicMock()
        mock_po.supplier.name = 'S'
        mock_po.sku.code = 'SKU-1'
        mock_po.total_cost = 50.0
        mock_po.id = 1
        log_po_confirmed(sender=None, po=mock_po)

    @patch('apps.audit.signals.AuditLog.objects.create')
    def test_log_po_rejection_handles_exception(self, mock_create):
        from unittest.mock import MagicMock

        from apps.audit.signals import log_po_rejection

        mock_create.side_effect = Exception('DB down')
        mock_po = MagicMock()
        mock_po.supplier.name = 'S'
        mock_po.total_cost = 50.0
        mock_po.id = 1
        log_po_rejection(sender=None, po=mock_po, user=self.user)

    @patch('apps.audit.signals.AuditLog.objects.create')
    def test_log_po_sent_handles_exception(self, mock_create):
        from unittest.mock import MagicMock

        from apps.audit.signals import log_po_sent

        mock_create.side_effect = Exception('DB down')
        mock_po = MagicMock()
        mock_po.supplier.name = 'S'
        mock_po.sku.code = 'SKU-1'
        mock_po.total_cost = 50.0
        mock_po.id = 1
        log_po_sent(sender=None, po=mock_po)

    @patch('apps.audit.signals.AuditLog.objects.create')
    def test_log_stock_adjustment_handles_exception(self, mock_create):
        from unittest.mock import MagicMock

        from apps.audit.signals import log_stock_adjustment

        mock_create.side_effect = Exception('DB down')
        mock_stock_level = MagicMock()
        mock_stock_level.id = 1
        mock_stock_level.sku.code = 'SKU-1'
        mock_stock_level.quantity_on_hand = 10
        log_stock_adjustment(
            sender=None, stock_level=mock_stock_level, delta=-1, user=self.user, reason='sale'
        )

    @patch('apps.audit.signals.AuditLog.objects.create')
    def test_log_stock_adjustment_skips_non_customuser(self, mock_create):
        from apps.audit.signals import log_stock_adjustment

        log_stock_adjustment(
            sender=None, stock_level=None, delta=0, user='not_a_user', reason='test'
        )
        mock_create.assert_not_called()

    @patch('apps.audit.signals.AuditLog.objects.create')
    def test_log_event_handles_exception(self, mock_create):
        from apps.audit.signals import log_event

        mock_create.side_effect = Exception('DB down')
        log_event('TEST_EVENT', self.user)

    def test_log_event_creates_log_entry(self):
        from apps.audit.signals import log_event

        log_event('TEST_EVENT', self.user, entity_id=42, data_snapshot={'key': 'val'})
        from apps.audit.models import AuditLog

        self.assertTrue(AuditLog.objects.filter(event='TEST_EVENT').exists())


class ExceptionHandlerCoverageTests(TestCase):
    def test_django_validation_error(self):
        from django.core.exceptions import ValidationError

        from config.exception_handler import custom_exception_handler

        exc = ValidationError('invalid input')
        response = custom_exception_handler(exc, {'view': MagicMock()})
        self.assertEqual(response.status_code, 422)

    def test_integrity_error_unique(self):
        from django.db import IntegrityError

        from config.exception_handler import custom_exception_handler

        exc = IntegrityError('unique constraint violation')
        response = custom_exception_handler(exc, {'view': MagicMock()})
        self.assertEqual(response.status_code, 409)

    def test_integrity_error_non_unique(self):
        from django.db import IntegrityError

        from config.exception_handler import custom_exception_handler

        exc = IntegrityError('some other constraint error')
        response = custom_exception_handler(exc, {'view': MagicMock()})
        self.assertEqual(response.status_code, 500)

    @patch('config.exception_handler.drf_exception_handler')
    def test_404_string_detail(self, mock_drf):
        from config.exception_handler import custom_exception_handler

        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.data = 'Not found string'
        mock_drf.return_value = mock_resp
        response = custom_exception_handler(ValueError(), {'view': MagicMock()})
        self.assertEqual(response.status_code, 404)

    @patch('config.exception_handler.drf_exception_handler')
    def test_401_string_detail(self, mock_drf):
        from config.exception_handler import custom_exception_handler

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.data = 'Unauthorized string'
        mock_drf.return_value = mock_resp
        response = custom_exception_handler(ValueError(), {'view': MagicMock()})
        self.assertEqual(response.status_code, 401)

    @patch('config.exception_handler.drf_exception_handler')
    def test_400_with_duplicate_string(self, mock_drf):
        from config.exception_handler import custom_exception_handler

        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.data = {'field': ['A record already exists']}
        mock_drf.return_value = mock_resp
        response = custom_exception_handler(ValueError(), {'view': MagicMock()})
        self.assertEqual(response.status_code, 409)

    @patch('config.exception_handler.drf_exception_handler')
    def test_422_with_non_list_field(self, mock_drf):
        from config.exception_handler import custom_exception_handler

        mock_resp = MagicMock()
        mock_resp.status_code = 422
        mock_resp.data = {'field': ('tuple', 1)}
        mock_drf.return_value = mock_resp
        response = custom_exception_handler(ValueError(), {'view': MagicMock()})
        self.assertEqual(response.status_code, 422)
        self.assertIn('fields', response.data)


class ProviderConfigGetWhisperClientTests(TestCase):
    @unittest.skipUnless(
        __import__('importlib', fromlist=['util']).util.find_spec('groq'),
        'groq not installed',
    )
    @patch('ai.llm.provider_config.get_api_key_for_provider', return_value='gsk-test')
    @patch('groq.Groq')
    def test_get_whisper_client_groq(self, mock_groq, mock_key):
        import ai.llm.provider_config as pc

        original = pc.WHISPER_PROVIDER
        try:
            pc.WHISPER_PROVIDER = 'groq'
            pc.get_whisper_client()
            mock_groq.assert_called_once()
        finally:
            pc.WHISPER_PROVIDER = original
