# IPGeo

Fast, affordable IP geolocation API.  Look up country, city, coordinates, ISP, ASN, and timezone for any IP address.

## Quickstart

```bash
curl -H "X-API-Key: ipgeo_YOUR_KEY" https://api.getipgeo.com/v1/ip/8.8.8.8
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

**[Get your free API key →](https://getipgeo.com/signup?plan=free)**

## Endpoints

### Geolocation

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/ip/{ip}` | Look up a specific IP |
| `GET` | `/v1/ip/me` | Look up your own IP |
| `POST` | `/v1/ip/batch` | Look up up to 100 IPs |

### Account

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/usage` | Current billing usage & quota |
| `POST` | `/v1/auth/register-free` | Sign up for a free plan API key |
| `POST` | `/v1/auth/register` | Sign up & get a Paddle checkout URL |
| `POST` | `/v1/auth/claim` | Claim your API key after checkout |
| `POST` | `/v1/auth/claim-by-email` | Recover your API key by email |

### System

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/health` | Health check (no auth) |
| `GET` | `/metrics` | Prometheus metrics |

Full OpenAPI docs: [api.getipgeo.com/docs](https://api.getipgeo.com/docs)

## Pricing

| Plan | Monthly | Lookups/mo | Rate Limit | Data |
|------|---------|-----------|------------|------|
| **Free** | $0 | 10,000 | 60/min | GeoLite2 |
| **Starter** | $9 | 100,000 | 600/min | GeoLite2 |
| **Pro** 🎯 | $29 | 500,000 | 3,000/min | **GeoIP2** |
| **Business** | $79 | 1,000,000 | 10,000/min | **GeoIP2** |

Pro & Business use MaxMind GeoIP2 (paid) for 95%+ city fill rate vs ~37% with GeoLite2.

See [getipgeo.com](https://getipgeo.com) for details and signup.

## Running locally

```bash
# 1. Get a free MaxMind license key
#    https://www.maxmind.com/en/geolite2/signup

# 2. Download databases
MAXMIND_KEY=your_key ./scripts/download-db.sh

# 3. Start services (Redis + API + Nginx)
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

Without Redis, the app falls back to an in-memory store (dev mode).  Set `IPGEO_REDIS_URL` to use Redis.

## Architecture

- **mmap** — GeoIP databases loaded via memory-mapped files, single lookup < 0.01ms
- **Redis** — billing, rate limiting, API key storage with Lua atomic scripts
- **FastAPI** — async Python, auto-generated OpenAPI docs at `/docs`
- **Docker Compose** — 3-service stack: Redis + IPGeo + Nginx behind Cloudflare
- **Paddle Billing** — merchant-of-record checkout flow, automatic plan provisioning via webhooks

## License

Source code: MIT.  GeoIP data: MaxMind GeoLite2 (CC BY-SA 4.0).
