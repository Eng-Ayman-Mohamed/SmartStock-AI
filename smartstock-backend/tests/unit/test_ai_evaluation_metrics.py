import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.test import TestCase

from ai.evaluation.metrics import (
    GOLDEN_DATASET_PATH,
    STOP_WORDS,
    _bigrams,
    _tokenize,
    compute_answer_faithfulness,
    compute_retrieval_precision_at_5,
    evaluate_golden_dataset,
    evaluate_single_query,
    load_golden_dataset,
    log_scores_to_langfuse,
)


class TokenizeTest(TestCase):
    def test_basic_tokenize(self):
        self.assertEqual(_tokenize('Hello World'), ['hello', 'world'])

    def test_empty_string(self):
        self.assertEqual(_tokenize(''), [])

    def test_single_word(self):
        self.assertEqual(_tokenize('test'), ['test'])


class BigramsTest(TestCase):
    def test_basic_bigrams(self):
        result = _bigrams(['a', 'b', 'c'])
        self.assertEqual(result, {('a', 'b'), ('b', 'c')})

    def test_single_token(self):
        self.assertEqual(_bigrams(['a']), set())

    def test_empty(self):
        self.assertEqual(_bigrams([]), set())


class LoadGoldenDatasetTest(TestCase):
    def test_load_existing_dataset(self):
        if GOLDEN_DATASET_PATH.exists():
            dataset = load_golden_dataset()
            self.assertIsInstance(dataset, list)
            self.assertGreater(len(dataset), 0)

    def test_load_nonexistent_file(self):
        with patch('ai.evaluation.metrics.GOLDEN_DATASET_PATH', Path('/nonexistent/file.jsonl')):
            result = load_golden_dataset()
            self.assertEqual(result, [])

    def test_load_malformed_json_lines(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"valid": true}\n')
            f.write('not valid json\n')
            f.write('{"also_valid": true}\n')
            f.write('\n')
            f.flush()
            with patch('ai.evaluation.metrics.GOLDEN_DATASET_PATH', Path(f.name)):
                result = load_golden_dataset()
                self.assertEqual(len(result), 2)

    def test_load_empty_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('')
            f.flush()
            with patch('ai.evaluation.metrics.GOLDEN_DATASET_PATH', Path(f.name)):
                result = load_golden_dataset()
                self.assertEqual(result, [])


class ComputeRetrievalPrecisionAt5Test(TestCase):
    def test_empty_docs(self):
        result = compute_retrieval_precision_at_5([], {})
        self.assertEqual(result, 0.0)

    def test_no_filters_returns_1(self):
        docs = [{'content': 'some content'}]
        result = compute_retrieval_precision_at_5(docs, {})
        self.assertEqual(result, 1.0)

    def test_all_relevant(self):
        docs = [
            {'content': 'SKU-123 widget', 'metadata': {'sku': 'SKU-123'}},
            {'content': 'SKU-456 gadget', 'metadata': {'sku': 'SKU-456'}},
            {'content': 'SKU-789 thing', 'metadata': {'sku': 'SKU-789'}},
            {'content': 'SKU-101 item', 'metadata': {'sku': 'SKU-101'}},
            {'content': 'SKU-202 part', 'metadata': {'sku': 'SKU-202'}},
        ]
        expected = {'conditions': [{'field': 'sku', 'value': 'SKU-123'}]}
        result = compute_retrieval_precision_at_5(docs, expected)
        self.assertEqual(result, 1.0)

    def test_partial_relevant(self):
        docs = [
            {'content': 'SKU-123 widget'},
            {'content': 'unrelated content'},
            {'content': 'unrelated content'},
            {'content': 'unrelated content'},
            {'content': 'unrelated content'},
        ]
        expected = {'conditions': [{'field': 'sku', 'value': 'SKU-123'}]}
        result = compute_retrieval_precision_at_5(docs, expected)
        self.assertAlmostEqual(result, 0.2)

    def test_metadata_match(self):
        docs = [
            {'content': '', 'metadata': {'category': 'electronics'}},
            {'content': '', 'metadata': {'category': 'clothing'}},
            {'content': '', 'metadata': {'category': 'food'}},
            {'content': '', 'metadata': {'category': 'toys'}},
            {'content': '', 'metadata': {'category': 'books'}},
        ]
        expected = {'conditions': [{'field': 'category', 'value': 'electronics'}]}
        result = compute_retrieval_precision_at_5(docs, expected)
        self.assertEqual(result, 0.2)

    def test_top_5_limit(self):
        docs = [
            {'content': 'match'},
            {'content': 'match'},
            {'content': 'match'},
            {'content': 'match'},
            {'content': 'match'},
            {'content': 'match extra beyond 5'},
        ]
        expected = {'conditions': [{'field': 'content', 'value': 'match'}]}
        result = compute_retrieval_precision_at_5(docs, expected)
        self.assertEqual(result, 1.0)

    def test_case_insensitive_match(self):
        docs = [{'content': 'SKU-123 Widget'}]
        expected = {'conditions': [{'field': 'sku', 'value': 'sku-123'}]}
        result = compute_retrieval_precision_at_5(docs, expected)
        self.assertEqual(result, 0.2)

    def test_no_content_or_metadata(self):
        docs = [{'other_key': 'value'}]
        expected = {'conditions': [{'field': 'sku', 'value': 'SKU-123'}]}
        result = compute_retrieval_precision_at_5(docs, expected)
        self.assertEqual(result, 0.0)

    def test_empty_conditions_with_filters_dict(self):
        docs = [{'content': 'something'}]
        expected = {'conditions': []}
        result = compute_retrieval_precision_at_5(docs, expected)
        self.assertEqual(result, 0.0)


class ComputeAnswerFaithfulnessTest(TestCase):
    def test_empty_answer(self):
        result = compute_answer_faithfulness('', [{'content': 'some context'}])
        self.assertEqual(result, 0.0)

    def test_empty_context(self):
        result = compute_answer_faithfulness('What is SKU-123?', [])
        self.assertEqual(result, 0.0)

    def test_both_empty(self):
        result = compute_answer_faithfulness('', [])
        self.assertEqual(result, 0.0)

    def test_high_faithfulness(self):
        docs = [{'content': 'The SKU-123 widget has 50 units in stock.'}]
        answer = 'SKU-123 has 50 units in stock'
        result = compute_answer_faithfulness(answer, docs)
        self.assertGreater(result, 0.5)

    def test_low_faithfulness(self):
        docs = [{'content': 'The weather is sunny today.'}]
        answer = 'The quarterly revenue report shows significant growth in Q3'
        result = compute_answer_faithfulness(answer, docs)
        self.assertLess(result, 0.5)

    def test_short_answer_floor(self):
        docs = [{'content': 'some context here'}]
        answer = 'yes'
        result = compute_answer_faithfulness(answer, docs)
        self.assertGreaterEqual(result, 0.25)

    def test_stop_words_removed(self):
        docs = [{'content': 'the quick brown fox jumps'}]
        answer = 'the quick brown fox'
        result = compute_answer_faithfulness(answer, docs)
        self.assertGreater(result, 0.0)

    def test_bigram_overlap(self):
        docs = [{'content': 'machine learning model prediction'}]
        answer = 'machine learning prediction model'
        result = compute_answer_faithfulness(answer, docs)
        self.assertGreater(result, 0.0)

    def test_only_stop_words_short_answer_floor(self):
        docs = [{'content': 'some context'}]
        answer = 'the is are was'
        result = compute_answer_faithfulness(answer, docs)
        self.assertEqual(result, 0.25)

    def test_multiple_context_docs(self):
        docs = [
            {'content': 'SKU-123 is a widget'},
            {'content': 'Widgets are stored in warehouse A'},
        ]
        answer = 'SKU-123 widget stored in warehouse A'
        result = compute_answer_faithfulness(answer, docs)
        self.assertGreater(result, 0.3)

    def test_score_max_1(self):
        docs = [{'content': 'test test test test test'}]
        answer = 'test test test test test'
        result = compute_answer_faithfulness(answer, docs)
        self.assertLessEqual(result, 1.0)


class EvaluateSingleQueryTest(TestCase):
    def test_with_no_retrieval_fn(self):
        query_row = {
            'id': 1,
            'query': 'Show me low stock items',
            'expected_filters': {'conditions': [{'field': 'status', 'value': 'low'}]},
        }
        result = evaluate_single_query(query_row)
        self.assertEqual(result['query_id'], 1)
        self.assertIn('precision_at_5', result)
        self.assertIn('faithfulness', result)
        self.assertEqual(result['retrieved_count'], 0)

    def test_with_retrieval_fn(self):
        def mock_retrieval(query, top_k=5):
            return [{'content': 'low stock items', 'metadata': {'status': 'low'}}] * top_k

        query_row = {
            'id': 2,
            'query': 'Show me low stock',
            'expected_filters': {'conditions': [{'field': 'status', 'value': 'low'}]},
        }
        result = evaluate_single_query(query_row, retrieval_fn=mock_retrieval)
        self.assertEqual(result['retrieved_count'], 5)
        self.assertGreater(result['precision_at_5'], 0)

    def test_retrieval_fn_raises_exception(self):
        def bad_retrieval(query, top_k=5):
            raise RuntimeError('retrieval failed')

        query_row = {
            'id': 3,
            'query': 'test query',
            'expected_filters': {},
        }
        result = evaluate_single_query(query_row, retrieval_fn=bad_retrieval)
        self.assertEqual(result['retrieved_count'], 0)


class EvaluateGoldenDatasetTest(TestCase):
    def test_empty_dataset_returns_zeros(self):
        with patch('ai.evaluation.metrics.load_golden_dataset', return_value=[]):
            result = evaluate_golden_dataset()
            self.assertEqual(result['precision_at_5'], 0.0)
            self.assertEqual(result['faithfulness'], 0.0)
            self.assertEqual(result['total_queries'], 0)

    def test_with_mock_dataset(self):
        mock_dataset = [
            {
                'id': 1,
                'query': 'test query 1',
                'expected_filters': {},
            },
            {
                'id': 2,
                'query': 'test query 2',
                'expected_filters': {},
            },
        ]
        with patch('ai.evaluation.metrics.load_golden_dataset', return_value=mock_dataset):
            result = evaluate_golden_dataset()
            self.assertEqual(result['total_queries'], 2)
            self.assertIn('per_query', result)
            self.assertEqual(len(result['per_query']), 2)


class LogScoresToLangfuseTest(TestCase):
    def test_langfuse_client_unavailable(self):
        with patch('ai.observability.langfuse.get_langfuse_client', return_value=None):
            log_scores_to_langfuse({'precision_at_5': 0.8, 'faithfulness': 0.9}, 100.0)

    def test_langfuse_client_logs_scores(self):
        mock_client = MagicMock()
        mock_client.trace.return_value = MagicMock(id='trace-123')
        with patch('ai.observability.langfuse.get_langfuse_client', return_value=mock_client):
            log_scores_to_langfuse(
                {
                    'precision_at_5': 0.8,
                    'faithfulness': 0.9,
                    'total_queries': 30,
                    'successful_queries': 25,
                },
                1500.0,
            )
            mock_client.trace.assert_called_once()
            self.assertEqual(mock_client.score.call_count, 2)
            mock_client.flush.assert_called_once()

    def test_langfuse_exception_handled(self):
        with patch('ai.observability.langfuse.get_langfuse_client', side_effect=Exception('conn fail')):
            log_scores_to_langfuse({'precision_at_5': 0.5}, 100.0)
