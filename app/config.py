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

    # Lemon Squeezy billing
    lemonsqueezy_api_key: str = ""
    lemonsqueezy_webhook_secret: str = ""
    lemonsqueezy_store_id: str = ""

    # Lemon Squeezy variant ID → IPGeo plan mapping
    # Create variants in LS dashboard, then paste their IDs here.
    lemonsqueezy_variant_plan_map: dict[str, str] = {
        "1794238": "free",
        "1794256": "starter",
        "1794262": "pro",
        "1794265": "business",
    }

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def lemonsqueezy_api_url(self) -> str:
        return "https://api.lemonsqueezy.com/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
