from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WORKFORCE_", extra="ignore")

    reasoning_provider: Literal['deterministic','vertex'] = 'deterministic'
    vertex_project: str = ''
    vertex_location: str = 'global'
    vertex_model: str = ''
    model_timeout_seconds: float = Field(default=10, gt=0, le=30)
    model_max_output_tokens: int = Field(default=2048, ge=128, le=8192)
    model_input_usd_per_million: float | None = Field(default=None, ge=0)
    model_output_usd_per_million: float | None = Field(default=None, ge=0)

    background_check_seconds: int = Field(default=30, ge=1)
    approval_db_path: Path = Path("data/approvals.sqlite3")
    agent_demo_enabled: bool = False
    agent_secure_cookies: bool = True
    agent_credentials: dict[str, dict] = Field(default_factory=dict)

    weather_source: Literal["open-meteo", "fixture"] = "open-meteo"
    open_meteo_base_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_stale_after_minutes: int = Field(default=180, gt=0)
    weather_timeout_seconds: float = Field(default=20.0, gt=0)
    fixture_path: Path | None = None
    planning_cycles_db_path: Path = Path("data/planning_cycles.sqlite3")
    default_location_id: str = "vadodara-gujarat"


def get_settings() -> Settings:
    return Settings()
