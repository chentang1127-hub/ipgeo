"""
Billing: credit deduction and usage tracking.

All deduction is done via Redis Lua scripts to guarantee atomicity.
"""

import time
import logging
from datetime import datetime, timezone

from .redis_client import get_redis

logger = logging.getLogger(__name__)

# Plan quotas (lookups per month)
# Aligned with competitive analysis: ip-api.com Pro €13.30/mo unlimited.
# IPGeo differentiates on data quality (Pro+ uses paid GeoIP2, 95%+ city fill).
PLAN_QUOTAS = {
    "free": 10_000,
    "starter": 100_000,
    "pro": 500_000,
    "business": 1_000_000,
    "enterprise": 0,  # unmetered
}


async def deduct(user_id: str, plan: str, count: int = 1) -> bool:
    """
    Atomic credit deduction.

    Returns True on success, False if the user has exhausted their quota.
    Enterprise plans always succeed.
    """
    if plan == "enterprise":
        return True

    redis = get_redis()
    month_str = datetime.now(timezone.utc).strftime("%Y-%m")
    usage_key = f"ipgeo:user:{user_id}:usage:{month_str}"
    credits_key = f"ipgeo:user:{user_id}:credits"
    plan_key = f"ipgeo:user:{user_id}:plan"

    lua = """
    local plan   = ARGV[1]
    local count  = tonumber(ARGV[2])
    local usage  = KEYS[1]
    local credits_key = KEYS[2]

    local quotas = {
        free      = 10000,
        starter   = 100000,
        pro       = 500000,
        business  = 1000000
    }
    local quota = quotas[plan] or 10000

    local used = tonumber(redis.call('GET', usage) or '0')

    -- Within monthly quota
    if used + count <= quota then
        redis.call('INCRBY', usage, count)
        redis.call('EXPIRE', usage, 86400 * 40)  -- keep ~40 days
        return 1
    end

    -- Monthly quota exhausted; try prepaid credits
    local overage = (used + count) - quota
    local credits = tonumber(redis.call('GET', credits_key) or '0')

    if credits >= overage then
        -- Use all remaining monthly quota + overage from credits
        if used < quota then
            redis.call('SET', usage, quota)
        end
        redis.call('DECRBY', credits_key, overage)
        redis.call('EXPIRE', usage, 86400 * 40)
        return 1
    end

    return 0  -- Insufficient balance
    """

    result = await redis.eval(lua, 2, usage_key, credits_key, plan, count)
    success = bool(result)

    if not success:
        logger.warning("Billing: user=%s plan=%s quota exhausted", user_id, plan)

    return success


async def add_credits(user_id: str, amount: int) -> int:
    """Add prepaid credits to a user account.  Returns new balance."""
    redis = get_redis()
    return await redis.incrby(f"ipgeo:user:{user_id}:credits", amount)


async def get_balance(user_id: str) -> int:
    """Get remaining prepaid credits."""
    redis = get_redis()
    return int(await redis.get(f"ipgeo:user:{user_id}:credits") or 0)


async def get_usage(user_id: str) -> dict:
    """Return current month's usage snapshot."""
    redis = get_redis()
    plan = await redis.get(f"ipgeo:user:{user_id}:plan") or "free"
    month_str = datetime.now(timezone.utc).strftime("%Y-%m")
    used = int(await redis.get(f"ipgeo:user:{user_id}:usage:{month_str}") or 0)
    credits = await get_balance(user_id)
    quota = PLAN_QUOTAS.get(plan, 1000)

    return {
        "plan": plan,
        "monthly_quota": quota,
        "monthly_used": used,
        "remaining_quota": max(0, quota - used),
        "prepaid_credits": credits,
    }


async def set_plan(user_id: str, plan: str) -> None:
    """Change a user's subscription plan."""
    if plan not in PLAN_QUOTAS:
        raise ValueError(f"Unknown plan: {plan}")
    redis = get_redis()
    await redis.set(f"ipgeo:user:{user_id}:plan", plan)
