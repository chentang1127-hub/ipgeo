"""
Competitor API Benchmark — Test IPGeo against real competitor APIs.

Tests latency, data completeness, and field coverage for each provider.
"""
import io
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project to path for IPGeo
sys.path.insert(0, str(Path(__file__).parent.parent))

# IPGeo setup
import os
os.environ["IPGEO_ENVIRONMENT"] = "test"
os.environ["IPGEO_CITY_DB_PATH"] = str(Path(__file__).parent.parent / "data" / "GeoLite2-City.mmdb")
os.environ["IPGEO_ASN_DB_PATH"] = str(Path(__file__).parent.parent / "data" / "GeoLite2-ASN.mmdb")

from app.config import get_settings
get_settings.cache_clear()
from app.geodb import GeoReader

# ---------------------------------------------------------------------------
# Test IPs
# ---------------------------------------------------------------------------
TEST_IPS = [
    ("8.8.8.8", "Google DNS (US)"),
    ("1.1.1.1", "Cloudflare DNS (US)"),
    ("8.8.4.4", "Google DNS secondary (US)"),
    ("9.9.9.9", "Quad9 (EU/CH)"),
    ("77.88.8.8", "Yandex DNS (RU)"),
    ("114.114.114.114", "China DNS"),
    ("223.5.5.5", "AliDNS (CN)"),
    ("103.235.46.40", "India ISP"),
    ("203.104.209.71", "Japan ISP"),
    ("177.54.148.1", "Brazil ISP"),
]

# ---------------------------------------------------------------------------
# Competitor API configurations
# ---------------------------------------------------------------------------
COMPETITORS = {
    "ip-api.com (free)": {
        "url_template": "http://ip-api.com/json/{ip}?fields=66842623",
        "needs_key": False,
        "key_header": None,
    },
    # ipinfo free tier — need to sign up at ipinfo.io for a token
    # "ipinfo.io": {
    #     "url_template": "https://ipinfo.io/{ip}?token={key}",
    #     "needs_key": True,
    #     "key_header": None,
    # },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def call_api(url: str, timeout: float = 5.0) -> tuple[dict | None, float, str | None]:
    """Call an API and return (parsed_json, latency_seconds, error)."""
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "IPGeo-Benchmark/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            latency = time.perf_counter() - t0
            return json.loads(body), latency, None
    except urllib.error.HTTPError as e:
        latency = time.perf_counter() - t0
        return None, latency, f"HTTP {e.code}"
    except Exception as e:
        latency = time.perf_counter() - t0
        return None, latency, str(e)[:80]


def benchmark_competitor(name: str, config: dict) -> dict:
    """Benchmark one competitor API."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")

    latencies = []
    results = []
    errors = 0

    for ip, desc in TEST_IPS:
        url = config["url_template"].format(ip=ip, key=config.get("key", ""))
        data, lat, err = call_api(url)

        if err:
            errors += 1
            results.append({"ip": ip, "desc": desc, "error": err, "latency_ms": round(lat * 1000, 1)})
            print(f"  {ip:<20} ERROR: {err}")
        else:
            latencies.append(lat)
            # Normalize fields
            fields = {
                "ip": ip,
                "desc": desc,
                "latency_ms": round(lat * 1000, 1),
                "country": data.get("countryCode") or data.get("country_code") or data.get("country"),
                "city": data.get("city"),
                "isp": data.get("isp") or data.get("org") or (data.get("as") or "").split(" ", 1)[-1] if data.get("as") else None,
                "asn": data.get("asn") or (data.get("as") or "").split(" ")[0].replace("AS", "") if data.get("as") else None,
                "latitude": data.get("lat") or data.get("latitude"),
                "longitude": data.get("lon") or data.get("longitude"),
                "timezone": data.get("timezone"),
                "postal": data.get("zip") or data.get("postal_code") or data.get("postal"),
                "region": data.get("regionName") or data.get("region") or data.get("subdivisions"),
                "org": data.get("org"),
            }
            results.append(fields)
            status = f"{fields['country'] or '?'}/{fields.get('city') or '-'}/{fields.get('isp') or '-'}"
            print(f"  {ip:<20} {fields['latency_ms']:6.1f}ms  {status[:60]}")

    if latencies:
        latencies.sort()
        p50 = latencies[len(latencies) // 2] * 1000
        p95 = latencies[int(len(latencies) * 0.95)] * 1000
        avg = sum(latencies) / len(latencies) * 1000
        print(f"\n  Latency: P50={p50:.1f}ms  P95={p95:.1f}ms  Avg={avg:.1f}ms")
        print(f"  Errors: {errors}/{len(TEST_IPS)}")
    else:
        p50 = p95 = avg = None
        print(f"\n  ALL FAILED — {errors}/{len(TEST_IPS)} errors")

    return {
        "name": name,
        "results": results,
        "latency_p50_ms": p50,
        "latency_p95_ms": p95,
        "latency_avg_ms": avg,
        "total_tested": len(TEST_IPS),
        "errors": errors,
    }


def benchmark_ipgeo_locally() -> dict:
    """Benchmark IPGeo locally (no network)."""
    print(f"\n{'='*60}")
    print("Testing: IPGeo (local mmap)")
    print(f"{'='*60}")

    geo = GeoReader()
    latencies = []
    results = []

    for ip, desc in TEST_IPS:
        t0 = time.perf_counter()
        data = geo.lookup(ip)
        lat = time.perf_counter() - t0
        latencies.append(lat)

        fields = {
            "ip": ip,
            "desc": desc,
            "latency_ms": round(lat * 1000, 1),
            "country": (data.get("country") or {}).get("code"),
            "city": data.get("city"),
            "isp": (data.get("network") or {}).get("isp"),
            "asn": (data.get("network") or {}).get("asn"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone"),
            "postal": data.get("postal_code"),
        }
        results.append(fields)
        status = f"{fields['country'] or '?'}/{fields.get('city') or '-'}/{fields.get('isp') or '-'}"
        print(f"  {ip:<20} {fields['latency_ms']:6.1f}ms  {status[:60]}")

    latencies.sort()
    p50 = latencies[len(latencies) // 2] * 1000
    p95 = latencies[int(len(latencies) * 0.95)] * 1000
    avg = sum(latencies) / len(latencies) * 1000
    print(f"\n  Latency: P50={p50:.3f}ms  P95={p95:.3f}ms  Avg={avg:.3f}ms")
    print(f"  (local mmap — no network overhead)")

    geo.close()
    return {
        "name": "IPGeo (local)",
        "results": results,
        "latency_p50_ms": p50,
        "latency_p95_ms": p95,
        "latency_avg_ms": avg,
        "total_tested": len(TEST_IPS),
        "errors": 0,
    }


# ---------------------------------------------------------------------------
# Cross-comparison
# ---------------------------------------------------------------------------
def compare_data_quality(all_results: list[dict]):
    """Compare data quality across providers."""
    print(f"\n{'='*60}")
    print("CROSS-COMPARISON: DATA QUALITY (country agreement)")
    print(f"{'='*60}")

    for i, (ip, desc) in enumerate(TEST_IPS):
        countries = []
        for r in all_results:
            entry = r["results"][i]
            if "error" not in entry:
                c = entry.get("country", "?") or "?"
                cs = str(c)[:4]
                countries.append(f"{r['name']}={cs}")
        print(f"  {ip:<20} {' | '.join(countries)}")


def main():
    print("IPGeo vs Competitors — Real API Benchmark")
    print(f"Testing {len(TEST_IPS)} IPs against each provider\n")

    all_results = []

    # Test IPGeo locally
    ipgeo_result = benchmark_ipgeo_locally()
    all_results.append(ipgeo_result)

    # Test competitors
    for name, config in COMPETITORS.items():
        result = benchmark_competitor(name, config)
        all_results.append(result)

    # Cross-comparison
    compare_data_quality(all_results)

    # Final scorecard
    print(f"\n{'='*60}")
    print("FINAL COMPARISON")
    print(f"{'='*60}")
    print(f"{'Provider':<30} {'P50':>8} {'P95':>8} {'Avg':>8} {'Errors':>7}")
    print("-" * 70)
    for r in all_results:
        p50 = f"{r['latency_p50_ms']:.1f}ms" if r['latency_p50_ms'] is not None else "FAIL"
        p95 = f"{r['latency_p95_ms']:.1f}ms" if r['latency_p95_ms'] is not None else "FAIL"
        avg = f"{r['latency_avg_ms']:.1f}ms" if r['latency_avg_ms'] is not None else "FAIL"
        print(f"{r['name']:<30} {p50:>8} {p95:>8} {avg:>8} {r['errors']:>6}/{r['total_tested']}")

    # Save results
    out = Path(__file__).parent.parent / "competitor_benchmark.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nFull results saved to: {out}")


if __name__ == "__main__":
    main()
