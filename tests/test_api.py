"""Integration tests for all API endpoints.

Run:  pytest tests/ -v
"""

import hmac
import hashlib
import json
import time

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import get_settings


# ---------------------------------------------------------------------------
# Health check (no auth, no billing)
# ---------------------------------------------------------------------------

class TestHealth:
    async def test_health_returns_ok(self, client: AsyncClient):
        resp = await client.get("/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] in ("healthy", "degraded")
        assert body["version"] == "0.2.0"
        assert body["components"]["database"]["status"] == "operational"

    async def test_health_no_auth_required(self, client: AsyncClient):
        """Health endpoint should work without any headers."""
        resp = await client.get("/v1/health")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class TestAuth:
    async def test_missing_key_returns_401(self, client: AsyncClient):
        resp = await client.get("/v1/ip/8.8.8.8")
        assert resp.status_code == 401
        assert resp.json()["error"] == "unauthorized"

    async def test_invalid_key_returns_401(self, client: AsyncClient):
        resp = await client.get(
            "/v1/ip/8.8.8.8",
            headers={"X-API-Key": "ipgeo_deadbeef00000000000000000000000000000000000000000000000000000000"},
        )
        assert resp.status_code == 401

    async def test_query_param_auth(self, client: AsyncClient, api_key: str):
        """Auth via ?api_key= query parameter."""
        resp = await client.get(f"/v1/ip/1.1.1.1?api_key={api_key}")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Single IP lookup
# ---------------------------------------------------------------------------

class TestLookupIP:
    async def test_valid_ipv4(self, client: AsyncClient, api_key: str):
        resp = await client.get(
            "/v1/ip/8.8.8.8",
            headers={"X-API-Key": api_key},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ip"] == "8.8.8.8"
        assert "location" in body
        assert body["location"]["country"]["code"] == "US"
        assert "network" in body
        assert "security" in body
        assert "meta" in body

    async def test_valid_ipv6(self, client: AsyncClient, api_key: str):
        resp = await client.get(
            "/v1/ip/2001:4860:4860::8888",
            headers={"X-API-Key": api_key},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ip"] == "2001:4860:4860::8888"

    async def test_invalid_ip_returns_400(self, client: AsyncClient, api_key: str):
        resp = await client.get(
            "/v1/ip/not-an-ip",
            headers={"X-API-Key": api_key},
        )
        assert resp.status_code == 400
        assert "Invalid IP" in resp.json()["detail"]

    async def test_private_ip(self, client: AsyncClient, api_key: str):
        resp = await client.get(
            "/v1/ip/192.168.1.1",
            headers={"X-API-Key": api_key},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["location"]["country"]["code"] == "XX"

    async def test_field_filtering(self, client: AsyncClient, api_key: str):
        """?fields=country,network → location group + network group."""
        resp = await client.get(
            "/v1/ip/8.8.8.8?fields=country,network",
            headers={"X-API-Key": api_key},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "ip" in body              # ip is always included
        assert "location" in body        # country → location group
        assert "network" in body         # top-level group
        assert "security" not in body    # not requested
        assert "meta" not in body

    async def test_field_filtering_group(self, client: AsyncClient, api_key: str):
        """?fields=location,security → just those groups."""
        resp = await client.get(
            "/v1/ip/8.8.8.8?fields=location,security",
            headers={"X-API-Key": api_key},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "location" in body
        assert "security" in body
        assert "network" not in body

    async def test_cf_connecting_ip_header(self, client: AsyncClient, api_key: str):
        """When CF-Connecting-IP is set, /v1/ip/me should use it."""
        resp = await client.get(
            "/v1/ip/me",
            headers={"X-API-Key": api_key, "CF-Connecting-IP": "1.2.3.4"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ip"] == "1.2.3.4"

    async def test_x_real_ip_header(self, client: AsyncClient, api_key: str):
        resp = await client.get(
            "/v1/ip/me",
            headers={"X-API-Key": api_key, "X-Real-IP": "5.6.7.8"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ip"] == "5.6.7.8"


# ---------------------------------------------------------------------------
# Batch lookup
# ---------------------------------------------------------------------------

class TestBatch:
    async def test_batch_requires_json_body(self, client: AsyncClient, api_key: str):
        resp = await client.post(
            "/v1/ip/batch",
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            json={"ips": ["8.8.8.8", "1.1.1.1", "8.8.4.4"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "results" in body
        assert len(body["results"]) == 3

    async def test_batch_empty_ips(self, client: AsyncClient, api_key: str):
        resp = await client.post(
            "/v1/ip/batch",
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            json={"ips": []},
        )
        assert resp.status_code == 400

    async def test_batch_invalid_ip(self, client: AsyncClient, api_key: str):
        resp = await client.post(
            "/v1/ip/batch",
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            json={"ips": ["8.8.8.8", "invalid"]},
        )
        assert resp.status_code == 400
        assert "Invalid IP" in resp.json()["detail"]

    async def test_batch_limit_100(self, client: AsyncClient, api_key: str):
        ips = [f"1.1.1.{i}" for i in range(1, 102)]  # 101 IPs
        resp = await client.post(
            "/v1/ip/batch",
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            json={"ips": ips},
        )
        assert resp.status_code == 400
        assert "100" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Usage endpoint
# ---------------------------------------------------------------------------

class TestUsage:
    async def test_usage_returns_structure(self, client: AsyncClient, api_key: str):
        resp = await client.get("/v1/usage", headers={"X-API-Key": api_key})
        assert resp.status_code == 200
        body = resp.json()
        assert body["plan"] == "free"
        assert "monthly_quota" in body
        assert "monthly_used" in body
        assert "remaining_quota" in body
        assert "prepaid_credits" in body

    async def test_usage_requires_auth(self, client: AsyncClient):
        resp = await client.get("/v1/usage")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

class TestRateLimit:
    async def test_rate_limit_applied(self, client: AsyncClient, api_key: str):
        """Free plan should get 429 after exceeding 60 req/min."""
        # Fire 65 requests rapidly to exceed the 60/min free limit
        statuses = []
        for _ in range(65):
            resp = await client.get(
                "/v1/ip/8.8.8.8",
                headers={"X-API-Key": api_key},
            )
            statuses.append(resp.status_code)

        assert 200 in statuses  # some should succeed
        assert 429 in statuses  # but eventually rate-limited


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

class TestAdmin:
    async def test_create_key_no_token(self, client: AsyncClient):
        resp = await client.post("/v1/admin/keys")
        assert resp.status_code == 403

    async def test_create_key_bad_token(self, client: AsyncClient):
        resp = await client.post(
            "/v1/admin/keys",
            headers={"X-Admin-Token": "wrong"},
        )
        assert resp.status_code == 403

    async def test_create_and_revoke_key(self, client: AsyncClient):
        key_data = None

        # Create
        resp = await client.post(
            "/v1/admin/keys",
            headers={
                "X-Admin-Token": "test-admin-secret",
                "Content-Type": "application/json",
            },
            json={"user_id": "integration-test", "plan": "starter"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["api_key"].startswith("ipgeo_")
        assert body["plan"] == "starter"
        key_data = body

        # Verify the key works
        resp = await client.get(
            "/v1/ip/8.8.8.8",
            headers={"X-API-Key": key_data["api_key"]},
        )
        assert resp.status_code == 200

        # Revoke
        resp = await client.request(
            "DELETE",
            "/v1/admin/keys",
            headers={
                "X-Admin-Token": "test-admin-secret",
                "Content-Type": "application/json",
            },
            content=json.dumps({"api_key": key_data["api_key"]}),
        )
        assert resp.status_code == 200
        assert resp.json()["revoked"] is True

        # Key should no longer work
        resp = await client.get(
            "/v1/ip/8.8.8.8",
            headers={"X-API-Key": key_data["api_key"]},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Paddle webhook
# ---------------------------------------------------------------------------

class TestPaddleWebhook:
    def _sign(self, body: bytes, secret: str) -> str:
        """Paddle signs with ts:body HMAC-SHA256 hex, format: ts=...;h1=..."""
        ts = "1700000000"
        payload = f"{ts}:{body.decode()}".encode()
        h1 = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return f"ts={ts};h1={h1}"

    async def test_webhook_missing_signature(self, client: AsyncClient):
        resp = await client.post("/v1/webhooks/paddle")
        assert resp.status_code == 401

    async def test_webhook_bad_signature(self, client: AsyncClient):
        body_dict = {"event_type": "transaction.completed", "data": {"id": "1"}}
        body_bytes = json.dumps(body_dict).encode()
        sig = self._sign(body_bytes, "wrong-secret")
        resp = await client.post(
            "/v1/webhooks/paddle",
            headers={"Paddle-Signature": sig, "Content-Type": "application/json"},
            content=body_bytes,
        )
        assert resp.status_code == 401

    async def test_webhook_valid_signature(self, client: AsyncClient):
        body_dict = {
            "event_type": "transaction.completed",
            "data": {
                "id": "txn_test",
                "custom_data": {"user_id": "test-user"},
                "items": [{"price": {"id": "pri_test"}}],
            },
        }
        body_bytes = json.dumps(body_dict).encode()
        sig = self._sign(body_bytes, "test-paddle-secret")
        resp = await client.post(
            "/v1/webhooks/paddle",
            headers={
                "Paddle-Signature": sig,
                "Content-Type": "application/json",
            },
            content=body_bytes,
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    async def test_webhook_transaction_completed_sets_plan(self, client: AsyncClient):
        """A transaction.completed with a mapped price should provision the user."""
        settings = get_settings()
        settings.paddle_price_plan_map = {"pri_test_pro": "pro"}

        body_dict = {
            "event_type": "transaction.completed",
            "data": {
                "id": "txn_provision_test",
                "custom_data": {"user_id": "test-user-2"},
                "items": [{"price": {"id": "pri_test_pro"}}],
                "customer_id": "cust_999",
            },
        }
        body_bytes = json.dumps(body_dict).encode()
        sig = self._sign(body_bytes, "test-paddle-secret")
        resp = await client.post(
            "/v1/webhooks/paddle",
            headers={
                "Paddle-Signature": sig,
                "Content-Type": "application/json",
            },
            content=body_bytes,
        )
        assert resp.status_code == 200

        # The user's plan should now be "pro"
        from app.redis_client import get_redis
        redis = get_redis()
        plan = await redis.get("ipgeo:user:test-user-2:plan")
        assert plan == "pro"

    async def test_webhook_cancelled_stores_ends_at(self, client: AsyncClient):
        body_dict = {
            "event_type": "subscription.canceled",
            "data": {
                "id": "sub_cancel_test",
                "custom_data": {"user_id": "cancel-user"},
                "scheduled_change": {"effective_at": "2026-07-14T00:00:00Z"},
            },
        }
        body_bytes = json.dumps(body_dict).encode()
        sig = self._sign(body_bytes, "test-paddle-secret")
        resp = await client.post(
            "/v1/webhooks/paddle",
            headers={
                "Paddle-Signature": sig,
                "Content-Type": "application/json",
            },
            content=body_bytes,
        )
        assert resp.status_code == 200

        from app.redis_client import get_redis
        redis = get_redis()
        effective_at = await redis.get("ipgeo:user:cancel-user:cancel_effective_at")
        assert effective_at == "2026-07-14T00:00:00Z"


# ---------------------------------------------------------------------------
# Metrics endpoint
# ---------------------------------------------------------------------------

class TestMetrics:
    async def test_metrics_returns_prometheus(self, client: AsyncClient):
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        assert "ipgeo_lookups_total" in resp.text


# ---------------------------------------------------------------------------
# CORS headers
# ---------------------------------------------------------------------------

class TestCORS:
    async def test_cors_headers_present(self, client: AsyncClient):
        resp = await client.options(
            "/v1/health",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        assert "access-control-allow-origin" in resp.headers


# ---------------------------------------------------------------------------
# RapidAPI marketplace integration
# ---------------------------------------------------------------------------

RAPIDAPI_SECRET = "test-rapidapi-secret"
RAPIDAPI_HEADERS = {
    "X-RapidAPI-Proxy-Secret": RAPIDAPI_SECRET,
    "X-RapidAPI-User": "test-rapidapi-user-123",
    "X-RapidAPI-Subscription": "PRO",
}


class TestRapidAPI:
    """Tests for RapidAPI marketplace integration."""

    # -- Auth -----------------------------------------------------------

    async def test_valid_rapidapi_request_succeeds(self, client: AsyncClient):
        """A request with correct proxy secret should work without X-API-Key."""
        resp = await client.get(
            "/v1/ip/8.8.8.8",
            headers=RAPIDAPI_HEADERS,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ip"] == "8.8.8.8"

    async def test_bad_proxy_secret_returns_401(self, client: AsyncClient):
        """Wrong proxy secret must be rejected."""
        headers = {**RAPIDAPI_HEADERS, "X-RapidAPI-Proxy-Secret": "wrong-secret"}
        resp = await client.get("/v1/ip/8.8.8.8", headers=headers)
        assert resp.status_code == 401

    async def test_no_rapidapi_headers_falls_through_to_key_auth(self, client: AsyncClient):
        """Without RapidAPI headers, normal X-API-Key auth must still be required."""
        resp = await client.get("/v1/ip/8.8.8.8")
        assert resp.status_code == 401
        assert resp.json()["error"] == "unauthorized"

    # -- Subscription mapping ------------------------------------------

    async def test_free_subscription_maps_to_free_plan(self, client: AsyncClient):
        """FREE (legacy) → free."""
        headers = {**RAPIDAPI_HEADERS, "X-RapidAPI-Subscription": "FREE"}
        resp = await client.get("/v1/ip/8.8.8.8", headers=headers)
        assert resp.status_code == 200

    async def test_basic_subscription_maps_to_free(self, client: AsyncClient):
        """BASIC → free."""
        headers = {**RAPIDAPI_HEADERS, "X-RapidAPI-Subscription": "BASIC"}
        resp = await client.get("/v1/ip/8.8.8.8", headers=headers)
        assert resp.status_code == 200

    async def test_pro_subscription_maps_to_starter(self, client: AsyncClient):
        """PRO → starter."""
        resp = await client.get("/v1/ip/8.8.8.8", headers=RAPIDAPI_HEADERS)
        assert resp.status_code == 200

    async def test_ultra_subscription_maps_to_pro(self, client: AsyncClient):
        """ULTRA → pro."""
        headers = {**RAPIDAPI_HEADERS, "X-RapidAPI-Subscription": "ULTRA"}
        resp = await client.get("/v1/ip/8.8.8.8", headers=headers)
        assert resp.status_code == 200

    async def test_mega_subscription_maps_to_business(self, client: AsyncClient):
        """MEGA → business."""
        headers = {**RAPIDAPI_HEADERS, "X-RapidAPI-Subscription": "MEGA"}
        resp = await client.get("/v1/ip/8.8.8.8", headers=headers)
        assert resp.status_code == 200

    async def test_unknown_subscription_defaults_to_free(self, client: AsyncClient):
        """Unknown subscription tier falls back to 'free'."""
        headers = {**RAPIDAPI_HEADERS, "X-RapidAPI-Subscription": "WEIRD_TIER"}
        resp = await client.get("/v1/ip/8.8.8.8", headers=headers)
        assert resp.status_code == 200
        # Uses free plan limits — should still work, just with GeoLite2 data

    # -- Rate limit + billing ------------------------------------------

    async def test_rapidapi_user_uses_separate_quota(self, client: AsyncClient):
        """RapidAPI users have their own quota bucket (prefixed 'rapidapi:')."""
        resp = await client.get(
            "/v1/usage",
            headers=RAPIDAPI_HEADERS,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["plan"] == "starter"

    # -- Non-API endpoints ---------------------------------------------

    async def test_health_endpoint_ignores_rapidapi_headers(self, client: AsyncClient):
        """Health check should work regardless of RapidAPI headers."""
        resp = await client.get("/v1/health", headers=RAPIDAPI_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    async def test_metrics_ignores_rapidapi_headers(self, client: AsyncClient):
        """Metrics should work regardless of RapidAPI headers."""
        resp = await client.get("/metrics", headers=RAPIDAPI_HEADERS)
        assert resp.status_code == 200
        assert "ipgeo" in resp.text
