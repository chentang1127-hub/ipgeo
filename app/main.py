"""
IPGeo — Fast IP Geolocation API.

Endpoints:
    GET  /v1/ip/{ip}     Look up a specific IP
    GET  /v1/ip/me       Look up the caller's own IP
    POST /v1/ip/batch    Look up up to 100 IPs at once
    GET  /v1/health      Health check (no auth, no billing)
    GET  /v1/usage       Current billing period usage (auth required)
"""

import ipaddress
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from .config import get_settings
from .geodb import GeoReader
from .redis_client import init_redis, close_redis
from . import auth
from . import billing
from .billing import PLAN_QUOTAS
from . import ratelimit
from . import webhooks

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
lookup_count = Counter(
    "ipgeo_lookups_total", "Total lookups", ["endpoint", "plan", "status"]
)
lookup_duration = Histogram(
    "ipgeo_lookup_duration_seconds",
    "Lookup duration",
    ["endpoint"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
geo: Optional[GeoReader] = None


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global geo
    settings = get_settings()

    logging.basicConfig(
        level=logging.INFO if settings.is_production else logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    await init_redis()
    geo = GeoReader()
    logger.info("IPGeo v%s started (env=%s)", app.version, settings.environment)

    yield

    if geo:
        geo.close()
    await close_redis()
    logger.info("IPGeo shut down")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="IPGeo",
    description="Fast, affordable IP geolocation API. Look up country, city, "
    "coordinates, ISP, ASN, and timezone for any IP address.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/v1/ip/me")
async def lookup_my_ip(
    request: Request,
    user: dict = Depends(auth.authenticate),
):
    """
    Look up the calling client's IP address.  No IP parameter needed.

    ```
    curl -H "X-API-Key: ipgeo_YOUR_KEY" https://api.getipgeo.com/v1/ip/me
    ```
    """
    user_id, plan = user["id"], user["plan"]

    if not await ratelimit.check(user_id, plan):
        raise HTTPException(429, detail="Rate limit exceeded")

    if not await billing.deduct(user_id, plan):
        raise HTTPException(429, detail="Monthly quota exhausted")

    # Extract real client IP from headers
    client_ip = (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Real-IP")
        or (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
        or request.client.host
    )

    result = geo.lookup(client_ip, plan)
    lookup_count.labels(endpoint="me", plan=plan, status="ok").inc()
    return result


@app.get("/v1/ip/{ip}")
async def lookup_ip(
    ip: str,
    request: Request,
    user: dict = Depends(auth.authenticate),
    fields: Optional[str] = Query(
        None, description="Comma-separated return fields, e.g. country,city,network"
    ),
):
    """
    Look up geolocation for an IP address.

    ```
    curl -H "X-API-Key: ipgeo_YOUR_KEY" https://api.getipgeo.com/v1/ip/8.8.8.8
    ```
    """
    # Validate IP format early
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid IP address: {ip}")

    # Rate limit
    user_id, plan = user["id"], user["plan"]
    if not await ratelimit.check(user_id, plan):
        raise HTTPException(429, detail="Rate limit exceeded. Upgrade at getipgeo.com/pricing")

    # Billing
    if not await billing.deduct(user_id, plan):
        raise HTTPException(
            429,
            detail="Monthly quota exhausted. Upgrade your plan or add prepaid credits.",
        )

    # Lookup
    result = geo.lookup(ip, plan)

    # Field filtering
    if fields:
        field_set = {f.strip() for f in fields.split(",")}
        field_set.add("ip")
        result = {k: v for k, v in result.items() if k in field_set}

    lookup_count.labels(endpoint="lookup", plan=plan, status="ok").inc()
    return result


@app.post("/v1/ip/batch")
async def batch_lookup(
    request: Request,
    user: dict = Depends(auth.authenticate),
    ips: list[str] = Query(None),
):
    """
    Look up up to 100 IPs in a single request.  Accepts JSON body:

    ```
    curl -X POST https://api.getipgeo.com/v1/ip/batch \
      -H "X-API-Key: ipgeo_YOUR_KEY" \
      -H "Content-Type: application/json" \
      -d '{"ips": ["8.8.8.8", "1.1.1.1"]}'
    ```
    """
    user_id, plan = user["id"], user["plan"]

    # Read body
    if ips is None:
        body = await request.json()
        ips = body.get("ips", [])

    if not ips:
        raise HTTPException(400, detail="Provide at least one IP in 'ips' array")
    if len(ips) > 100:
        raise HTTPException(400, detail="Maximum 100 IPs per batch request")

    # Validate all IPs
    for ip in ips:
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise HTTPException(400, detail=f"Invalid IP address: {ip}")

    # Rate limit + billing (charge for each IP)
    count = len(ips)
    if not await ratelimit.check(user_id, plan, count):
        raise HTTPException(429, detail="Rate limit exceeded")

    if not await billing.deduct(user_id, plan, count):
        raise HTTPException(429, detail="Monthly quota exceeded")

    # Parallel lookups via thread pool
    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(lambda ip: geo.lookup(ip, plan), ips))

    lookup_count.labels(endpoint="batch", plan=plan, status="ok").inc(count)
    return {"results": results}


@app.get("/v1/usage")
async def get_usage(user: dict = Depends(auth.authenticate)):
    """
    Return the current billing period's usage.

    ```
    curl -H "X-API-Key: ipgeo_YOUR_KEY" https://api.getipgeo.com/v1/usage
    ```
    """
    return await billing.get_usage(user["id"])


@app.get("/v1/health")
async def health():
    """Health check — no auth, no billing."""
    return {
        "status": "ok",
        "version": app.version,
        "db_loaded": geo.loaded if geo else False,
        "cache": geo.stats if geo else {},
    }


# ---------------------------------------------------------------------------
# Admin endpoints (behind ADMIN_TOKEN)
# ---------------------------------------------------------------------------

@app.post("/v1/admin/keys")
async def admin_create_key(request: Request):
    """Create a new API key.  Requires X-Admin-Token header."""
    admin_token = request.headers.get("X-Admin-Token")
    settings = get_settings()
    if admin_token != settings.admin_token:
        raise HTTPException(403, detail="Invalid admin token")

    body = await request.json() or {}
    user_id = body.get("user_id", "admin")
    plan = body.get("plan", "free")
    key = await auth.create(user_id, plan)
    return {"api_key": key, "user_id": user_id, "plan": plan}


@app.delete("/v1/admin/keys")
async def admin_revoke_key(request: Request):
    """Revoke an API key."""
    admin_token = request.headers.get("X-Admin-Token")
    if admin_token != get_settings().admin_token:
        raise HTTPException(403, detail="Invalid admin token")

    body = await request.json() or {}
    api_key = body.get("api_key", "")
    if not api_key:
        raise HTTPException(400, detail="Missing api_key")
    deleted = await auth.revoke(api_key)
    return {"revoked": deleted}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---------------------------------------------------------------------------
# Paddle webhook
# ---------------------------------------------------------------------------


@app.post("/v1/webhooks/paddle")
async def paddle_webhook(request: Request):
    """
    Paddle billing webhook receiver.  Paddle POSTs events here for
    subscription lifecycle: activation, cancellation, renewals, payments.

    Verify the HMAC-SHA256 signature before processing.
    """
    from .config import get_settings

    settings = get_settings()
    raw_body = await request.body()
    signature = request.headers.get("Paddle-Signature", "")

    if not webhooks.verify_signature(raw_body, signature, settings.paddle_webhook_secret):
        raise HTTPException(401, detail="Invalid webhook signature")

    body = await request.json()
    event_type = body.get("event_type", "")
    event_data = body.get("data", {})

    await webhooks.handle_event(event_type, event_data)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.exception_handler(401)
async def on_401(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=401,
        content={
            "error": "unauthorized",
            "message": exc.detail or "Missing or invalid API key",
            "docs": "https://getipgeo.com/docs#authentication",
        },
    )


@app.exception_handler(429)
async def on_429(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limited",
            "message": exc.detail or "Too many requests",
            "docs": "https://getipgeo.com/pricing",
        },
    )
