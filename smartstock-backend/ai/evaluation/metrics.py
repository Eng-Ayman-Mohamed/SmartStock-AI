"""
MQ8 — Langfuse Evaluation Metrics

Implements:
- Retrieval Precision@5 using the golden dataset
- Answer Faithfulness scoring
- Langfuse score logging
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

GOLDEN_DATASET_PATH = (
    Path(__file__).resolve().parents[2] / 'tests' / 'golden_dataset' / 'nl_queries.jsonl'
)


def load_golden_dataset() -> list[dict]:
    """Load the golden dataset from the JSONL file."""
    if not GOLDEN_DATASET_PATH.exists():
        logger.error('Golden dataset not found at %s', GOLDEN_DATASET_PATH)
        return []
    rows = []
    for line in GOLDEN_DATASET_PATH.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                logger.warning('Skipping malformed line in golden dataset: %s', exc)
    return rows


def compute_retrieval_precision_at_5(retrieved_docs: list[dict], expected_filters: dict) -> float:
    """Compute Precision@5 for a single query.

    ``retrieved_docs`` is a list of dicts with at least 'content' or 'metadata' keys.
    ``expected_filters`` contains expected field/value pairs from the golden dataset.

    Precision@5 = (number of relevant docs in top 5) / 5
    A document is considered relevant if its content or metadata overlaps with
    the expected filter fields/values.
    """
    top_k = retrieved_docs[:5]
    if not top_k:
        return 0.0

    expected_conditions = expected_filters.get('conditions', [])
    if not expected_conditions and not expected_filters:
        return 1.0 if top_k else 0.0

    relevant_count = 0
    for doc in top_k:
        content = (doc.get('content') or '').lower()
        metadata = doc.get('metadata') or {}
        is_relevant = False
        for cond in expected_conditions:
            field = str(cond.get('field', '')).lower()
            value = cond.get('value')
            if isinstance(value, str):
                value = value.lower()
            if field in content or (isinstance(value, str) and value in content):
                is_relevant = True
                break
            meta_val = metadata.get(field)
            if meta_val is not None and str(meta_val).lower() == str(value).lower():
                is_relevant = True
                break
        if is_relevant:
            relevant_count += 1

    return relevant_count / 5.0


def compute_answer_faithfulness(answer: str, context_docs: list[dict]) -> float:
    """Compute faithfulness score: how well the answer is grounded in context.

    Uses simple token-overlap heuristic: fraction of answer tokens found in context.
    Returns a score between 0.0 and 1.0.
    """
    if not answer or not context_docs:
        return 0.0

    answer_tokens = set(answer.lower().split())
    context_text = ' '.join((doc.get('content') or '').lower() for doc in context_docs)
    context_tokens = set(context_text.split())

    if not answer_tokens:
        return 0.0

    overlap = answer_tokens & context_tokens
    return len(overlap) / len(answer_tokens)


def evaluate_single_query(query_row: dict, retrieval_fn=None) -> dict:
    """Evaluate a single golden dataset query.

    Returns dict with precision_at_5, faithfulness, and metadata.
    """
    query = query_row['query']
    expected_filters = query_row.get('expected_filters', {})

    retrieved_docs = []
    if retrieval_fn is not None:
        try:
            retrieved_docs = retrieval_fn(query, top_k=5)
        except Exception as exc:
            logger.warning('Retrieval failed for query %s: %s', query_row['id'], exc)

    precision = compute_retrieval_precision_at_5(retrieved_docs, expected_filters)
    faithfulness = compute_answer_faithfulness(query, retrieved_docs)

    return {
        'query_id': query_row['id'],
        'query': query,
        'precision_at_5': precision,
        'faithfulness': faithfulness,
        'retrieved_count': len(retrieved_docs),
    }


def evaluate_golden_dataset(retrieval_fn=None) -> dict:
    """Run full evaluation on the golden dataset.

    Returns aggregated metrics.
    """
    dataset = load_golden_dataset()
    if not dataset:
        return {
            'precision_at_5': 0.0,
            'faithfulness': 0.0,
            'total_queries': 0,
            'successful_queries': 0,
        }

    results = []
    for row in dataset:
        result = evaluate_single_query(row, retrieval_fn=retrieval_fn)
        results.append(result)

    total = len(results)
    avg_precision = sum(r['precision_at_5'] for r in results) / total if total else 0.0
    avg_faithfulness = sum(r['faithfulness'] for r in results) / total if total else 0.0
    successful = sum(1 for r in results if r['retrieved_count'] > 0)

    return {
        'precision_at_5': round(avg_precision, 4),
        'faithfulness': round(avg_faithfulness, 4),
        'total_queries': total,
        'successful_queries': successful,
        'per_query': results,
    }


def log_scores_to_langfuse(evaluation_results: dict, duration_ms: float) -> None:
    """Log evaluation scores to Langfuse."""
    try:
        from ai.observability.langfuse import get_langfuse_client

        client = get_langfuse_client()
        if client is None:
            logger.info('Langfuse client unavailable — skipping score logging')
            return

        trace = client.trace(
            name='daily_evaluation',
            input={'type': 'golden_dataset_evaluation'},
            output={
                'precision_at_5': evaluation_results.get('precision_at_5'),
                'faithfulness': evaluation_results.get('faithfulness'),
                'total_queries': evaluation_results.get('total_queries'),
                'successful_queries': evaluation_results.get('successful_queries'),
            },
            metadata={
                'duration_ms': duration_ms,
                'evaluation_type': 'daily_golden_dataset',
            },
        )

        client.score(
            trace_id=trace.id,
            name='retrieval_precision_at_5',
            value=evaluation_results.get('precision_at_5', 0.0),
        )

        client.score(
            trace_id=trace.id,
            name='answer_faithfulness',
            value=evaluation_results.get('faithfulness', 0.0),
        )

        client.flush()
        logger.info(
            'Langfuse scores logged: precision_at_5=%.4f, faithfulness=%.4f',
            evaluation_results.get('precision_at_5', 0),
            evaluation_results.get('faithfulness', 0),
        )
    except Exception as exc:
        logger.exception('Failed to log scores to Langfuse: %s', exc)
