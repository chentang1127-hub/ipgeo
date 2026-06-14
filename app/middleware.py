"""
ASGI middleware — HTTP-level metrics for every request.

Records:
    ipgeo_http_requests_total{method, path, status}
    ipgeo_http_request_duration_seconds{method, path}
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware

from .metrics import http_requests_total, http_request_duration_seconds, normalize_path


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record HTTP-level request count + duration for every request."""

    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        path = normalize_path(request.url.path)
        method = request.method
        status = response.status_code

        http_requests_total.labels(method=method, path=path, status=status).inc()
        http_request_duration_seconds.labels(method=method, path=path).observe(duration)

        return response
