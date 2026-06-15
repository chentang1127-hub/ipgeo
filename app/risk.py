"""
Risk detection — Tor exit nodes, hosting/datacenter, proxies.

Tor exit node list: https://check.torproject.org/torbulkexitlist
Refreshed hourly.  Zero external API cost, zero dependencies beyond stdlib.

Hosting detection: ASN-based heuristics (known cloud/hosting provider ASNs).
"""

import logging
import threading
import time
import urllib.request
from typing import Optional, Set

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known hosting/datacenter ASNs — cloud providers and VPS hosts
# These are commonly used for proxies, VPNs, and automated traffic.
# ---------------------------------------------------------------------------
HOSTING_ASNS: Set[int] = {
    # Amazon AWS
    16509, 14618,
    # Google Cloud
    15169, 396982,
    # Microsoft Azure
    8075,
    # DigitalOcean
    14061,
    # Linode / Akamai
    63949,
    # Vultr
    20473,
    # OVH
    16276,
    # Hetzner
    24940,
    # Oracle Cloud
    31898,
    # Alibaba Cloud
    45102,
    # Tencent Cloud
    45090,
    # IBM Cloud / SoftLayer
    36351,
    # GoDaddy / MediaTemple
    26496,
    # DreamHost
    26347,
    # HostGator / EIG
    46606,
    # 1&1 IONOS
    8560,
    # Leaseweb
    16265,
    # Rackspace
    19994,
    # Equinix
    54825,
}

# ---------------------------------------------------------------------------
# Tor exit node list
# ---------------------------------------------------------------------------
_TOR_URL = "https://check.torproject.org/torbulkexitlist"
_TOR_REFRESH_SEC = 3600  # 1 hour

_tor_exits: Set[str] = set()
_tor_lock = threading.RLock()
_tor_last_fetch: float = 0.0
_tor_available: bool = False


def _fetch_tor_exits() -> Set[str]:
    """Download the current Tor exit node list.  Best-effort."""
    try:
        req = urllib.request.Request(
            _TOR_URL,
            headers={"User-Agent": "IPGeo/1.0 (https://getipgeo.com)"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8")
        exits = {
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.startswith("#")
        }
        logger.info("Tor exit list: %d IPs fetched", len(exits))
        return exits
    except Exception as exc:
        logger.warning("Failed to fetch Tor exit list: %s", exc)
        return set()


def _refresh_loop() -> None:
    """Background thread: refresh Tor list every hour."""
    global _tor_exits, _tor_last_fetch, _tor_available
    while True:
        time.sleep(_TOR_REFRESH_SEC)
        fresh = _fetch_tor_exits()
        if fresh:
            with _tor_lock:
                _tor_exits = fresh
                _tor_last_fetch = time.time()
                _tor_available = True


def init_risk() -> None:
    """Initialize risk detection on startup."""
    global _tor_exits, _tor_last_fetch, _tor_available

    exits = _fetch_tor_exits()
    if exits:
        _tor_exits = exits
        _tor_last_fetch = time.time()
        _tor_available = True

    t = threading.Thread(target=_refresh_loop, daemon=True, name="tor-refresh")
    t.start()

    logger.info(
        "Risk detection ready — Tor: %s, Hosting ASNs: %d",
        "available" if _tor_available else "unavailable",
        len(HOSTING_ASNS),
    )


def check_risk(ip_str: str, asn: Optional[int]) -> dict:
    """
    Check an IP against known risk signals.

    Returns a dict of boolean flags.  Empty dict = clean (no signals).
    """
    flags: dict = {}

    # Tor exit node
    with _tor_lock:
        if ip_str in _tor_exits:
            flags["tor_exit"] = True

    # Hosting / datacenter
    if asn is not None and asn in HOSTING_ASNS:
        flags["hosting"] = True

    return flags
