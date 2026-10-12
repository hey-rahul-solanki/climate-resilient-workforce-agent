from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
import respx

from workforce_agent.config import Settings
from workforce_agent.schemas import TimeWindow
from workforce_agent.weather.client import FixtureWeatherClient, OpenMeteoClient
from workforce_agent.weather.exceptions import WeatherIncompleteError, WeatherUnavailableError
from workforce_agent.weather.mapper import map_open_meteo_forecast
from tests.conftest import IST, OPEN_METEO_FIXTURE


def _payload() -> dict:
    return json.loads(OPEN_METEO_FIXTURE.read_text(encoding="utf-8"))


def test_mapper_normalizes_open_meteo_into_provider_neutral_schema(plant_site, planning_window) -> None:
    issued_at = datetime(2026, 5, 12, 10, 5, tzinfo=IST)
    forecast = map_open_meteo_forecast(
        _payload(),
        site=plant_site,
        source="open-meteo",
        issued_at=issued_at,
        requested_window=planning_window,
    )
    assert forecast.site_id == "VAD-PLANT-01"
    assert forecast.source == "open-meteo"
    assert forecast.quality.is_complete is True
    assert forecast.quality.is_stale is False
    assert forecast.quality.covers_requested_window is True
    first = forecast.hourly[0]
    assert first.observed_at.tzinfo is not None
    assert first.temperature_c == 34.1
    assert first.relative_humidity_pct == 48
    assert first.wind_speed_ms == 2.1
    assert forecast.valid_from == datetime(2026, 5, 12, 8, 0, tzinfo=IST).astimezone(timezone.utc)


def test_mapper_flags_incomplete_nulls_without_inventing_values(plant_site) -> None:
    payload = _payload()
    payload["hourly"]["temperature_2m"][2] = None
    forecast = map_open_meteo_forecast(
        payload,
        site=plant_site,
        source="open-meteo",
        issued_at=datetime(2026, 5, 12, 10, 5, tzinfo=IST),
    )
    assert forecast.quality.is_complete is False
    assert forecast.quality.incomplete_hour_count == 1
    assert forecast.hourly[2].temperature_c is None


def test_mapper_flags_stale_current_observation(plant_site) -> None:
    payload = _payload()
    issued_at = datetime(2026, 5, 12, 16, 0, tzinfo=IST)
    forecast = map_open_meteo_forecast(
        payload,
        site=plant_site,
        source="open-meteo",
        issued_at=issued_at,
        stale_after=timedelta(hours=3),
    )
    assert forecast.quality.is_stale is True
    assert any("staleness" in note for note in forecast.quality.notes)


def test_mapper_rejects_empty_hourly_series(plant_site) -> None:
    with pytest.raises(WeatherIncompleteError):
        map_open_meteo_forecast(
            {"hourly": {"time": []}},
            site=plant_site,
            source="open-meteo",
            issued_at=datetime(2026, 5, 12, 10, 0, tzinfo=IST),
        )


def test_mapper_flags_missing_required_variables(plant_site) -> None:
    payload = _payload()
    del payload["hourly"]["relative_humidity_2m"]
    forecast = map_open_meteo_forecast(
        payload,
        site=plant_site,
        source="open-meteo",
        issued_at=datetime(2026, 5, 12, 10, 5, tzinfo=IST),
    )
    assert "relative_humidity_2m" in forecast.quality.missing_variables
    assert forecast.quality.is_complete is False
    assert all(hour.relative_humidity_pct is None for hour in forecast.hourly)


def test_mapper_detects_window_not_covered(plant_site) -> None:
    window = TimeWindow(
        start=datetime(2026, 5, 13, 8, 0, tzinfo=IST),
        end=datetime(2026, 5, 13, 12, 0, tzinfo=IST),
    )
    forecast = map_open_meteo_forecast(
        _payload(),
        site=plant_site,
        source="open-meteo",
        issued_at=datetime(2026, 5, 12, 10, 5, tzinfo=IST),
        requested_window=window,
    )
    assert forecast.quality.covers_requested_window is False


def test_fixture_client_is_deterministic(plant_site, planning_window) -> None:
    issued_at = datetime(2026, 5, 12, 10, 5, tzinfo=IST)
    client = FixtureWeatherClient(OPEN_METEO_FIXTURE, issued_at=issued_at)
    first = client.get_forecast(plant_site, planning_window)
    second = client.get_forecast(plant_site, planning_window)
    assert first.model_dump(exclude={"forecast_id"}) == second.model_dump(exclude={"forecast_id"})
    assert first.source == "fixture"


@respx.mock
def test_open_meteo_client_maps_http_response(plant_site) -> None:
    settings = Settings(open_meteo_base_url="https://api.open-meteo.com/v1/forecast")
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(200, json=_payload())
    )
    with httpx.Client() as http_client:
        client = OpenMeteoClient(settings, http_client=http_client)
        forecast = client.get_forecast(plant_site)
    assert forecast.source == "open-meteo"
    assert forecast.hourly[0].temperature_c == 34.1


@respx.mock
def test_open_meteo_http_errors_are_unavailable(plant_site) -> None:
    settings = Settings(open_meteo_base_url="https://api.open-meteo.com/v1/forecast")
    respx.get("https://api.open-meteo.com/v1/forecast").mock(return_value=httpx.Response(503))
    with httpx.Client() as http_client:
        client = OpenMeteoClient(settings, http_client=http_client)
        with pytest.raises(WeatherUnavailableError):
            client.get_forecast(plant_site)


def test_fixture_client_missing_file(plant_site, tmp_path: Path) -> None:
    client = FixtureWeatherClient(tmp_path / "missing.json")
    with pytest.raises(WeatherUnavailableError):
        client.get_forecast(plant_site)


@pytest.mark.network
@pytest.mark.skipif(os.environ.get("RUN_NETWORK_TESTS") != "1", reason="set RUN_NETWORK_TESTS=1")
def test_live_open_meteo_vadodara(plant_site) -> None:
    forecast = OpenMeteoClient().get_forecast(plant_site, forecast_days=1)
    assert forecast.hourly
    assert forecast.site_id == plant_site.site_id
