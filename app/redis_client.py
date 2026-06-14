"""
Redis connection singleton — with in-memory dev mode fallback.

In dev mode (IPGEO_ENVIRONMENT=development, no Redis URL), uses an
in-process dict store that mimics the Redis API surface we need.
"""

import asyncio
import logging
from typing import Optional

from .config import get_settings

logger = logging.getLogger(__name__)

_pool = None  # redis.Redis or InMemoryStore


class InMemoryStore:
    """
    Minimal Redis-compatible in-memory store for local development.

    Supports: get, set, delete, exists, incrby, decrby, eval (Lua subset),
              aclose, ping.
    Lua subset supported:
      - billing.deduct script (atomic GET/SET/INCRBY/DECRBY/EXPIRE)
      - ratelimit.check  script (ZREMRANGEBYSCORE/ZCARD/ZADD/EXPIRE)
    """

    def __init__(self):
        self._data: dict[str, str] = {}
        # Sorted sets: key -> {member: score}
        self._zsets: dict[str, dict[str, float]] = {}
        self._lock = asyncio.Lock()

    async def ping(self) -> bool:
        return True

    async def get(self, key: str) -> Optional[str]:
        return self._data.get(key)

    async def set(self, key: str, value: str, *args, **kwargs) -> bool:
        self._data[key] = value
        return True

    async def delete(self, key: str) -> int:
        return 1 if self._data.pop(key, None) is not None else 0

    async def exists(self, key: str) -> bool:
        return key in self._data

    async def incrby(self, key: str, amount: int) -> int:
        val = int(self._data.get(key, 0)) + amount
        self._data[key] = str(val)
        return val

    async def incr(self, key: str) -> int:
        return await self.incrby(key, 1)

    async def keys(self, pattern: str = "*") -> list:
        """Minimal glob: only supports * at start/end of prefix/suffix."""
        import fnmatch
        return [k for k in self._data if fnmatch.fnmatch(k, pattern)]

    async def decrby(self, key: str, amount: int) -> int:
        return await self.incrby(key, -amount)

    async def hincrby(self, key: str, field: str, amount: int = 1) -> int:
        """Increment a field in a hash. Creates the hash if needed."""
        hash_key = f"_hash:{key}"
        if hash_key not in self._data:
            self._data[hash_key] = {}
        import json
        try:
            h = json.loads(self._data[hash_key])
        except (json.JSONDecodeError, TypeError):
            h = {}
        val = h.get(field, 0) + amount
        h[field] = val
        self._data[hash_key] = json.dumps(h)
        return val

    async def aclose(self) -> None:
        pass

    async def eval(self, script: str, numkeys: int, *args) -> int | list:
        """
        Minimal Lua subset for billing & ratelimit scripts.
        We parse just enough to run our two scripts.
        """
        async with self._lock:
            # --- Billing script (numkeys=2) ---
            # KEYS[1] = usage key, KEYS[2] = credits key
            # ARGV[1] = plan, ARGV[2] = count
            if "ZREMRANGEBYSCORE" not in script and "quota" in script.lower():
                return self._eval_billing(script, args)

            # --- Rate-limit script (numkeys=1) ---
            # KEYS[1] = ratelimit key
            # ARGV[1] = now, ARGV[2] = window, ARGV[3] = limit, ARGV[4] = count
            if "ZREMRANGEBYSCORE" in script and "ZCARD" in script:
                return self._eval_ratelimit(script, args)

            logger.warning("Unknown Lua script, returning 0")
            return 0

    def _eval_billing(self, _script: str, args: list) -> int:
        # eval() called as: redis.eval(lua, 2, usage_key, credits_key, plan, count)
        # args = (usage_key, credits_key, plan, count) — 0-based indexing
        usage_key = args[0]
        credits_key = args[1]
        plan = args[2]
        count = int(args[3])

        quotas = {
            "free": 10_000,
            "starter": 100_000,
            "pro": 250_000,
            "business": 1_000_000,
        }
        quota = quotas.get(plan, 10_000)

        used = int(self._data.get(usage_key, 0))
        if used + count <= quota:
            self._data[usage_key] = str(used + count)
            return 1

        overage = (used + count) - quota
        credits = int(self._data.get(credits_key, 0))
        if credits >= overage:
            if used < quota:
                self._data[usage_key] = str(quota)
            self._data[credits_key] = str(credits - overage)
            return 1

        return 0

    def _eval_ratelimit(self, _script: str, args: list) -> int:
        # eval() called as: redis.eval(lua, 1, key, now, window, limit, count)
        # args = (key, now, window, limit, count) — 0-based indexing
        key = args[0]
        now = float(args[1])
        window = float(args[2])
        limit = int(args[3])
        count = int(args[4])

        if key not in self._zsets:
            self._zsets[key] = {}

        zset = self._zsets[key]

        # Remove expired
        expired = [m for m, s in zset.items() if s < now - window]
        for m in expired:
            del zset[m]

        current = len(zset)
        if current + count > limit:
            return 0

        for i in range(count):
            member = f"{now}:{i}:{current + i}"
            zset[member] = now + i * 0.000001

        return 1


async def init_redis() -> None:
    """Create Redis connection, or in-memory store in dev mode."""
    global _pool
    settings = get_settings()

    if settings.redis_url == "redis://localhost:6379/0" and not settings.is_production:
        # Dev mode — no Redis configured, use in-memory store
        logger.info("Using in-memory store (dev mode).  Set IPGEO_REDIS_URL for Redis.")
        _pool = InMemoryStore()
    else:
        import redis.asyncio as redis

        _pool = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            health_check_interval=30,
        )
        await _pool.ping()
        logger.info("Redis connected: %s", settings.redis_url)


async def close_redis() -> None:
    global _pool
    if _pool:
        await _pool.aclose()
        _pool = None


def get_redis():
    if _pool is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _pool
