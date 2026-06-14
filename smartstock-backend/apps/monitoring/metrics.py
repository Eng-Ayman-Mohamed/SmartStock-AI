from prometheus_client import Counter, Gauge, Histogram

# --- Request metrics ---
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

# --- AI / Token metrics ---
TOKEN_USAGE_TOTAL = Counter(
    'ai_token_usage_total',
    'Total AI tokens consumed',
    ['type'],  # input / output / total
)

DAILY_TOKEN_USAGE = Gauge(
    'ai_daily_token_usage',
    'Cumulative token usage for the current day',
)

TOKEN_DAILY_BUDGET = Gauge(
    'ai_token_daily_budget',
    'Configured daily token budget',
)

# --- Agent metrics ---
AGENT_RUN_TOTAL = Counter(
    'ai_agent_runs_total',
    'Total AI agent runs',
    ['agent_name', 'outcome'],  # outcome: success / failure
)

# --- Alerting gauges (Prometheus alert rules query these) ---
P95_LATENCY = Gauge(
    'http_request_p95_latency_seconds',
    'P95 request latency over the evaluation window',
)

ERROR_RATE = Gauge(
    'http_error_rate',
    'Current application error rate (errors / total requests)',
)

DAILY_TOKEN_SPEND = Gauge(
    'ai_daily_token_spend',
    'Current daily token spend count',
)

AGENT_SUCCESS_RATE_GAUGE = Gauge(
    'ai_agent_success_rate_current',
    'Current agent success rate over evaluation window',
)

# --- Tracked values (updated by middleware / tasks, read by alert evaluators) ---
# prometheus_client Gauge._value is a private implementation detail.
# We maintain plain Python counters that are synced to Gauges periodically.
_current_p95_latency: float = 0.0
_current_error_rate: float = 0.0
_current_daily_token_budget: float = 1_000_000.0


def get_current_p95_latency() -> float:
    return _current_p95_latency


def set_current_p95_latency(value: float) -> None:
    global _current_p95_latency
    _current_p95_latency = value
    P95_LATENCY.set(value)


def get_current_error_rate() -> float:
    return _current_error_rate


def set_current_error_rate(value: float) -> None:
    global _current_error_rate
    _current_error_rate = value
    ERROR_RATE.set(value)


def get_current_daily_token_budget() -> float:
    return _current_daily_token_budget


def set_current_daily_token_budget(value: float) -> None:
    global _current_daily_token_budget
    _current_daily_token_budget = value
    TOKEN_DAILY_BUDGET.set(value)
