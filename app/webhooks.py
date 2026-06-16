"""
Paddle Billing webhook handler.

Verifies HMAC-SHA256 signatures and processes subscription lifecycle events.
https://developer.paddle.com/webhooks/overview
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from .config import get_settings
from .redis_client import get_redis
from . import billing
from . import auth

logger = logging.getLogger(__name__)


def verify_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """
    Verify Paddle webhook signature.

    Paddle signs the raw request body with HMAC-SHA256 using the webhook secret.
    The ``Paddle-Signature`` header contains ``ts={timestamp};h1={hmac_hex}``.
    """
    if not signature or not secret:
        return False

    parts = {}
    for part in signature.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            parts[k] = v

    if "ts" not in parts or "h1" not in parts:
        return False

    payload = f"{parts['ts']}:{raw_body.decode()}".encode()
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected, parts["h1"])


async def handle_event(event_type: str, data: dict) -> None:
    """
    Dispatch Paddle webhook events to the appropriate handler.
    """
    logger.info("Paddle webhook: %s (event_id=%s)", event_type, data.get("id", "?"))

    handlers = {
        "transaction.completed": _handle_transaction_completed,
        "subscription.activated": _handle_subscription_activated,
        "subscription.updated": _handle_subscription_updated,
        "subscription.canceled": _handle_subscription_canceled,
        "transaction.payment_failed": _handle_payment_failed,
    }

    handler = handlers.get(event_type)
    if handler:
        await handler(data)
    else:
        logger.debug("Unhandled Paddle event: %s", event_type)


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------


async def _handle_transaction_completed(data: dict) -> None:
    """
    Transaction completed = money received.

    This is THE most important event. Provision the service:

    - New subscription  → create API key + set plan
    - Renewal           → extend access (already handled by subscription status)
    - One-time purchase → add prepaid credits
    """
    custom = data.get("custom_data") or {}
    user_id = custom.get("user_id")

    if not user_id:
        logger.warning("transaction.completed without custom_data.user_id — skipping")
        return

    # Check items in the transaction
    items = data.get("items") or []
    for item in items:
        price_data = item.get("price") or {}
        price_id = price_data.get("id", "")

        # Try to map price → plan
        settings = get_settings()
        plan = settings.paddle_price_plan_map.get(price_id)

        if plan:
            await billing.set_plan(user_id, plan)
            # Also store the Paddle subscription/customer IDs for management
            redis = get_redis()
            subscription_id = data.get("subscription_id", "")
            customer_id = data.get("customer_id", "")
            if subscription_id:
                await redis.set(f"ipgeo:user:{user_id}:paddle_sub", subscription_id)
            if customer_id:
                await redis.set(f"ipgeo:user:{user_id}:paddle_customer", customer_id)

            logger.info(
                "Provisioned: user=%s plan=%s price=%s", user_id, plan, price_id
            )


async def _handle_subscription_activated(data: dict) -> None:
    """Subscription started — ensure plan is set."""
    custom = data.get("custom_data") or {}
    user_id = custom.get("user_id")
    if not user_id:
        return

    settings = get_settings()
    items = data.get("items") or []
    for item in items:
        price_id = (item.get("price") or {}).get("id", "")
        plan = settings.paddle_price_plan_map.get(price_id)
        if plan:
            await billing.set_plan(user_id, plan)
            redis = get_redis()
            await redis.set(
                f"ipgeo:user:{user_id}:paddle_sub", data.get("id", "")
            )
            logger.info("Subscription activated: user=%s plan=%s", user_id, plan)
            return


async def _handle_subscription_updated(data: dict) -> None:
    """Subscription changed — update plan."""
    custom = data.get("custom_data") or {}
    user_id = custom.get("user_id")
    if not user_id:
        return

    settings = get_settings()
    items = data.get("items") or []
    for item in items:
        price_id = (item.get("price") or {}).get("id", "")
        plan = settings.paddle_price_plan_map.get(price_id)
        if plan:
            await billing.set_plan(user_id, plan)
            logger.info("Subscription updated: user=%s plan=%s", user_id, plan)
            return

    # If status is paused/past_due, we might want to restrict access
    status = data.get("status", "")
    if status in ("past_due", "paused"):
        logger.warning(
            "Subscription %s: user=%s status=%s — consider restricting access",
            status, user_id, status,
        )


async def _handle_subscription_canceled(data: dict) -> None:
    """Subscription canceled — downgrade to free at period end."""
    custom = data.get("custom_data") or {}
    user_id = custom.get("user_id")
    if not user_id:
        return

    # Paddle keeps the subscription active until the end of the billing period.
    # scheduled_change tells us when it ends.
    scheduled_change = data.get("scheduled_change") or {}
    effective_at = scheduled_change.get("effective_at", "unknown")

    logger.info(
        "Subscription canceled: user=%s effective_at=%s (stays active until then)",
        user_id, effective_at,
    )

    # Don't immediately downgrade — the user paid for the period.
    # We'll handle the actual downgrade when the period ends.
    # For now, store the effective_at so a cron job or future webhook can act.
    redis = get_redis()
    await redis.set(f"ipgeo:user:{user_id}:cancel_effective_at", effective_at)


async def _handle_payment_failed(data: dict) -> None:
    """Payment failed — log for now. Could notify the user later."""
    custom = data.get("custom_data") or {}
    user_id = custom.get("user_id", "unknown")
    logger.warning(
        "Payment failed: user=%s transaction=%s",
        user_id, data.get("id", "?"),
    )


# ---------------------------------------------------------------------------
# Transaction verification helper
# ---------------------------------------------------------------------------


async def verify_transaction(transaction_id: str) -> Optional[dict]:
    """
    Query Paddle API for a transaction by ID.

    Paddle.js checkout redirects with ``checkout_id`` or ``transaction_id``
    in the URL. We use the Paddle Transactions API to verify payment status.

    Returns None if not found/error, otherwise:
        {
            "status": "completed" | "billed" | "draft" | ...,
            "user_id": "...",        // from custom_data
            "email": "...",          // customer email
            "price_id": "...",       // plan identifier
        }
    """
    import httpx

    settings = get_settings()
    url = f"{settings.paddle_api_url}/transactions/{transaction_id}"
    headers = {
        "Authorization": f"Bearer {settings.paddle_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            logger.warning("Paddle transaction lookup failed: %s %s",
                           resp.status_code, resp.text[:200])
            return None

        data = resp.json().get("data", {})

    return _parse_transaction(data)


def _parse_transaction(txn: dict) -> dict:
    """Extract user-facing fields from a Paddle transaction object."""
    custom = txn.get("custom_data") or {}
    customer = txn.get("customer") or {}
    items = txn.get("items") or []
    price_id = ""
    if items:
        price_id = (items[0].get("price") or {}).get("id", "")
    return {
        "status": txn.get("status", ""),
        "user_id": custom.get("user_id", ""),
        "email": customer.get("email", ""),
        "price_id": price_id,
    }
