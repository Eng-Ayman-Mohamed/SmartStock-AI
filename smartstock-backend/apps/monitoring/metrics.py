"""Prometheus metrics for the SmartStock monitoring subsystem.

All P95 latency and error-rate calculations are done by Prometheus via
histogram_quantile() and rate() respectively.  No process-local state
is used — every metric is process-safe by construction because
prometheus_client's Counter/Gauge/Histogram use locks internally and
prometheus multiprocess mode (PROMETHEUS_MULTIPROC_DIR) aggregates
across workers automatically.
"""

from prometheus_client import Counter, Gauge, Histogram

# ---------------------------------------------------------------------------
# Request metrics — Histogram + Counters only.
# Prometheus computes P95 via histogram_quantile(0.95, rate(..._bucket[5m]))
# and error rate via sum(rate(..._total[5m])) / sum(rate(http_requests_total[5m])).
# ---------------------------------------------------------------------------
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint', 'status_code'],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 30.0),
)

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
)

ERROR_COUNT = Counter(
    'http_errors_total',
    'Total HTTP error responses (4xx + 5xx)',
    ['method', 'endpoint', 'status_code'],
)

# ---------------------------------------------------------------------------
# AI / Token metrics
# ---------------------------------------------------------------------------
TOKEN_USAGE_TOTAL = Counter(
    'ai_token_usage_total',
    'Total AI tokens consumed',
    ['type'],  # input / output / total
)

DAILY_TOKEN_USAGE = Gauge(
    'ai_daily_token_usage',
    'Cumulative token usage for the current day (updated by Celery task)',
)

TOKEN_DAILY_BUDGET = Gauge(
    'ai_token_daily_budget',
    'Configured daily token budget',
)

# ---------------------------------------------------------------------------
# Agent metrics
# ---------------------------------------------------------------------------
AGENT_RUN_TOTAL = Counter(
    'ai_agent_runs_total',
    'Total AI agent runs',
    ['agent_name', 'outcome'],  # outcome: success / failure
)

AGENT_SUCCESS_RATE_GAUGE = Gauge(
    'ai_agent_success_rate_current',
    'Current agent success rate over evaluation window (updated by Celery task)',
)

# ---------------------------------------------------------------------------
# Evaluation metrics (set by daily evaluation task)
# ---------------------------------------------------------------------------
EVALUATION_PRECISION_GAUGE = Gauge(
    'evaluation_retrieval_precision_at_5',
    'Retrieval Precision@5 from golden dataset evaluation',
)

EVALUATION_FAITHFULNESS_GAUGE = Gauge(
    'evaluation_answer_faithfulness',
    'Answer Faithfulness score from golden dataset evaluation',
)

EVALUATION_TIMESTAMP_GAUGE = Gauge(
    'evaluation_last_timestamp_seconds',
    'Unix timestamp of the last evaluation run',
)
