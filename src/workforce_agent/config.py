from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WORKFORCE_", extra="ignore", env_file=".env")

    # Application Mode
    mode: Literal["static", "dynamic"] = "static"

    # Weather Configuration
    weather_source: Literal["fixture", "open-meteo", "meteor"] = "fixture"
    fixture_path: Path = Path("./data/fixtures/weather.json")
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    open_meteo_timeout: float = Field(default=10.0, gt=0)
    weather_stale_after_minutes: int = Field(default=180, gt=0)
    weather_timeout_seconds: float = Field(default=20.0, gt=0)

    # Meteor (Optional)
    meteor_api_key: Optional[str] = None
    meteor_base_url: str = "https://api.meteor.com"

    # Location Configuration
    location_source: Literal["static", "osm"] = "static"

    # OpenStreetMap (Optional)
    osm_nominatim_base: str = "https://nominatim.openstreetmap.org"
    osm_timeout: float = Field(default=10.0, gt=0)
    osm_rate_limit: float = Field(default=1.0, gt=0)

    # AI Configuration
    ai_source: Literal["rule_based", "gemini"] = "rule_based"

    # Gemini (Optional)
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-pro"
    gemini_timeout: float = Field(default=30.0, gt=0)

    # GCP Configuration (Optional)
    gcp_project_id: Optional[str] = None
    gcp_location: str = "us-central1"
    gcp_service_account_key_path: Optional[str] = None

    # Database Configuration
    database_url: str = "postgresql://user:pass@localhost/db"
    use_static_db: bool = False
    planning_cycles_db_path: Path = Path("data/planning_cycles.sqlite3")

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:5173"

    # Default Configuration
    default_location_id: str = "vadodara-gujarat"


def get_settings() -> Settings:
    return Settings()


# Global settings instance
settings = get_settings()
