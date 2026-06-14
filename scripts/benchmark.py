"""
IPGeo Benchmark — Latency, throughput, and data completeness.

Runs against the local IPGeo app (no network involved — pure engine speed).
"""
import json
import sys
import time
from pathlib import Path

# Ensure we use test settings
import os
os.environ["IPGEO_ENVIRONMENT"] = "test"
os.environ["IPGEO_ADMIN_TOKEN"] = "benchmark-token"
os.environ["IPGEO_PADDLE_WEBHOOK_SECRET"] = "benchmark-secret"

PROJECT_ROOT = Path(__file__).parent.parent
os.environ["IPGEO_CITY_DB_PATH"] = str(PROJECT_ROOT / "data" / "GeoLite2-City.mmdb")
os.environ["IPGEO_ASN_DB_PATH"] = str(PROJECT_ROOT / "data" / "GeoLite2-ASN.mmdb")

from app.config import get_settings
get_settings.cache_clear()

import asyncio
from app.geodb import GeoReader

# ---------------------------------------------------------------------------
# Test IPs — diverse set
# ---------------------------------------------------------------------------
TEST_IPS = [
    # Major DNS / cloud
    ("8.8.8.8", "Google DNS (US)"),
    ("1.1.1.1", "Cloudflare DNS (US)"),
    ("8.8.4.4", "Google DNS secondary (US)"),
    ("208.67.222.222", "OpenDNS (US)"),
    # Europe
    ("9.9.9.9", "Quad9 (EU/CH)"),
    ("77.88.8.8", "Yandex DNS (RU)"),
    ("195.82.147.49", "UK ISP (BT)"),
    ("194.158.96.55", "Swisscom (CH)"),
    # Asia
    ("114.114.114.114", "China DNS"),
    ("223.5.5.5", "AliDNS (CN)"),
    ("103.235.46.40", "India ISP"),
    ("203.104.209.71", "Japan ISP"),
    # South America
    ("177.54.148.1", "Brazil ISP"),
    ("190.210.144.1", "Argentina ISP"),
    # Oceania
    ("203.2.218.14", "Australia ISP"),
    # Africa
    ("102.66.176.4", "South Africa ISP"),
    # IPv6
    ("2001:4860:4860::8888", "Google DNS v6"),
    ("2606:4700:4700::1111", "Cloudflare DNS v6"),
    ("2a00:1450:4009:811::200e", "Google v6 (EU)"),
    # Edge cases
    ("192.168.1.1", "Private IPv4"),
    ("10.0.0.1", "Private IPv4"),
    ("127.0.0.1", "Loopback"),
    ("fc00::1", "Unique Local v6"),
    ("invalid", "Invalid input"),
    ("", "Empty string"),
]

# Fields we expect for a public IP
EXPECTED_FIELDS = [
    "ip", "country", "city", "subdivisions", "postal_code",
    "latitude", "longitude", "accuracy_radius_km", "timezone",
    "continent", "network",
]


def benchmark_latency(geo: GeoReader, rounds: int = 10_000):
    """Measure single-lookup latency statistics."""
    print(f"\n{'='*60}")
    print(f"LATENCY BENCHMARK ({rounds:,} lookups)")
    print(f"{'='*60}")

    # Warmup
    for _ in range(100):
        geo.lookup("8.8.8.8")

    times = []
    ip = "8.8.8.8"
    start = time.perf_counter()
    for _ in range(rounds):
        t0 = time.perf_counter()
        geo.lookup(ip)
        times.append(time.perf_counter() - t0)
    elapsed = time.perf_counter() - start

    times.sort()
    p50 = times[len(times) // 2]
    p95 = times[int(len(times) * 0.95)]
    p99 = times[int(len(times) * 0.99)]
    avg = sum(times) / len(times)
    qps = rounds / elapsed

    print(f"  P50:  {p50*1_000_000:8.1f} us")
    print(f"  P95:  {p95*1_000_000:8.1f} us")
    print(f"  P99:  {p99*1_000_000:8.1f} us")
    print(f"  Avg:  {avg*1_000_000:8.1f} us")
    print(f"  Min:  {times[0]*1_000_000:8.1f} us")
    print(f"  Max:  {times[-1]*1_000_000:8.1f} us")
    print(f"  QPS:  {qps:,.0f} (single-thread)")
    return {"p50_us": p50 * 1_000_000, "p95_us": p95 * 1_000_000, "p99_us": p99 * 1_000_000, "qps": qps}


def benchmark_throughput(geo: GeoReader):
    """Measure multi-IP throughput."""
    print(f"\n{'='*60}")
    print("THROUGHPUT BENCHMARK (5000 IPs × 10 rounds)")
    print(f"{'='*60}")

    ips = ["8.8.8.8", "1.1.1.1", "8.8.4.4", "9.9.9.9", "208.67.222.222"] * 1000

    # Warmup
    for ip in ips[:100]:
        geo.lookup(ip)

    times = []
    start = time.perf_counter()
    for ip in ips:
        t0 = time.perf_counter()
        geo.lookup(ip)
        times.append(time.perf_counter() - t0)
    elapsed = time.perf_counter() - start

    times.sort()
    p50 = times[len(times) // 2]
    qps = len(ips) / elapsed

    print(f"  Total IPs: {len(ips):,}")
    print(f"  Total time: {elapsed:.3f}s")
    print(f"  QPS: {qps:,.0f}")
    print(f"  P50: {p50*1_000_000:.1f} us")
    return {"qps": qps, "p50_us": p50 * 1_000_000}


def check_data_completeness(geo: GeoReader):
    """Check what fields are returned for each test IP."""
    print(f"\n{'='*60}")
    print("DATA COMPLETENESS CHECK")
    print(f"{'='*60}")

    rows = []
    stats = {"total": 0, "has_city": 0, "has_isp": 0, "has_postal": 0,
             "has_coords": 0, "has_timezone": 0, "has_asn": 0, "private": 0,
             "invalid": 0, "details": []}

    for ip, desc in TEST_IPS:
        result = geo.lookup(ip)
        stats["total"] += 1

        if result.get("error"):
            stats["invalid"] += 1
            stats["details"].append({"ip": ip, "desc": desc, "error": result["error"]})
            continue

        if result.get("country", {}).get("code") == "XX":
            stats["private"] += 1
            status = "(private)"
        else:
            status = ""

        country = result.get("country", {}).get("code", "?")
        city = result.get("city") or "-"
        isp = (result.get("network") or {}).get("isp") or "-"
        field_count = len(result)

        if city and city != "-":
            stats["has_city"] += 1
        if isp and isp != "-":
            stats["has_isp"] += 1
        if result.get("postal_code"):
            stats["has_postal"] += 1
        if result.get("latitude") is not None:
            stats["has_coords"] += 1
        if result.get("timezone"):
            stats["has_timezone"] += 1
        if (result.get("network") or {}).get("asn"):
            stats["has_asn"] += 1

        stats["details"].append({
            "ip": ip, "desc": desc, "country": country, "city": city,
            "isp": isp, "fields": field_count, "status": status,
            "has_coords": result.get("latitude") is not None,
            "has_timezone": bool(result.get("timezone")),
        })

    print(f"\n  Summary ({stats['total']} IPs):")
    valid = max(stats['total'] - stats['private'] - stats['invalid'], 1)
    print(f"  City:       {stats['has_city']}/{valid} ({stats['has_city']/valid*100:.0f}%)")
    print(f"  ISP/Org:    {stats['has_isp']}/{valid} ({stats['has_isp']/valid*100:.0f}%)")
    print(f"  Postal:     {stats['has_postal']}/{valid} ({stats['has_postal']/valid*100:.0f}%)")
    print(f"  Coords:     {stats['has_coords']}/{valid} ({stats['has_coords']/valid*100:.0f}%)")
    print(f"  Timezone:   {stats['has_timezone']}/{valid} ({stats['has_timezone']/valid*100:.0f}%)")
    print(f"  ASN:        {stats['has_asn']}/{valid} ({stats['has_asn']/valid*100:.0f}%)")
    print(f"  Private:    {stats['private']}")
    print(f"  Invalid:    {stats['invalid']}")

    return stats


def sample_response(geo: GeoReader):
    """Print a full sample JSON response."""
    print(f"\n{'='*60}")
    print("SAMPLE RESPONSE (8.8.8.8)")
    print(f"{'='*60}")
    result = geo.lookup("8.8.8.8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n  Total fields: {len(result)}")
    return result


def main():
    print("IPGeo Benchmark Suite")
    print(f"{'='*60}")

    geo = GeoReader()
    if not geo.loaded:
        print("FATAL: Database not loaded. Run scripts/download-db.sh first.")
        sys.exit(1)

    print(f"City DB:  {geo._city_path} ({geo._city_path.stat().st_size/1_048_576:.1f} MB)")
    if geo._asn:
        print(f"ASN DB:   {geo._asn_path} ({geo._asn_path.stat().st_size/1_048_576:.1f} MB)")
    print(f"Cache:    {geo._cache_max:,} entries")

    # Run benchmarks
    sample = sample_response(geo)
    lat = benchmark_latency(geo, rounds=10_000)
    tput = benchmark_throughput(geo)
    data = check_data_completeness(geo)

    valid_ips = max(data["total"] - data["private"] - data["invalid"], 1)

    # Save detailed results to JSON
    results = {
        "app": "IPGeo",
        "data_source": "MaxMind GeoLite2 (free)",
        "city_db_size_mb": geo._city_path.stat().st_size / 1_048_576,
        "asn_db_size_mb": geo._asn_path.stat().st_size / 1_048_576 if geo._asn else 0,
        "sample_response_8_8_8_8": sample,
        "latency": {
            "p50_us": lat["p50_us"],
            "p95_us": lat["p95_us"],
            "p99_us": lat["p99_us"],
            "qps_single_thread": lat["qps"],
        },
        "throughput": {"mixed_5_ip_qps": tput["qps"], "mixed_p50_us": tput["p50_us"]},
        "data_completeness": {
            "total_ips_tested": data["total"],
            "city_fill_pct": round(data["has_city"] / valid_ips * 100, 1),
            "isp_fill_pct": round(data["has_isp"] / valid_ips * 100, 1),
            "postal_fill_pct": round(data["has_postal"] / valid_ips * 100, 1),
            "coords_fill_pct": round(data["has_coords"] / valid_ips * 100, 1),
            "timezone_fill_pct": round(data["has_timezone"] / valid_ips * 100, 1),
            "asn_fill_pct": round(data["has_asn"] / valid_ips * 100, 1),
        },
        "per_ip_details": data["details"],
    }
    out_path = PROJECT_ROOT / "benchmark_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Detailed results saved to: {out_path}")

    # Scorecard
    print(f"\n{'='*60}")
    print("SCORECARD")
    print(f"{'='*60}")
    print(f"  Single-lookup P50:   {lat['p50_us']:.0f} us  {'OK' if lat['p50_us'] < 500 else 'WARN'}")
    print(f"  Single-lookup P99:   {lat['p99_us']:.0f} us  {'OK' if lat['p99_us'] < 2000 else 'WARN'}")
    print(f"  Single-thread QPS:   {lat['qps']:,.0f}     {'OK' if lat['qps'] > 50_000 else 'WARN'}")
    print(f"  Mixed-IP QPS:        {tput['qps']:,.0f}")
    print(f"  City fill rate:      {data['has_city']/valid_ips*100:.0f}%")
    print(f"  ISP fill rate:       {data['has_isp']/valid_ips*100:.0f}%")
    print(f"  Coordinate rate:     {data['has_coords']/valid_ips*100:.0f}%")

    geo.close()


if __name__ == "__main__":
    main()
