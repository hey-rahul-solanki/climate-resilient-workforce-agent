from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

import httpx

from workforce_agent.config import Settings, get_settings
from workforce_agent.schemas import Site, TimeWindow, WeatherForecast
from workforce_agent.weather.exceptions import WeatherUnavailableError
from workforce_agent.weather.mapper import HOURLY_VARIABLE_MAP, map_open_meteo_forecast

DEFAULT_HOURLY = ",".join(HOURLY_VARIABLE_MAP.keys())


class WeatherClient(Protocol):
    def get_forecast(
        self,
        site: Site,
        window: TimeWindow | None = None,
        *,
        forecast_days: int = 7,
    ) -> WeatherForecast: ...


class OpenMeteoClient:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._client = http_client
        self._owns_client = http_client is None

    def close(self) -> None:
        if self._owns_client and self._client is not None:
            self._client.close()

    def _http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.settings.weather_timeout_seconds)
        return self._client

    def get_forecast(
        self,
        site: Site,
        window: TimeWindow | None = None,
        *,
        forecast_days: int = 7,
    ) -> WeatherForecast:
        params = {
            "latitude": site.latitude,
            "longitude": site.longitude,
            "timezone": site.timezone,
            "forecast_days": forecast_days,
            "timeformat": "iso8601",
            "temperature_unit": "celsius",
            "wind_speed_unit": "ms",
            "precipitation_unit": "mm",
            "hourly": DEFAULT_HOURLY,
            "current": "temperature_2m",
        }
        try:
            response = self._http().get(self.settings.open_meteo_base_url, params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise WeatherUnavailableError(f"Open-Meteo request failed: {exc}") from exc
        except ValueError as exc:
            raise WeatherUnavailableError("Open-Meteo returned non-JSON content") from exc

        return map_open_meteo_forecast(
            payload,
            site=site,
            source="open-meteo",
            issued_at=datetime.now(timezone.utc),
            requested_window=window,
            stale_after=timedelta(minutes=self.settings.weather_stale_after_minutes),
        )


class FixtureWeatherClient:
    def __init__(
        self,
        path: Path,
        settings: Settings | None = None,
        *,
        issued_at: datetime | None = None,
    ) -> None:
        self.path = path
        self.settings = settings or get_settings()
        self.issued_at = issued_at

    def get_forecast(
        self,
        site: Site,
        window: TimeWindow | None = None,
        *,
        forecast_days: int = 7,
    ) -> WeatherForecast:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise WeatherUnavailableError(f"weather fixture is unavailable: {self.path}") from exc
        issued_at = self.issued_at or datetime.now(timezone.utc)
        forecast = map_open_meteo_forecast(
            payload,
            site=site,
            source="fixture",
            issued_at=issued_at,
            requested_window=window,
            stale_after=timedelta(minutes=self.settings.weather_stale_after_minutes),
        )
        if forecast_days:
            limit = forecast_days * 24
            hourly = forecast.hourly[:limit]
            if hourly:
                forecast = forecast.model_copy(
                    update={
                        "hourly": hourly,
                        "valid_from": hourly[0].observed_at,
                        "valid_until": hourly[-1].observed_at + timedelta(hours=1),
                    }
                )
        return forecast


def build_weather_client(settings: Settings | None = None) -> WeatherClient:
    resolved = settings or get_settings()
    if resolved.weather_source == "fixture":
        if resolved.fixture_path is None:
            raise WeatherUnavailableError("WORKFORCE_FIXTURE_PATH is required when weather_source=fixture")
        return FixtureWeatherClient(resolved.fixture_path, settings=resolved)
    return OpenMeteoClient(resolved)
