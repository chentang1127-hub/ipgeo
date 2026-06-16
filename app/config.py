"""Application settings, loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {
        "env_prefix": "IPGEO_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow",
    }

    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    redis_url: str = "redis://localhost:6379/0"
    maxmind_license_key: str = ""

    city_db_path: str = "data/GeoLite2-City.mmdb"
    asn_db_path: str = "data/GeoLite2-ASN.mmdb"

    # Paid GeoIP2 databases (higher precision, 95%+ city fill vs ~37% GeoLite2)
    # Used for Pro / Business / Enterprise plans when available.
    geoip2_city_db_path: str = ""
    geoip2_asn_db_path: str = ""

    admin_token: str = "change-me"

    # Rate-limit window in seconds
    ratelimit_window: int = 60

    # Paddle billing
    paddle_api_key: str = ""
    paddle_webhook_secret: str = ""
    paddle_sandbox: bool = True  # True = Paddle sandbox, False = live

    # Paddle price ID → IPGeo plan mapping
    # Create prices in Paddle dashboard, then paste their IDs here.
    paddle_price_plan_map: dict[str, str] = {
        "pri_01kv753sk1wzebfa479gjtn3wa": "free",
        "pri_01kv756stsr32sg1jxkc0gd905": "starter",
        "pri_01kv7585xg3psf5bpbkpqh6hda": "pro",
        "pri_01kv759mjz9q8zt34gngj7zda0": "business",
    }

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def paddle_api_url(self) -> str:
        if self.paddle_sandbox:
            return "https://sandbox-api.paddle.com"
        return "https://api.paddle.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
