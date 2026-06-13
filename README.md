# IPGeo

Fast, affordable IP geolocation API.  Look up country, city, coordinates, ISP, ASN, and timezone for any IP address.

## Quickstart

```bash
curl -H "X-API-Key: ipgeo_YOUR_KEY" https://api.ipgeo.io/v1/ip/8.8.8.8
```

```json
{
  "ip": "8.8.8.8",
  "country": { "code": "US", "name": "United States" },
  "city": "Mountain View",
  "latitude": 37.386,
  "longitude": -122.0838,
  "timezone": "America/Los_Angeles",
  "network": { "isp": "Google LLC", "asn": 15169 }
}
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/ip/{ip}` | Look up a specific IP |
| `GET` | `/v1/ip/me` | Look up your own IP |
| `POST` | `/v1/ip/batch` | Look up up to 100 IPs |
| `GET` | `/v1/usage` | Current billing usage |
| `GET` | `/v1/health` | Health check |

## Pricing

| Plan | Monthly | Lookups/mo | Rate Limit |
|------|---------|-----------|------------|
| **Free** | $0 | 1,000 | 30/min |
| **Starter** | $19 | 10,000 | 300/min |
| **Pro** | $49 | 50,000 | 1,200/min |
| **Business** | $199 | 250,000 | 6,000/min |

See [ipgeo.io/pricing](https://ipgeo.io) for details.

## Running locally

```bash
# 1. Get a free MaxMind license key
#    https://www.maxmind.com/en/geolite2/signup

# 2. Download databases
MAXMIND_KEY=your_key ./scripts/download-db.sh

# 3. Start services
docker compose up -d

# 4. Test
curl http://localhost:8000/v1/health
```

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit .env with your settings
uvicorn app.main:app --reload
```

## Architecture

- **mmap** — GeoIP databases loaded via memory-mapped files, single lookup < 0.01ms
- **Redis** — billing, rate limiting, and API key storage with Lua atomic scripts
- **FastAPI** — async Python, auto-generated OpenAPI docs at `/docs`
- **Docker** — single-container deployment behind Cloudflare or any reverse proxy

## License

Source code: MIT.  GeoIP data: MaxMind GeoLite2 (CC BY-SA 4.0).
