"""Prometheus request metrics middleware.

Records request count, error count, and latency via standard Prometheus
Counter and Histogram primitives.  P95 latency and error rate are computed
by Prometheus using histogram_quantile() and rate() — no process-local
state is maintained.
"""

import logging
import re
import time

from django.utils.deprecation import MiddlewareMixin

from .metrics import ERROR_COUNT, REQUEST_COUNT, REQUEST_LATENCY

logger = logging.getLogger(__name__)

# Pre-compiled patterns for path normalisation.
_UUID_RE = re.compile(
    r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
)
NumericSegment = re.compile(r'^\d+$')

UNSUPPORTED_PATHS = ('/metrics', '/admin/', '/api/docs/', '/api/schema/')


def _normalise_path(path: str) -> str:
    """Collapse dynamic path segments to avoid high-cardinality labels.

    - Numeric IDs → {id}
    - UUIDs        → {id}
    - Everything else is kept as-is.
    """
    stripped = path.strip('/')
    if not stripped:
        return '/'

    parts = stripped.split('/')
    normalised: list[str] = []
    for part in parts:
        if _UUID_RE.fullmatch(part) or NumericSegment.fullmatch(part):
            normalised.append('{id}')
        else:
            normalised.append(part)
    return '/' + '/'.join(normalised)


class PrometheusMetricsMiddleware(MiddlewareMixin):
    """Collects request latency, request count, and error count for Prometheus.

    All state lives inside prometheus_client primitives (Counter, Histogram)
    which are either process-safe by construction or aggregated by the
    Prometheus client library when PROMETHEUS_MULTIPROC_DIR is set.
    """

    def process_request(self, request):
        request._prom_start_time = time.time()

    def process_response(self, request, response):
        if any(request.path.startswith(p) for p in UNSUPPORTED_PATHS):
            return response

        start_time = getattr(request, '_prom_start_time', None)
        if start_time is None:
            return response

        duration = time.time() - start_time
        method = request.method
        endpoint = _normalise_path(request.path)
        status_code = str(response.status_code)

        REQUEST_LATENCY.labels(method=method, endpoint=endpoint, status_code=status_code).observe(
            duration
        )
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

        if response.status_code >= 400:
            ERROR_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()

        return response
