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

    # DB-IP City Lite (free, CC BY 4.0, ~100% city fill)
    # Replaces GeoLite2-City as the primary location database
    dbip_city_db_path: str = "data/dbip-city.mmdb"

    # GeoLite2 ASN (kept for ISP/ASN data since DB-IP Lite has no ASN)
    geo_asn_db_path: str = "data/GeoLite2-ASN.mmdb"

    # ip2region xdb for China ISP enhancement (Apache 2.0, free)
    ip2region_xdb_path: str = "data/ip2region_v4.xdb"

    admin_token: str = "change-me"

    # Rate-limit window in seconds
    ratelimit_window: int = 60

    # Paddle billing
    paddle_api_key: str = ""
    paddle_webhook_secret: str = ""
    paddle_sandbox: bool = True  # True = Paddle sandbox, False = live

    # RapidAPI marketplace
    rapidapi_proxy_secret: str = ""   # From RapidAPI Provider Dashboard → API settings
    rapidapi_enabled: bool = False    # Master switch for RapidAPI integration

    # Paddle price ID → IPGeo plan mapping
    # Create prices in Paddle dashboard, then paste their IDs here.
    paddle_price_plan_map: dict[str, str] = {
        "pri_01kv2fm7b7y2bwptwjeyq6gt36": "free",
        "pri_01kv2fsash4j8ed9m2swmbst7z": "starter",
        "pri_01kv2fyaj4ek50cxrbw7f332eh": "pro",
        "pri_01kv2g0mdbeze07k2rqdcqykse": "business",
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
