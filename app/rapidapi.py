"""
RapidAPI marketplace middleware.

Detects RapidAPI-originated requests, verifies the platform signature,
and maps RapidAPI subscription tiers to IPGeo plans.

RapidAPI injects these headers on every proxied request:
    X-RapidAPI-Proxy-Secret   — HMAC secret (MUST verify to prevent bypass)
    X-RapidAPI-User           — end-user's RapidAPI account ID
    X-RapidAPI-Subscription   — plan tier (FREE/BASIC/PRO/ULTRA/MEGA)
    X-RapidAPI-Request-Id     — unique request id for dedup/tracing

Architecture:
    RapidAPI user → RapidAPI Gateway → IPGeo API
                                          │
                         ┌─────────────────┘
                         ▼
                  RapidAPIMiddleware (pure ASGI)
                    ├─ verify X-RapidAPI-Proxy-Secret
                    ├─ map subscription → IPGeo plan
                    └─ attach identity to request.state
                                          │
                         ┌─────────────────┘
                         ▼
                  auth.authenticate()
                    └─ if request.state.is_rapidapi → return RapidAPI identity

Uses a pure ASGI middleware class (not BaseHTTPMiddleware) so that
HTTPException responses are properly rendered without TaskGroup errors.
"""

import hmac
import logging
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Scope, Receive, Send

from .config import get_settings

logger = logging.getLogger(__name__)

# RapidAPI subscription tier → IPGeo plan
SUBSCRIPTION_PLAN_MAP = {
    "FREE":       "free",
    "BASIC":      "starter",
    "PRO":        "pro",
    "ULTRA":      "business",
    "MEGA":       "enterprise",
    "ENTERPRISE": "enterprise",
}

# Header that signals a RapidAPI request
RAPIDAPI_SIGNATURE_HEADER = "X-RapidAPI-Proxy-Secret"


def _verify_secret(request: Request) -> bool:
    """
    Constant-time comparison of X-RapidAPI-Proxy-Secret.
    Returns False on mismatch, True when valid or not yet configured.
    """
    settings = get_settings()
    expected = settings.rapidapi_proxy_secret
    if not expected:
        logger.warning("RapidAPI proxy secret is empty — allowing unverified request")
        return True
    actual = request.headers.get(RAPIDAPI_SIGNATURE_HEADER, "")
    return hmac.compare_digest(actual, expected)


def _extract_identity(request: Request) -> tuple[str, str]:
    """
    Extract (user_id, plan) from RapidAPI headers.
    user_id is prefixed with "rapidapi:" to avoid collisions with direct users.
    """
    rapidapi_user = request.headers.get("X-RapidAPI-User", "")
    subscription = request.headers.get("X-RapidAPI-Subscription", "FREE")
    plan = SUBSCRIPTION_PLAN_MAP.get(subscription.upper(), "free")
    user_id = f"rapidapi:{rapidapi_user}" if rapidapi_user else "rapidapi:anonymous"
    return user_id, plan


class RapidAPIMiddleware:
    """
    Pure ASGI middleware for RapidAPI integration.

    Applied to /v1/ endpoints only.  Detects the X-RapidAPI-Proxy-Secret
    header, verifies it, and attaches the resolved identity to request.state.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # Only enforce on /v1/ API endpoints
        if not path.startswith("/v1/"):
            await self.app(scope, receive, send)
            return

        # Build a Request from the ASGI scope to read headers
        request = Request(scope, receive)

        is_rapidapi = RAPIDAPI_SIGNATURE_HEADER in request.headers

        if is_rapidapi:
            if not _verify_secret(request):
                response = JSONResponse(
                    status_code=401,
                    content={
                        "error": "unauthorized",
                        "message": "Invalid RapidAPI proxy secret",
                    },
                )
                await response(scope, receive, send)
                return

            # Attach identity to request.state for downstream dependencies
            user_id, plan = _extract_identity(request)
            scope.setdefault("state", {})
            scope["state"]["is_rapidapi"] = True
            scope["state"]["rapidapi_user_id"] = user_id
            scope["state"]["rapidapi_plan"] = plan

            logger.debug("RapidAPI: user=%s plan=%s", user_id, plan)

        await self.app(scope, receive, send)
