"""
Prometheus metrics for IPGeo — HTTP-level (middleware) + business-level.

HTTP metrics:
    ipgeo_http_requests_total{method, path, status}
    ipgeo_http_request_duration_seconds{method, path}

Business metrics:
    ipgeo_lookups_total{endpoint, plan, status}
    ipgeo_lookup_duration_seconds{endpoint}
    ipgeo_auth_failures_total{reason}
    ipgeo_rate_limit_hits_total{plan}
    ipgeo_registrations_total{plan, method}

Analytics events (fired from website JS):
    ipgeo_analytics_events_total{event, page}
"""

from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

# Custom registry — no Python GC / process noise, only our metrics.
REGISTRY = CollectorRegistry(auto_describe=False)

# ---------------------------------------------------------------------------
# HTTP-level (recorded by middleware — every request)
# ---------------------------------------------------------------------------
http_requests_total = Counter(
    "ipgeo_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
    registry=REGISTRY,
)
http_request_duration_seconds = Histogram(
    "ipgeo_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# App-level — lookups
# ---------------------------------------------------------------------------
lookups_total = Counter(
    "ipgeo_lookups_total",
    "Total IP lookups",
    ["endpoint", "plan", "status"],
    registry=REGISTRY,
)
lookup_duration_seconds = Histogram(
    "ipgeo_lookup_duration_seconds",
    "Lookup duration in seconds",
    ["endpoint"],
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Business — auth & rate limit
# ---------------------------------------------------------------------------
auth_failures_total = Counter(
    "ipgeo_auth_failures_total",
    "Authentication failures",
    ["reason"],
    registry=REGISTRY,
)
rate_limit_hits_total = Counter(
    "ipgeo_rate_limit_hits_total",
    "Rate limit blocks",
    ["plan", "type"],  # type = ratelimit | quota
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Business — registrations
# ---------------------------------------------------------------------------
registrations_total = Counter(
    "ipgeo_registrations_total",
    "New user registrations",
    ["plan", "method"],  # method = free | claim | lemonsqueezy
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Website analytics events
# ---------------------------------------------------------------------------
analytics_events_total = Counter(
    "ipgeo_analytics_events_total",
    "Website analytics events",
    ["event", "page"],
    registry=REGISTRY,
)


def render() -> bytes:
    """Generate Prometheus text from our registry (no Python GC / process noise)."""
    return generate_latest(REGISTRY)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def record_lookup(endpoint: str, plan: str, status: str = "ok", count: int = 1):
    lookups_total.labels(endpoint=endpoint, plan=plan, status=status).inc(count)


def record_lookup_duration(endpoint: str):
    """Context-manager timer for lookup operations.

    Usage:
        with record_lookup_duration("lookup"):
            result = geo.lookup(ip)
    """
    return lookup_duration_seconds.labels(endpoint=endpoint).time()


def record_auth_failure(reason: str):
    auth_failures_total.labels(reason=reason).inc()


def record_rate_limit_hit(plan: str, limit_type: str):
    rate_limit_hits_total.labels(plan=plan, type=limit_type).inc()


def record_registration(plan: str, method: str):
    registrations_total.labels(plan=plan, method=method).inc()


def record_analytics_event(event: str, page: str = "/"):
    analytics_events_total.labels(event=event, page=page).inc()


# Path normalisation — collapse dynamic segments so Prometheus
# cardinality stays bounded.
#
#   /v1/ip/8.8.8.8           → /v1/ip/{ip}
#   /v1/ip/2001:db8::1        → /v1/ip/{ip}
#   /v1/ip/me                 → /v1/ip/me
#   /v1/ip/batch              → /v1/ip/batch
#   /v1/auth/register-free    → /v1/auth/register-free
#   /v1/auth/claim-by-email   → /v1/auth/claim-by-email
#   /v1/auth/register         → /v1/auth/register
#   /v1/auth/claim            → /v1/auth/claim
#   /v1/usage                 → /v1/usage
#   /v1/health                → /v1/health
#   /metrics                  → /metrics
#   /docs /openapi.json       → /docs /openapi.json
#   /v1/analytics/event       → /v1/analytics/event
#   /v1/admin/keys            → /v1/admin/keys
#   /v1/webhooks/lemonsqueezy → /v1/webhooks/lemonsqueezy
#

_V1_STATIC_PREFIXES = (
    "/v1/ip/me",
    "/v1/ip/batch",
    "/v1/usage",
    "/v1/health",
    "/v1/auth/",
    "/v1/admin/",
    "/v1/webhooks/",
    "/v1/analytics/",
)


def normalize_path(path: str) -> str:
    """Collapse dynamic path segments for Prometheus label cardinality."""
    # Static routes under /v1
    for prefix in _V1_STATIC_PREFIXES:
        if path.startswith(prefix):
            return path

    # /v1/ip/{ip}  →  /v1/ip/{ip}
    if path.startswith("/v1/ip/"):
        return "/v1/ip/{ip}"

    # /docs, /redoc, /openapi.json — keep as-is (low cardinality)
    return path
