"""
Sliding-window rate limiting.  Per-user, backed by Redis sorted sets.

Plan limits (requests per minute) — aligned with competitive analysis:
    free      60/min
    starter   600/min
    pro       3_000/min
    business  10_000/min
    enterprise  unmetered
"""

import time

from .redis_client import get_redis

PLAN_LIMITS = {
    "free": 60,
    "starter": 600,
    "pro": 3_000,
    "business": 10_000,
    "enterprise": 0,  # unmetered
}

WINDOW = 60  # seconds


async def check(user_id: str, plan: str, count: int = 1) -> bool:
    """
    Return True if the request is within the rate limit.
    Enterprise plans are never limited.
    """
    limit = PLAN_LIMITS.get(plan, 30)
    if limit == 0:
        return True

    redis = get_redis()
    now = time.time()
    key = f"ipgeo:ratelimit:{user_id}:60s"

    lua = """
    local key    = KEYS[1]
    local now    = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local limit  = tonumber(ARGV[3])
    local count  = tonumber(ARGV[4])

    -- Remove expired entries
    redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

    local current = redis.call('ZCARD', key)
    if current + count > limit then
        return 0
    end

    -- Add request(s) with unique microsecond scores
    for i = 1, count do
        redis.call('ZADD', key, now + i * 0.000001,
                   now .. ':' .. i .. ':' .. redis.call('INCR', key .. ':seq'))
    end
    redis.call('EXPIRE', key, window + 10)
    return 1
    """

    result = await redis.eval(lua, 1, key, now, WINDOW, limit, count)
    return bool(result)
