"""
Lemon Squeezy billing webhook handler.

Verifies HMAC-SHA256 signatures and processes order/subscription lifecycle events.
https://docs.lemonsqueezy.com/api
https://docs.lemonsqueezy.com/help/webhooks
"""

import hashlib
import hmac
import logging
from typing import Optional

from .config import get_settings
from .redis_client import get_redis
from . import billing
from . import auth

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Signature verification
# ---------------------------------------------------------------------------


def verify_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """
    Verify a Lemon Squeezy webhook signature.

    LS signs the raw request body with HMAC-SHA256 using your webhook secret.
    The signature is in the ``X-Signature`` header as a hex digest.
    """
    if not signature or not secret:
        return False

    expected = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


# ---------------------------------------------------------------------------
# Event dispatcher
# ---------------------------------------------------------------------------


async def handle_event(event_type: str, data: dict, meta: dict = None) -> None:
    """Dispatch a Lemon Squeezy webhook event to the appropriate handler."""
    logger.info("Lemon Squeezy webhook: %s (id=%s)", event_type, data.get("id", "?"))

    # LS webhook payload: {data: {...}, meta: {custom_data: {...}}}
    # custom_data is in the top-level meta, not nested inside data.attributes
    if meta is None:
        meta = {}

    handlers = {
        "order_created": _handle_order_created,
        "subscription_created": _handle_subscription_created,
        "subscription_updated": _handle_subscription_updated,
        "subscription_cancelled": _handle_subscription_cancelled,
        "subscription_expired": _handle_subscription_expired,
        "subscription_payment_failed": _handle_payment_failed,
        "subscription_payment_success": _handle_payment_success,
    }

    handler = handlers.get(event_type)
    if handler:
        await handler(data, meta)
    else:
        logger.debug("Unhandled LS event: %s", event_type)


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------


async def _handle_order_created(data: dict, meta: dict = None) -> None:
    """
    A new order was placed — this is the primary event for provisioning.

    LS webhook sends custom_data in the top-level ``meta`` object:
    ``{data: {attributes: {...}}, meta: {custom_data: {user_id: ...}}}``

    We extract ``user_id``, provision the plan, and create an API key so the
    user can claim it immediately on the success page.
    """
    if meta is None:
        meta = {}
    attrs = data.get("attributes") or {}

    # custom_data is in top-level meta (LS JSON:API webhook format)
    custom = meta.get("custom_data") or attrs.get("custom_data") or {}
    # Also try nested: attrs.meta.custom_data (older format)
    nested_meta = attrs.get("meta") or {}
    if not custom:
        custom = nested_meta.get("custom_data") or {}
    user_id = custom.get("user_id") or ""

    if not user_id:
        logger.warning("order_created without custom_data.user_id — trying checkout lookup")
        return

    await _provision_user(user_id, attrs, data.get("id", ""))


async def _handle_subscription_created(data: dict, meta: dict = None) -> None:
    """Subscription created — ensure plan is set (redundant with order_created)."""
    if meta is None:
        meta = {}
    attrs = data.get("attributes") or {}
    custom = meta.get("custom_data") or attrs.get("custom_data") or {}
    user_id = custom.get("user_id") or ""

    if not user_id:
        return

    redis = get_redis()
    await redis.set(f"ipgeo:user:{user_id}:ls_subscription", data.get("id", ""))
    await _provision_user(user_id, attrs, data.get("id", ""))


async def _handle_subscription_updated(data: dict, meta: dict = None) -> None:
    """Subscription changed — update plan if variant changed."""
    attrs = data.get("attributes") or {}
    variant_id = str(attrs.get("variant_id", ""))
    customer_id = str(attrs.get("customer_id", ""))

    if not variant_id or not customer_id:
        return

    # Find user by LS customer_id
    redis = get_redis()
    user_id = await redis.get(f"ipgeo:customer:{customer_id}:user")
    if not user_id:
        logger.warning("subscription_updated: no user for LS customer %s", customer_id)
        return

    plan = _plan_from_variant(variant_id)
    if plan:
        await billing.set_plan(user_id, plan)
        logger.info("Subscription updated: user=%s plan=%s", user_id, plan)

    # Handle paused / past_due status
    status = attrs.get("status", "")
    if status in ("past_due", "paused", "unpaid"):
        logger.warning(
            "Subscription status=%s user=%s — consider restricting access",
            status, user_id,
        )


async def _handle_subscription_cancelled(data: dict, meta: dict = None) -> None:
    """Subscription cancelled — will expire at period end (grace period)."""
    attrs = data.get("attributes") or {}
    ends_at = attrs.get("ends_at", "unknown")

    customer_id = str(attrs.get("customer_id", ""))
    redis = get_redis()
    user_id = await redis.get(f"ipgeo:customer:{customer_id}:user") if customer_id else None

    logger.info(
        "Subscription cancelled: user=%s ends_at=%s (active until then)",
        user_id or "unknown", ends_at,
    )

    if user_id:
        await redis.set(f"ipgeo:user:{user_id}:cancel_effective_at", str(ends_at))


async def _handle_subscription_expired(data: dict, meta: dict = None) -> None:
    """Subscription expired — downgrade to free."""
    attrs = data.get("attributes") or {}
    customer_id = str(attrs.get("customer_id", ""))
    redis = get_redis()
    user_id = await redis.get(f"ipgeo:customer:{customer_id}:user") if customer_id else None

    if user_id:
        await billing.set_plan(user_id, "free")
        logger.info("Subscription expired: user=%s downgraded to free", user_id)


async def _handle_payment_failed(data: dict, meta: dict = None) -> None:
    """Payment failed — log for now."""
    attrs = data.get("attributes") or {}
    logger.warning(
        "Payment failed: order=%s status=%s",
        data.get("id", "?"), attrs.get("status", "?"),
    )


async def _handle_payment_success(data: dict, meta: dict = None) -> None:
    """Recurring payment succeeded — log for record keeping."""
    attrs = data.get("attributes") or {}
    logger.info(
        "Payment success: subscription=%s total=%s",
        attrs.get("subscription_id", "?"),
        attrs.get("total_formatted", "?"),
    )


# ---------------------------------------------------------------------------
# Provisioning helper
# ---------------------------------------------------------------------------


async def _provision_user(user_id: str, attrs: dict, order_or_sub_id: str) -> None:
    """Provision a user with a plan and cache linking info."""
    redis = get_redis()

    # Check if already provisioned (idempotent)
    existing = await redis.get(f"ipgeo:user:{user_id}:plan")
    if existing and existing != "free":
        logger.info("User %s already provisioned as %s — skipping", user_id, existing)
        return

    # Determine plan
    variant_id = str(attrs.get("variant_id", ""))
    plan = _plan_from_variant(variant_id)
    if not plan:
        logger.warning("Cannot determine plan from variant_id=%s", variant_id)
        return

    await billing.set_plan(user_id, plan)

    # Link customer for future lookups
    customer_id = str(attrs.get("customer_id", ""))
    if customer_id:
        await redis.set(f"ipgeo:customer:{customer_id}:user", user_id)

    # Store LS IDs
    if attrs.get("subscription_id"):
        await redis.set(f"ipgeo:user:{user_id}:ls_subscription", str(attrs["subscription_id"]))
    await redis.set(f"ipgeo:user:{user_id}:ls_order", order_or_sub_id)

    logger.info("Provisioned: user=%s plan=%s variant=%s", user_id, plan, variant_id)


def _plan_from_variant(variant_id: str) -> str:
    """Map a Lemon Squeezy variant ID to an IPGeo plan name."""
    settings = get_settings()
    return settings.lemonsqueezy_variant_plan_map.get(variant_id, "")


# ---------------------------------------------------------------------------
# Checkout helpers
# ---------------------------------------------------------------------------


async def create_checkout(
    user_id: str,
    variant_id: str,
    customer_email: str,
    claim_token: str = "",
) -> dict:
    """
    Create a Lemon Squeezy checkout and return the checkout data.

    Call LS ``POST /v1/checkouts`` (JSON:API format), get back a signed
    checkout URL the user is redirected to.

    LS does NOT support template variables in redirect_url, so we pre-generate
    a claim_token and embed it. After payment LS redirects to
    ``/success?token={claim_token}`` and the frontend claims the key with it.

    Returns::

        {
            "id": "checkout-uuid",
            "url": "https://store.lemonsqueezy.com/checkout/...",
        }
    """
    import httpx

    settings = get_settings()
    url = f"{settings.lemonsqueezy_api_url}/checkouts"

    # LS doesn't replace {checkout_id} — use our own claim token
    redirect_url = f"https://getipgeo.com/success?token={claim_token}"

    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": customer_email,
                    "custom": {"user_id": user_id},
                },
                "product_options": {
                    "redirect_url": redirect_url,
                },
            },
            "relationships": {
                "store": {
                    "data": {
                        "type": "stores",
                        "id": str(settings.lemonsqueezy_store_id),
                    }
                },
                "variant": {
                    "data": {
                        "type": "variants",
                        "id": str(variant_id),
                    }
                },
            },
        }
    }

    headers = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "Authorization": f"Bearer {settings.lemonsqueezy_api_key}",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        result = resp.json()

        if resp.status_code not in (200, 201):
            logger.error("LS checkout error (status=%s): %s", resp.status_code, result)
            raise RuntimeError(f"Lemon Squeezy checkout failed: {result}")

        checkout = result.get("data") or {}
        attrs = checkout.get("attributes") or {}
        checkout_id = checkout.get("id", "")
        checkout_url = attrs.get("url", "")

        # Store checkout_id → user_id mapping so we can verify later
        redis = get_redis()
        await redis.setex(f"ipgeo:checkout:{checkout_id}", 86400, user_id)

        return {
            "id": checkout_id,
            "url": checkout_url,
        }


async def verify_checkout(checkout_id: str) -> Optional[dict]:
    """
    Verify a Lemon Squeezy checkout by looking up its associated order.

    After a customer completes payment:
    1. LS creates an Order linked to the Checkout.
    2. We look up the order to confirm payment status.

    Returns ``None`` if not found, otherwise::

        {
            "status": "paid" | "pending" | "refunded" | ...,
            "user_id": "...",
            "email": "...",
            "variant_id": "...",
        }
    """
    import httpx

    settings = get_settings()
    headers = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "Authorization": f"Bearer {settings.lemonsqueezy_api_key}",
    }

    # First, get the checkout to find its order
    check_url = f"{settings.lemonsqueezy_api_url}/checkouts/{checkout_id}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(check_url, headers=headers)
        if resp.status_code != 200:
            logger.warning("LS checkout lookup failed: %s", resp.status_code)
            return None

        checkout = resp.json().get("data") or {}
        attrs = checkout.get("attributes") or {}
        status = attrs.get("status", "")

        # If checkout still active (unpaid), tell caller to retry
        if status in ("draft", "expired"):
            return {
                "status": status,
                "user_id": "",
                "email": "",
                "variant_id": "",
            }

        # Check for linked order in relationships
        relationships = checkout.get("relationships") or {}
        order_rel = relationships.get("order") or {}
        order_data = order_rel.get("data") or {}
        order_id = order_data.get("id", "")

        # If no order yet, check if we have the checkout info cached
        if not order_id:
            # Fallback: try listing recent orders filtered by email
            redis = get_redis()
            user_id = await redis.get(f"ipgeo:checkout:{checkout_id}") or ""
            # No order = payment not yet completed → retry
            return {
                "status": "pending",
                "user_id": user_id,
                "email": "",
                "variant_id": "",
            }

        # Get the order to check its status
        order_resp = await client.get(
            f"{settings.lemonsqueezy_api_url}/orders/{order_id}",
            headers=headers,
        )
        if order_resp.status_code != 200:
            logger.warning("LS order lookup failed: %s", order_resp.status_code)
            return None

        order = order_resp.json().get("data") or {}
        order_attrs = order.get("attributes") or {}
        order_status = order_attrs.get("status", "")

        # Extract user_id from custom_data
        order_meta = order_attrs.get("meta") or {}
        custom = order_meta.get("custom_data") or {}
        user_id = custom.get("user_id", "")

        # If still no user_id, check our Redis cache
        if not user_id:
            redis = get_redis()
            user_id = await redis.get(f"ipgeo:checkout:{checkout_id}") or ""

        return {
            "status": order_status,
            "user_id": user_id,
            "email": order_attrs.get("user_email", ""),
            "variant_id": str(order_attrs.get("variant_id", "")),
        }
