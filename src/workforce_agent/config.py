from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WORKFORCE_", extra="ignore")

    weather_source: Literal["open-meteo", "fixture"] = "open-meteo"
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_stale_after_minutes: int = Field(default=180, gt=0)
    weather_timeout_seconds: float = Field(default=20.0, gt=0)
    fixture_path: Path | None = None
    default_location_id: str = "vadodara-gujarat"


def get_settings() -> Settings:
    return Settings()
