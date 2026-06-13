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

    admin_token: str = "change-me"

    # Rate-limit window in seconds
    ratelimit_window: int = 60

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
