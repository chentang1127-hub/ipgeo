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
import json
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST

from .config import get_settings
from .geodb import GeoReader
from .redis_client import init_redis, close_redis, get_redis
from .middleware import MetricsMiddleware
from . import auth
from . import billing
from .billing import PLAN_QUOTAS
from . import metrics as m
from . import ratelimit
from . import rapidapi
from . import risk
from . import webhooks

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
geo: Optional[GeoReader] = None
_uptime_task: Optional["asyncio.Task"] = None


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global geo, _uptime_task
    settings = get_settings()

    logging.basicConfig(
        level=logging.INFO if settings.is_production else debugging,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    await init_redis()
    geo = GeoReader()
    risk.init_risk()

    # Persist server start time for uptime display (public stats)
    try:
        redis = get_redis()
        await redis.set("ipgeo:stats:started_at", str(time.time()))
        # Initialize uptime tracking if not present
        if not await redis.exists("ipgeo:stats:health_checks_total"):
            await redis.set("ipgeo:stats:health_checks_total", "0")
            await redis.set("ipgeo:stats:health_checks_failed", "0")
    except Exception:
        pass

    # Start background uptime heartbeat
    import asyncio
    _uptime_task = asyncio.create_task(_uptime_heartbeat())

    logger.info("IPGeo v%s started (env=%s)", app.version, settings.environment)

    yield

    if _uptime_task:
        _uptime_task.cancel()
    if geo:
        geo.close()
    await close_redis()
    logger.info("IPGeo shut down")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="IPGeo",
    description="IP geolocation API with built-in security detection — "
    "VPN/proxy/Tor/hosting flags included on every plan, 10K free lookups/month. "
    "Look up country, city, coordinates, ISP, ASN, timezone, and security "
    "flags for any IP address.",
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["X-API-Key", "X-Admin-Token", "Content-Type"],
)
app.add_middleware(MetricsMiddleware)
app.add_middleware(rapidapi.RapidAPIMiddleware)

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
        m.record_rate_limit_hit(plan, "ratelimit")
        raise HTTPException(429, detail="Rate limit exceeded")

    if not await billing.deduct(user_id, plan):
        m.record_rate_limit_hit(plan, "quota")
        raise HTTPException(429, detail="Monthly quota exhausted")

    # Extract real client IP from headers
    client_ip = (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Real-IP")
        or (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
        or request.client.host
    )

    with m.record_lookup_duration("me"):
        result = geo.lookup(client_ip, plan)
    m.record_lookup("me", plan, "ok")
    await _incr_total()
    return result


# Mapping from common flat field names to their v2 response group.
# Allows `?fields=country,city,isp` to work even though country & city
# are nested inside `location` and isp inside `network`.
_V2_FIELD_GROUPS = {
    # location group
    "country": "location", "continent": "location", "city": "location",
    "region": "location", "postal_code": "location", "latitude": "location",
    "longitude": "location", "accuracy_km": "location", "timezone": "location",
    # network group
    "isp": "network", "asn": "network", "type": "network",
    # security group
    "is_tor": "security", "is_vpn": "security",
    "is_proxy": "security", "is_hosting": "security",
    # meta group
    "data_source": "meta", "upgrade": "meta",
}


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

    Response is grouped into `location`, `network`, `security`, `meta`.
    Use `?fields=` to select top-level groups or common field names.
    Examples:
      `?fields=location`          → only the location block
      `?fields=country,city,isp`  → location block + network block
      (no fields param)           → full v2 response

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
        m.record_rate_limit_hit(plan, "ratelimit")
        raise HTTPException(429, detail="Rate limit exceeded. Upgrade at getipgeo.com/pricing")

    # Billing
    if not await billing.deduct(user_id, plan):
        m.record_rate_limit_hit(plan, "quota")
        raise HTTPException(
            429,
            detail="Monthly quota exhausted. Upgrade your plan or add prepaid credits.",
        )

    # Lookup
    with m.record_lookup_duration("lookup"):
        result = geo.lookup(ip, plan)

    # Field filtering — maps flat field names to v2 groups
    if fields:
        raw = {f.strip() for f in fields.split(",")}
        # Resolve: keep top-level group keys as-is, map known fields to their group
        groups = set()
        for f in raw:
            if f in ("ip", "location", "network", "security", "meta"):
                groups.add(f)                     # top-level group
            elif f in _V2_FIELD_GROUPS:
                groups.add(_V2_FIELD_GROUPS[f])   # nested field → its group
        groups.add("ip")
        result = {k: v for k, v in result.items() if k in groups}

    m.record_lookup("lookup", plan, "ok")
    await _incr_total()
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
        m.record_rate_limit_hit(plan, "ratelimit")
        raise HTTPException(429, detail="Rate limit exceeded")

    if not await billing.deduct(user_id, plan, count):
        m.record_rate_limit_hit(plan, "quota")
        raise HTTPException(429, detail="Monthly quota exceeded")

    # Parallel lookups via thread pool
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(lambda ip: geo.lookup(ip, plan), ips))
    m.lookup_duration_seconds.labels(endpoint="batch").observe(time.perf_counter() - t0)

    m.record_lookup("batch", plan, "ok", count)
    await _incr_total(count)
    return {"results": results}


@app.get("/v1/usage")
async def get_usage(user: dict = Depends(auth.authenticate)):
    """
    Return the current billing period's usage.

    ```
    curl -H "X-API-Key: ipgeo_YOUR_KEY" https://api.getipgeo.com/v1/usage
    ```
    """
    return await billing.get_usage(user["id"], user.get("plan"))


@app.get("/v1/health")
async def health():
    """Health check — no auth, no billing. Returns component-level status."""
    components = {}
    overall = "healthy"

    # 1. Database
    db_loaded = geo.loaded if geo else False
    components["database"] = {
        "status": "operational" if db_loaded else "degraded",
        "detail": (
            "City-Level IP Database"
            if db_loaded
            else "Database not loaded"
        ),
    }
    if not db_loaded:
        overall = "degraded"

    # 2. Redis
    try:
        redis = get_redis()
        await redis.ping()
        components["redis"] = {"status": "operational", "detail": "Connected"}
    except Exception:
        components["redis"] = {"status": "degraded", "detail": "Connection failed"}
        overall = "degraded"

    # 3. API
    components["api"] = {"status": "operational", "detail": f"v{app.version}"}

    # 4. Risk detection
    tor_count = len(risk._tor_exits) if risk._tor_exits else 0
    components["risk_detection"] = {
        "status": "operational" if risk._tor_available else "degraded",
        "detail": f"{tor_count} Tor exits tracked" if risk._tor_available else "Initializing",
    }

    return {
        "status": overall,
        "version": app.version,
        "components": components,
        "cache": geo.stats if geo else {},
    }


# ---------------------------------------------------------------------------
# Auth / Registration endpoints
# ---------------------------------------------------------------------------


@app.post("/v1/auth/register-free")
async def auth_register_free(request: Request):
    """
    Register a free plan user directly (no checkout needed).

    Request body:
        { "email": "user@example.com" }

    Response:
        { "api_key": "ipgeo_...", "plan": "free", "user_id": "..." }
    """
    body = await request.json() or {}
    email = (body.get("email") or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, detail="Valid email is required")

    # Check if user already exists
    existing_user_id = await auth.get_user_by_email(email)
    if existing_user_id:
        api_key = await auth.create(existing_user_id, "free")
        return {"api_key": api_key, "plan": "free", "user_id": existing_user_id}

    # New user
    user_id = uuid.uuid4().hex[:16]
    await auth.store_user_email(user_id, email)
    await billing.set_plan(user_id, "free")
    api_key = await auth.create(user_id, "free")

    logger.info("Free registration: user=%s email=%s", user_id, email)
    m.record_registration("free", "free")
    return {"api_key": api_key, "plan": "free", "user_id": user_id}


@app.post("/v1/auth/claim-by-email")
async def auth_claim_by_email(request: Request):
    """
    Claim an API key by email. Fallback when the user loses their checkout_id.

    Request body:
        { "email": "user@example.com" }

    Response:
        { "api_key": "ipgeo_...", "plan": "pro", "user_id": "..." }
    """
    body = await request.json() or {}
    email = (body.get("email") or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, detail="Valid email is required")

    user_id = await auth.get_user_by_email(email)
    if not user_id:
        raise HTTPException(404, detail="No account found for this email. Complete your purchase first.")

    redis = get_redis()
    plan = await redis.get(f"ipgeo:user:{user_id}:plan") or "free"
    api_key = await auth.create(user_id, plan)

    logger.info("Claim-by-email: user=%s plan=%s", user_id, plan)
    m.record_registration(plan, "claim")
    return {"api_key": api_key, "plan": plan, "user_id": user_id}


@app.post("/v1/auth/register")
async def auth_register(request: Request):
    """
    Register a new user before Paddle.js checkout.

    Request body:
        { "email": "user@example.com", "price_id": "pri_01kv2fyaj4ek50cxrbw7f332eh" }

    Response:
        { "user_id": "...", "plan": "pro" }

    The frontend then opens Paddle.Checkout.open() with the price_id
    and custom_data.user_id. After payment, Paddle redirects to
    /success?checkout_id=xxx where the user claims their key.
    """
    body = await request.json() or {}

    email = (body.get("email") or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, detail="Valid email is required")

    price_id = (body.get("price_id") or "").strip()
    if not price_id:
        raise HTTPException(400, detail="price_id is required (plan selection)")

    # Validate price_id maps to a known plan
    settings = get_settings()
    plan = settings.paddle_price_plan_map.get(price_id)
    if not plan:
        raise HTTPException(400, detail=f"Unknown price_id: {price_id}")

    # Check if user already exists by email
    existing_user_id = await auth.get_user_by_email(email)
    if existing_user_id:
        user_id = existing_user_id
    else:
        user_id = uuid.uuid4().hex[:16]
        await auth.store_user_email(user_id, email)

    logger.info("Registration: user=%s email=%s plan=%s", user_id, email, plan)

    return {
        "user_id": user_id,
        "plan": plan,
    }


@app.post("/v1/auth/claim")
async def auth_claim(request: Request):
    """
    Claim an API key after completing Paddle checkout.

    Request body:
        { "checkout_id": "..." }

    Response:
        { "api_key": "ipgeo_...", "plan": "pro", "user_id": "..." }

    Idempotent: repeat calls with the same checkout_id return the SAME key.
    """
    body = await request.json() or {}
    checkout_id = (body.get("checkout_id") or "").strip()

    if not checkout_id:
        raise HTTPException(400, detail="checkout_id is required")

    settings = get_settings()
    redis = get_redis()

    # 0. Idempotency check — already claimed this checkout?
    cached = await redis.get(f"ipgeo:claim:{checkout_id}")
    if cached:
        api_key, plan, user_id = cached.split("|", 2)
        logger.info("Claim: checkout=%s already claimed, returning cached key", checkout_id)
        return {"api_key": api_key, "plan": plan, "user_id": user_id}

    # 1. Verify transaction with Paddle
    txn_info = await webhooks.verify_transaction(checkout_id)
    if txn_info is None:
        raise HTTPException(400, detail="Transaction not found. It may take a moment — please retry.")

    if txn_info.get("status") not in ("completed", "billed"):
        raise HTTPException(
            425,  # Too Early
            detail=f"Payment not yet completed (status: {txn_info['status']}). "
                   "Please retry after the payment processes.",
        )

    user_id = txn_info.get("user_id", "")
    paddle_price_id = txn_info.get("price_id", "")
    plan = settings.paddle_price_plan_map.get(paddle_price_id, "free")

    if not user_id:
        raise HTTPException(400, detail="Could not identify user from checkout. Please contact support.")

    # 2. Provision user
    existing_plan = await redis.get(f"ipgeo:user:{user_id}:plan")
    if existing_plan:
        logger.info("Claim: user=%s already provisioned as %s", user_id, existing_plan)
    else:
        await billing.set_plan(user_id, plan)
        # Also store email from checkout
        email = txn_info.get("email", "")
        if email:
            await auth.store_user_email(user_id, email)
        logger.info("Claim: user=%s provisioned as plan=%s", user_id, plan)

    # 3. Create API key + cache idempotently
    api_key = await auth.create(user_id, plan)
    await redis.setex(f"ipgeo:claim:{checkout_id}", 86400, f"{api_key}|{plan}|{user_id}")

    return {"api_key": api_key, "plan": plan, "user_id": user_id}


# ---------------------------------------------------------------------------
# Analytics event collector (website JS beacon)
# ---------------------------------------------------------------------------

@app.post("/v1/analytics/event")
async def analytics_event(request: Request):
    """
    Collect a website analytics event.  No auth required.

    Request body:
        { "event": "page_view", "page": "/", "referrer": "https://..." }

    Events: page_view, demo_try, pricing_click, signup_start, signup_complete

    Stored in Prometheus + Redis for persistence.
    """
    body = await request.json() or {}
    event = (body.get("event") or "").strip()
    page = (body.get("page") or "/").strip()
    referrer = (body.get("referrer") or "").strip()
    plan = (body.get("plan") or "").strip()  # optional, for pricing clicks
    detail = (body.get("detail") or "").strip()  # arbitrary extra data

    if not event:
        raise HTTPException(400, detail="event is required")

    # Prometheus counter
    m.record_analytics_event(event, page)

    # Persist to Redis for later querying (daily bucketed)
    try:
        from datetime import datetime, timezone
        redis = get_redis()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        pipe = redis if hasattr(redis, 'pipeline') else None
        if hasattr(redis, 'hincrby'):
            key = f"ipgeo:analytics:{today}:{event}"
            await redis.hincrby(key, page, 1)
            if referrer:
                await redis.hincrby(key, f"ref:{referrer}", 1)
    except Exception:
        pass  # analytics persistence is best-effort; never break the request

    return {"ok": True}


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _incr_total(count: int = 1) -> None:
    """Increment the global lookup counter (best-effort)."""
    try:
        redis = get_redis()
        await redis.incrby("ipgeo:stats:total_lookups", count)
    except Exception:
        pass


async def _uptime_heartbeat(interval: int = 60) -> None:
    """Record a health-check heartbeat every `interval` seconds for uptime tracking."""
    import asyncio
    while True:
        try:
            await asyncio.sleep(interval)
            redis = get_redis()
            # Increment total checks
            await redis.incrby("ipgeo:stats:health_checks_total", 1)
            # Run a lightweight self-check
            ok = geo.loaded if geo else False
            if ok:
                try:
                    await redis.ping()
                except Exception:
                    ok = False
            if not ok:
                await redis.incrby("ipgeo:stats:health_checks_failed", 1)
            # Store the latest check timestamp
            await redis.set("ipgeo:stats:last_health_check", str(time.time()))
        except asyncio.CancelledError:
            break
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Public stats (no auth required)
# ---------------------------------------------------------------------------


@app.get("/v1/stats")
async def public_stats():
    """
    Public usage statistics — no auth required.
    Intended for the /public-stats transparency page.
    """
    try:
        redis = get_redis()
        total = int(await redis.get("ipgeo:stats:total_lookups") or "0")
        started = float(await redis.get("ipgeo:stats:started_at") or "0")
    except Exception:
        total = 0
        started = 0.0

    uptime_sec = max(0, time.time() - started)

    # Uptime percentage from heartbeat checks
    uptime_pct = None
    checks_total = 0
    checks_failed = 0
    try:
        checks_total = int(await redis.get("ipgeo:stats:health_checks_total") or "0")
        checks_failed = int(await redis.get("ipgeo:stats:health_checks_failed") or "0")
        if checks_total > 0:
            uptime_pct = round((1 - checks_failed / checks_total) * 100, 2)
    except Exception:
        pass

    return {
        "total_lookups_served": total,
        "uptime_seconds": int(uptime_sec),
        "uptime_days": round(uptime_sec / 86400, 1),
        "uptime_pct": uptime_pct,
        "health_checks_total": checks_total,
        "version": app.version,
        "db_loaded": geo.loaded if geo else False,
        "cache": geo.stats if geo else {},
    }


@app.get("/v1/admin/dashboard")
async def admin_dashboard(request: Request):
    """
    Internal dashboard — requires X-Admin-Token.
    Returns aggregated metrics for the dashboard page.
    """
    settings = get_settings()
    admin_token = request.headers.get("X-Admin-Token")
    if admin_token != settings.admin_token:
        raise HTTPException(403, detail="Invalid admin token")

    from datetime import datetime, timezone, timedelta

    redis = get_redis()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    # --- API calls ---
    total_lookups = int(await redis.get("ipgeo:stats:total_lookups") or "0")

    # --- Registrations (signup_complete) ---
    try:
        signups_raw = await redis.hgetall(f"ipgeo:analytics:{today}:signup_complete") or {}
        signups_today = sum(int(v) for v in signups_raw.values())
    except Exception:
        signups_today = 0

    # --- Pricing clicks ---
    try:
        pricing_raw = await redis.hgetall(f"ipgeo:analytics:{today}:pricing_click") or {}
        pricing_today = sum(int(v) for v in pricing_raw.values())
    except Exception:
        pricing_today = 0

    # --- Demo tries ---
    try:
        demo_raw = await redis.hgetall(f"ipgeo:analytics:{today}:demo_try") or {}
        demo_today = sum(int(v) for v in demo_raw.values())
    except Exception:
        demo_today = 0

    # --- Page views today ---
    try:
        pv_raw = await redis.hgetall(f"ipgeo:analytics:{today}:page_view") or {}
        pv_today = sum(int(v) for v in pv_raw.values())
    except Exception:
        pv_today = 0

    # --- Channel attribution (referrers from page_view, last 7 days) ---
    channels = {}
    for i in range(7):
        d = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        try:
            raw = await redis.hgetall(f"ipgeo:analytics:{d}:page_view") or {}
            for k, v in raw.items():
                if k.startswith("ref:"):
                    ref = k[4:]
                    # Normalize referrer to channel
                    channel = _classify_referrer(ref)
                    channels[channel] = channels.get(channel, 0) + int(v)
        except Exception:
            pass

    # --- User plan distribution ---
    plan_counts = {"free": 0, "starter": 0, "pro": 0, "business": 0}
    try:
        keys = await redis.keys("ipgeo:user:*:plan")
        for key in keys:
            plan = await redis.get(key) or "free"
            plan_counts[plan] = plan_counts.get(plan, 0) + 1
    except Exception:
        pass
    total_users = sum(plan_counts.values())

    # --- GitHub / PyPI / npm (static placeholders, can be updated via API) ---
    gh_stars = int(await redis.get("ipgeo:external:github_stars") or "0")
    pypi_dl = int(await redis.get("ipgeo:external:pypi_downloads") or "0")
    npm_dl = int(await redis.get("ipgeo:external:npm_downloads") or "0")

    return {
        "date": today,
        "lookups": {"total": total_lookups},
        "users": {"total": total_users, "by_plan": plan_counts},
        "today": {
            "signups": signups_today,
            "pricing_clicks": pricing_today,
            "demo_tries": demo_today,
            "page_views": pv_today,
        },
        "channels": channels,
        "external": {
            "github_stars": gh_stars,
            "pypi_downloads": pypi_dl,
            "npm_downloads": npm_dl,
        },
    }


def _classify_referrer(ref: str) -> str:
    """Map a raw referrer URL to a channel label."""
    ref_lower = ref.lower()
    if "google." in ref_lower:
        return "Google Search"
    if "dev.to" in ref_lower:
        return "Dev.to"
    if "reddit.com" in ref_lower:
        return "Reddit"
    if "stackoverflow.com" in ref_lower or "stackexchange.com" in ref_lower:
        return "Stack Overflow"
    if "github.com" in ref_lower:
        return "GitHub"
    if "hackernews" in ref_lower or "news.ycombinator.com" in ref_lower:
        return "Hacker News"
    if "pypi.org" in ref_lower:
        return "PyPI"
    if "npmjs.com" in ref_lower:
        return "npm"
    if "producthunt.com" in ref_lower:
        return "Product Hunt"
    if "twitter.com" in ref_lower or "x.com" in ref_lower:
        return "Twitter / X"
    if "baidu.com" in ref_lower:
        return "Baidu"
    if "csdn.net" in ref_lower:
        return "CSDN"
    if "juejin" in ref_lower:
        return "掘金"
    if "v2ex.com" in ref_lower:
        return "V2EX"
    if "zhihu.com" in ref_lower:
        return "知乎"
    if "t.co" in ref_lower:
        return "Twitter / X"
    if ref_lower.startswith("direct") or not ref_lower:
        return "Direct"
    return "Other"


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(m.render(), media_type=CONTENT_TYPE_LATEST)


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
            "upgrade": {
                "url": "https://getipgeo.com/manual-upgrade",
                "contact": "chentang1127@gmail.com",
            },
        },
    )
