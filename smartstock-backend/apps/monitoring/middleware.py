import logging
import threading
import time
from collections import deque

from django.utils.deprecation import MiddlewareMixin

from .metrics import (
    ERROR_COUNT,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    set_current_error_rate,
    set_current_p95_latency,
)

logger = logging.getLogger(__name__)

# Sliding window for latency samples (last 5 minutes of requests)
_LATENCY_WINDOW_MAX = 5000
_latency_samples: deque = deque(maxlen=_LATENCY_WINDOW_MAX)
_lock = threading.Lock()

# Counters for error rate computation over the evaluation window
_total_requests_window: int = 0
_error_requests_window: int = 0
_window_start: float = time.time()
_ERROR_RATE_WINDOW_SECONDS: float = 300  # 5 minutes


def _compute_p95(samples: list) -> float:
    if not samples:
        return 0.0
    sorted_samples = sorted(samples)
    idx = int(len(sorted_samples) * 0.95)
    return sorted_samples[min(idx, len(sorted_samples) - 1)]


class PrometheusMetricsMiddleware(MiddlewareMixin):
    """Collects request latency, request count, and error count for Prometheus.

    Computes P95 latency and error rate over a sliding window and syncs
    them to Prometheus Gauges so alert rules can fire.
    """

    UNSUPPORTED_PATHS = ('/metrics', '/admin/', '/api/docs/', '/api/schema/')

    def process_request(self, request):
        request._prom_start_time = time.time()

    def process_response(self, request, response):
        if any(request.path.startswith(p) for p in self.UNSUPPORTED_PATHS):
            return response

        start_time = getattr(request, '_prom_start_time', None)
        if start_time is None:
            return response

        duration = time.time() - start_time
        method = request.method
        endpoint = self._normalise_path(request.path)
        status_code = str(response.status_code)

        REQUEST_LATENCY.labels(method=method, endpoint=endpoint, status_code=status_code).observe(
            duration
        )
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

        if response.status_code >= 400:
            ERROR_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

        # Update sliding window for P95 computation
        with _lock:
            _latency_samples.append(duration)
            set_current_p95_latency(_compute_p95(list(_latency_samples)))

        # Update error rate over sliding window
        self._update_error_rate(response.status_code >= 400)

        return response

    def _update_error_rate(self, is_error: bool):
        global _total_requests_window, _error_requests_window, _window_start

        now = time.time()
        with _lock:
            # Reset window if expired
            if now - _window_start > _ERROR_RATE_WINDOW_SECONDS:
                _total_requests_window = 0
                _error_requests_window = 0
                _window_start = now

            _total_requests_window += 1
            if is_error:
                _error_requests_window += 1

            if _total_requests_window > 0:
                rate = _error_requests_window / _total_requests_window
                set_current_error_rate(rate)

    @staticmethod
    def _normalise_path(path):
        """Collapse dynamic path segments to avoid high-cardinality labels."""
        parts = path.strip('/').split('/')
        normalised = []
        for part in parts:
            if part.isdigit():
                normalised.append('{id}')
            else:
                normalised.append(part)
        return '/' + '/'.join(normalised) if normalised else '/'
