"""
API key authentication.

Key format:   ipgeo_<random 32 hex chars>
Storage:      SHA-256 hash → user_id  (never store plaintext)
              60-second process-local LRU cache to reduce Redis load.
"""

import hashlib
import secrets
import time
from typing import Optional

from fastapi import Request, HTTPException

from .redis_client import get_redis

KEY_PREFIX = "ipgeo_"
AUTH_HEADER = "X-API-Key"

# Process-local cache
_cache: dict[str, dict] = {}          # key → {"id":..., "plan":...}
_cache_ts: dict[str, float] = {}      # key → insertion timestamp
_cache_ttl = 60.0                      # seconds


def generate() -> str:
    """Generate a new API key.  Return the plaintext (show it once)."""
    return f"{KEY_PREFIX}{secrets.token_hex(32)}"


def hash_body(api_key: str) -> str:
    """SHA-256 of the key body (strip prefix if present)."""
    body = api_key.removeprefix(KEY_PREFIX)
    return hashlib.sha256(body.encode()).hexdigest()


async def validate(api_key: str) -> Optional[dict]:
    """
    Validate an API key.  Returns {"id": ..., "plan": ...} or None.
    """
    if not api_key or not api_key.startswith(KEY_PREFIX):
        return None

    # 1. Local cache
    entry = _cache.get(api_key)
    if entry:
        return entry

    # 2. Redis
    redis = get_redis()
    key_hash = hash_body(api_key)
    user_id = await redis.get(f"ipgeo:key:{key_hash}")

    if user_id is None:
        return None

    plan = await redis.get(f"ipgeo:user:{user_id}:plan") or "free"
    user = {"id": user_id, "plan": plan}

    # 3. Populate cache
    _cache[api_key] = user
    _cache_ts[api_key] = time.time()
    _evict_stale()

    return user


async def authenticate(request: Request) -> dict:
    """
    FastAPI dependency: extract and validate API key.

    Usage:
        @app.get("/v1/ip/{ip}")
        async def lookup(ip: str, user = Depends(authenticate)):
            ...
    """
    api_key = (
        request.headers.get(AUTH_HEADER)
        or request.query_params.get("api_key")
    )

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    user = await validate(api_key)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return user


async def create(user_id: str, plan: str = "free") -> str:
    """Create a new API key for a user.  Returns the plaintext."""
    redis = get_redis()
    key = generate()
    hashed = hash_body(key)
    await redis.set(f"ipgeo:key:{hashed}", user_id)
    await redis.set(f"ipgeo:user:{user_id}:plan", plan)
    return key


async def revoke(api_key: str) -> bool:
    """Delete an API key."""
    redis = get_redis()
    hashed = hash_body(api_key)
    deleted = await redis.delete(f"ipgeo:key:{hashed}")
    _cache.pop(api_key, None)
    _cache_ts.pop(api_key, None)
    return bool(deleted)


def _evict_stale() -> None:
    """Remove cache entries older than _cache_ttl."""
    now = time.time()
    stale = [k for k, ts in _cache_ts.items() if now - ts > _cache_ttl]
    for k in stale:
        _cache.pop(k, None)
        _cache_ts.pop(k, None)
