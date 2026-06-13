"""Shared fixtures for API integration tests."""

import os
from pathlib import Path

# Project root (where data/ lives)
PROJECT_ROOT = Path(__file__).parent.parent

# Ensure we don't accidentally hit real Redis
os.environ["IPGEO_ENVIRONMENT"] = "test"
os.environ["IPGEO_ADMIN_TOKEN"] = "test-admin-secret"
os.environ["IPGEO_PADDLE_WEBHOOK_SECRET"] = "test-paddle-secret"
os.environ["IPGEO_CITY_DB_PATH"] = str(PROJECT_ROOT / "data" / "GeoLite2-City.mmdb")
os.environ["IPGEO_ASN_DB_PATH"] = str(PROJECT_ROOT / "data" / "GeoLite2-ASN.mmdb")

import pytest
from httpx import AsyncClient, ASGITransport

from app.config import get_settings
get_settings.cache_clear()  # force reload with new env vars

from app.main import app
from app.redis_client import init_redis, close_redis
from app import auth


@pytest.fixture(scope="session")
async def startup():
    """One-time setup: init in-memory store, load DB, wire globals."""
    await init_redis()
    from app import main
    from app.geodb import GeoReader
    main.geo = GeoReader()
    assert main.geo.loaded, "Database not found. Run: scripts/download-db.sh"
    yield
    main.geo.close()
    main.geo = None
    await close_redis()


@pytest.fixture
async def client(startup):
    """Async HTTP client pointed at the FastAPI app (no server needed)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def api_key(startup):
    """Create a test API key and return the plaintext."""
    key = await auth.create("test-user", "free")
    yield key
    await auth.revoke(key)


@pytest.fixture
async def pro_api_key(startup):
    """Create a pro-plan API key."""
    key = await auth.create("pro-user", "pro")
    yield key
    await auth.revoke(key)
