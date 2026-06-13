"""Tests for the GeoIP reader.

Requires a test database.  Download with:
  scripts/download-db.sh
"""

import ipaddress
import pytest
from pathlib import Path

from app.geodb import GeoReader

DB_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture(scope="module")
def reader():
    """Load the GeoLite2 database (download first)."""
    city = DB_DIR / "GeoLite2-City.mmdb"
    if not city.exists():
        pytest.skip("Database not found. Run: scripts/download-db.sh")

    return GeoReader(str(city))


class TestGeoReader:
    def test_loaded(self, reader):
        assert reader.loaded

    def test_valid_ip(self, reader):
        result = reader.lookup("8.8.8.8")
        assert result["ip"] == "8.8.8.8"
        # Google's DNS is in the US
        assert result.get("country", {}).get("code") == "US"

    def test_private_ip(self, reader):
        result = reader.lookup("192.168.1.1")
        assert result["country"]["code"] == "XX"
        assert result["city"] is None

    def test_ipv6(self, reader):
        result = reader.lookup("2001:4860:4860::8888")
        assert "ip" in result
        assert result.get("country", {}).get("code") is not None

    def test_invalid_ip(self, reader):
        result = reader.lookup("not-an-ip")
        assert "error" in result

    def test_cache_works(self, reader):
        reader.lookup("1.1.1.1")
        reader.lookup("1.1.1.1")  # second call should hit cache
        assert reader.stats["cache_hits"] >= 1

    def test_returned_keys(self, reader):
        result = reader.lookup("8.8.8.8")
        expected_keys = {"ip", "country", "latitude", "longitude", "timezone"}
        missing = expected_keys - set(result.keys())
        assert not missing, f"Missing keys: {missing}"
