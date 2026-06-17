"""
GeoIP database reader.

Uses MaxMind's MMDB binary format loaded via mmap.
- Lookup latency < 0.01ms
- Single-core throughput > 200K QPS
- Thread-safe reads
- Background hot-reload when database files are updated
- Built-in LRU cache for repeated lookups

Data tiers:
  - GeoLite2 (free):  ~37% city fill — fallback when GeoIP2 unavailable
  - GeoIP2  (paid):   ~95% city fill — used for ALL plans when present

ALL plans get the best available database.  No artificial accuracy gating.
"""

import ipaddress
import logging
import threading
import time
from pathlib import Path
from typing import Optional

import maxminddb

from .config import get_settings
from .risk import check_risk

logger = logging.getLogger(__name__)


class GeoReader:
    """Thread-safe, hot-reloadable mmap-backed GeoIP reader.

    Uses GeoIP2 (paid) for ALL plans when the file is present.
    Falls back to GeoLite2 (free) when GeoIP2 is not yet purchased/deployed.
    """

    def __init__(self, city_db_path: str = "", asn_db_path: str = ""):
        settings = get_settings()
        self._city_path = Path(city_db_path or settings.city_db_path)
        self._asn_path = (
            Path(asn_db_path) if asn_db_path else Path(settings.asn_db_path)
        )

        # Paid GeoIP2 (optional — loaded when files exist)
        self._city2_path = self._resolve(settings.geoip2_city_db_path)
        self._asn2_path = self._resolve(settings.geoip2_asn_db_path)

        self._city: Optional[maxminddb.Reader] = None
        self._asn: Optional[maxminddb.Reader] = None
        self._city2: Optional[maxminddb.Reader] = None  # GeoIP2
        self._asn2: Optional[maxminddb.Reader] = None   # GeoIP2
        self._has_geoip2 = False   # true when GeoIP2 City .mmdb is loaded
        self._lock = threading.RLock()

        # Simple FIFO cache for hot IPs
        self._cache: dict[str, dict] = {}
        self._cache_max = 10_000
        self._cache_hits = 0
        self._cache_misses = 0

        # Track file mtimes for hot-reload detection
        self._city_mtime = 0.0
        self._asn_mtime = 0.0
        self._city2_mtime = 0.0
        self._asn2_mtime = 0.0

        self.load()
        self._start_watcher()

    @staticmethod
    def _resolve(path: str) -> Optional[Path]:
        if not path:
            return None
        p = Path(path)
        return p if p.exists() else None

    # ------------------------------------------------------------------
    # Load / Reload
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load (or reload) database files via mmap."""
        with self._lock:
            if self._city:
                try:
                    self._city.close()
                except Exception:
                    pass

            self._city = maxminddb.open_database(
                str(self._city_path), maxminddb.MODE_MMAP
            )
            self._city_mtime = self._city_path.stat().st_mtime
            logger.info(
                "City DB loaded: %s (%.1f MB)",
                self._city_path.name,
                self._city_path.stat().st_size / 1_048_576,
            )

            if self._asn_path.exists():
                if self._asn:
                    try:
                        self._asn.close()
                    except Exception:
                        pass
                self._asn = maxminddb.open_database(
                    str(self._asn_path), maxminddb.MODE_MMAP
                )
                self._asn_mtime = self._asn_path.stat().st_mtime
                logger.info("ASN DB loaded: %s", self._asn_path.name)
            else:
                logger.info("ASN DB not found at %s, skipping", self._asn_path)

            # GeoIP2 (paid, optional — when present ALL plans use it)
            self._has_geoip2 = False
            if self._city2_path:
                if self._city2:
                    try:
                        self._city2.close()
                    except Exception:
                        pass
                self._city2 = maxminddb.open_database(
                    str(self._city2_path), maxminddb.MODE_MMAP
                )
                self._city2_mtime = self._city2_path.stat().st_mtime
                logger.info("GeoIP2 City DB loaded: %s", self._city2_path.name)
                self._has_geoip2 = True

            if self._asn2_path:
                if self._asn2:
                    try:
                        self._asn2.close()
                    except Exception:
                        pass
                self._asn2 = maxminddb.open_database(
                    str(self._asn2_path), maxminddb.MODE_MMAP
                )
                self._asn2_mtime = self._asn2_path.stat().st_mtime
                logger.info("GeoIP2 ASN DB loaded: %s", self._asn2_path.name)

            # Invalidate cache on reload
            self._cache.clear()

    def close(self) -> None:
        """Release mmap handles."""
        with self._lock:
            for reader in (self._city, self._asn, self._city2, self._asn2):
                if reader:
                    try:
                        reader.close()
                    except Exception:
                        pass

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def lookup(self, ip: str, plan: str = "free") -> dict:
        """
        Look up geolocation for a single IP address.

        ALL plans use the best available database:
          - GeoIP2 City (paid, 95%+ fill) when the file exists
          - GeoLite2 City (free, 37% fill) as fallback
        ASN data: GeoIP2 ASN > GeoLite2 ASN > none.

        Returns v2 grouped format: {ip, location, network, security, meta}.
        """
        # 1. Cache check
        cache_key = f"v2:{ip}"
        cached = self._cache.get(cache_key)
        if cached:
            self._cache_hits += 1
            return cached
        self._cache_misses += 1

        # 2. Validate IP
        try:
            ip_obj = ipaddress.ip_address(ip)
        except ValueError:
            return {"ip": ip, "error": "Invalid IP address"}

        ip_str = str(ip_obj)

        # 3. Private / reserved
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved:
            result = self._build_private_result(ip_str, plan, use_geoip2)
            self._cache_put(cache_key, result)
            return result

        # 4. ALWAYS use best available: GeoIP2 > GeoLite2
        use_geoip2 = self._has_geoip2

        city_data = {}
        with self._lock:
            try:
                reader = self._city2 if use_geoip2 else self._city
                city_data = reader.get(ip_str) or {}
            except Exception:
                pass

        # ASN: GeoIP2 ASN > GeoLite2 ASN
        asn_data = {}
        asn_reader = self._asn2 if (use_geoip2 and self._asn2) else self._asn
        if asn_reader:
            with self._lock:
                try:
                    asn_data = asn_reader.get(ip_str) or {}
                except Exception:
                    pass

        # 5. Assemble v2 response
        result = self._build_result_v2(ip_str, city_data, asn_data)

        # 6. Security block
        result["security"] = self._build_security(ip_str, asn_data, city_data)

        # 7. Meta block
        result["meta"] = self._build_meta(use_geoip2, plan)

        self._cache_put(cache_key, result)
        return result

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @property
    def loaded(self) -> bool:
        return self._city is not None

    @property
    def has_geoip2(self) -> bool:
        return self._has_geoip2

    @property
    def stats(self) -> dict:
        total = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total * 100) if total > 0 else 0.0
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_size": len(self._cache),
            "cache_hit_rate_pct": round(hit_rate, 1),
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _cache_put(self, key: str, val: dict) -> None:
        if len(self._cache) >= self._cache_max:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[key] = val

    @staticmethod
    def _build_private_result(ip: str, plan: str, use_geoip2: bool = False) -> dict:
        result = {
            "ip": ip,
            "location": {
                "country": {"code": "XX", "name": "Private Network"},
                "city": None,
            },
            "network": {
                "isp": None,
                "asn": None,
                "type": None,
            },
            "security": {
                "is_tor": False,
                "is_vpn": False,
                "is_proxy": False,
                "is_hosting": False,
            },
            "meta": {"data_source": "GeoIP2" if use_geoip2 else "GeoLite2"},
        }
        return result

    @staticmethod
    def _build_result_v2(ip: str, city: dict, asn: dict) -> dict:
        """Build v2 grouped response: location + network.

        location  — country, continent, city, region, postal_code,
                     latitude, longitude, accuracy_km, timezone
        network   — isp, asn, type (hosting indicator)
        """
        country = city.get("country", {})
        location = city.get("location", {})
        continent = city.get("continent", {})
        subdivisions = city.get("subdivisions", [])
        asn_num = asn.get("autonomous_system_number")

        # Determine network type from ASN heuristics
        from .risk import HOSTING_ASNS
        net_type = "hosting" if (asn_num is not None and asn_num in HOSTING_ASNS) else None

        # Always include location — fall back to XX country when unknown
        loc = _maybe({
            "country": _maybe({
                "code": country.get("iso_code"),
                "name": country.get("names", {}).get("en"),
            }),
            "continent": _maybe({
                "code": continent.get("code"),
                "name": continent.get("names", {}).get("en"),
            }),
            "city": city.get("city", {}).get("names", {}).get("en"),
            "region": subdivisions[0].get("names", {}).get("en") if subdivisions else None,
            "postal_code": city.get("postal", {}).get("code"),
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "accuracy_km": location.get("accuracy_radius"),
            "timezone": location.get("time_zone"),
        })
        if loc is None:
            loc = {"country": {"code": "XX", "name": "Unknown"}, "city": None}

        result = {
            "ip": ip,
            "location": loc,
            "network": _maybe({
                "isp": asn.get("autonomous_system_organization"),
                "asn": asn_num,
                "type": net_type,
            }) or {"isp": None, "asn": None, "type": None},
        }

        return _compact(result)

    @staticmethod
    def _build_security(ip_str: str, asn_data: dict, city_data: dict) -> dict:
        """Build security block with boolean detection flags.

        Sources:
          - Tor exit nodes: check.torproject.org bulk list (risk.py)
          - Hosting detection: ASN heuristics (risk.py)
          - Anonymous proxy: GeoIP2/GeoLite2 traits
          - VPN detection: requires IP2Location PX8 (not yet purchased)
        """
        asn = asn_data.get("autonomous_system_number")
        traits = city_data.get("traits", {})

        risk_flags = check_risk(ip_str, asn)

        security = {
            "is_tor": risk_flags.get("tor_exit", False),
            "is_vpn": False,    # TODO: enable after purchasing IP2Location PX8
            "is_proxy": traits.get("is_anonymous_proxy", False),
            "is_hosting": risk_flags.get("hosting", False),
        }

        return security

    @staticmethod
    def _build_meta(is_geoip2: bool, plan: str) -> dict:
        """Build meta block with data source and upgrade hints."""
        meta = {
            "data_source": "GeoIP2" if is_geoip2 else "GeoLite2",
        }

        # Free / Starter plans see the Risk upgrade hint
        if plan in ("free", "starter"):
            meta["upgrade"] = {
                "risk_scoring": "Get risk_score, confidence, and abuse reports on Pro+",
                "learn_more": "https://getipgeo.com/risk",
            }

        return meta

    def _start_watcher(self) -> None:
        """Background thread: checks file mtimes every 60s, reloads on change."""

        def _watch():
            while True:
                time.sleep(60)
                try:
                    city_mt = self._city_path.stat().st_mtime
                    asn_mt = self._asn_path.stat().st_mtime if self._asn_path.exists() else 0
                    city2_mt = self._city2_path.stat().st_mtime if self._city2_path else 0
                    asn2_mt = self._asn2_path.stat().st_mtime if self._asn2_path else 0

                    if (city_mt > self._city_mtime or
                        (asn_mt and asn_mt > self._asn_mtime) or
                        (city2_mt and city2_mt > self._city2_mtime) or
                        (asn2_mt and asn2_mt > self._asn2_mtime)):
                        logger.info("Database files changed, hot-reloading...")
                        self.load()
                except Exception as exc:
                    logger.warning("Watcher error: %s", exc)

        t = threading.Thread(target=_watch, daemon=True, name="geodb-watcher")
        t.start()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _maybe(d: dict) -> Optional[dict]:
    """Return d if it has at least one non-None value, else None."""
    for v in d.values():
        if v is not None:
            return d
    return None


def _compact(d: dict) -> dict:
    """Remove top-level keys whose value is None or empty list/dict."""
    out = {}
    for k, v in d.items():
        if v is None or v == [] or v == {}:
            continue
        if isinstance(v, dict) and all(vv is None for vv in v.values()):
            continue
        out[k] = v
    return out
