"""
Subscription expiry checker — run via cron to downgrade expired subscriptions.

Scans Redis for cancelled subscriptions whose effective date has passed
and downgrades them to the free plan.

Usage (inside Docker):
    docker compose exec ipgeo python /app/scripts/check_expired_subs.py

Suggested cron (every hour):
    7 * * * * cd /opt/ipgeo && docker compose exec -T ipgeo python /app/scripts/check_expired_subs.py
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.redis_client import init_redis, close_redis, get_redis
from app.billing import set_plan

logger = logging.getLogger(__name__)

PREFIX = "ipgeo:user:"
SUFFIX = ":cancel_effective_at"


async def main():
    await init_redis()
    redis = get_redis()

    pattern = f"{PREFIX}*{SUFFIX}"
    keys = await redis.keys(pattern)

    if not keys:
        logger.info("No cancelled subscriptions to check.")
        await close_redis()
        return

    now = datetime.now(timezone.utc)
    downgraded = 0
    skipped = 0

    for key in keys:
        effective_at_str = await redis.get(key)
        if not effective_at_str:
            continue

        try:
            effective_at = datetime.fromisoformat(
                effective_at_str.replace("Z", "+00:00")
            )
        except (ValueError, AttributeError):
            logger.warning("Bad date for %s: %s", key, effective_at_str)
            continue

        if effective_at > now:
            skipped += 1
            continue

        # ipgeo:user:{user_id}:cancel_effective_at → user_id
        user_id = key[len(PREFIX) : -len(SUFFIX)]

        await set_plan(user_id, "free")
        await redis.delete(key)
        logger.info("Downgraded user=%s to free (eff=%s)", user_id, effective_at_str)
        downgraded += 1

    logger.info(
        "Expiry check: %d total, %d downgraded, %d still active.",
        len(keys), downgraded, skipped,
    )
    await close_redis()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(main())
