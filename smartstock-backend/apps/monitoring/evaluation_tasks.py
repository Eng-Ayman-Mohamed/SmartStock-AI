"""MQ8 — Daily evaluation Celery tasks.

Runs Retrieval Precision@5 and Answer Faithfulness against the golden dataset,
logs scores to Langfuse, and exposes metrics via Prometheus.
"""

import logging
import time

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    acks_late=True,
)
def run_daily_evaluation_task(self):
    """Daily evaluation task scheduled at 03:00 UTC via Celery Beat.

    Loads the golden dataset, executes evaluations, computes metrics,
    uploads results to Langfuse, and logs failures.
    """
    from ai.evaluation.metrics import evaluate_golden_dataset, log_scores_to_langfuse

    from .metrics import (
        EVALUATION_FAITHFULNESS_GAUGE,
        EVALUATION_PRECISION_GAUGE,
        EVALUATION_TIMESTAMP_GAUGE,
    )

    start = time.time()
    try:
        logger.info('Starting daily evaluation run')

        results = evaluate_golden_dataset(retrieval_fn=None)

        duration_ms = (time.time() - start) * 1000

        log_scores_to_langfuse(results, duration_ms)

        EVALUATION_PRECISION_GAUGE.set(results.get('precision_at_5', 0.0))
        EVALUATION_FAITHFULNESS_GAUGE.set(results.get('faithfulness', 0.0))
        EVALUATION_TIMESTAMP_GAUGE.set(time.time())

        logger.info(
            'Daily evaluation completed: precision_at_5=%.4f, faithfulness=%.4f, '
            'total_queries=%d, duration_ms=%.0f',
            results.get('precision_at_5', 0),
            results.get('faithfulness', 0),
            results.get('total_queries', 0),
            duration_ms,
        )

        return {
            'status': 'success',
            'precision_at_5': results.get('precision_at_5'),
            'faithfulness': results.get('faithfulness'),
            'total_queries': results.get('total_queries'),
            'successful_queries': results.get('successful_queries'),
            'duration_ms': round(duration_ms),
        }

    except Exception as exc:
        logger.exception('Daily evaluation task failed: %s', exc)
        try:
            self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error('Daily evaluation task exceeded max retries')
        return {
            'status': 'failure',
            'error': str(exc),
            'duration_ms': round((time.time() - start) * 1000),
        }
