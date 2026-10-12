from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
import respx
from pydantic import ValidationError

from workforce_agent.config import Settings
from workforce_agent.schemas import (
    DailyWeather,
    HourlyWeather,
    TimeWindow,
    WeatherForecast,
)
from workforce_agent.weather import cli as weather_cli
from workforce_agent.weather.client import FixtureWeatherClient, OpenMeteoClient
from workforce_agent.weather.exceptions import WeatherIncompleteError, WeatherUnavailableError
from workforce_agent.weather.mapper import map_open_meteo_forecast
from tests.conftest import IST, OPEN_METEO_FIXTURE, OUT_TXT, SAVED_FORECAST_FIXTURE


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
    assert first.valid_at.tzinfo is not None
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


def test_saved_out_txt_fixture_roundtrip_and_contracts() -> None:
    assert OUT_TXT.exists()
    assert SAVED_FORECAST_FIXTURE.exists()

    data = json.loads(SAVED_FORECAST_FIXTURE.read_text(encoding="utf-8"))
    forecast = WeatherForecast.model_validate(data)

    assert forecast.forecast_id == "faa32079-5eae-4af3-9801-c838496b1ccb"
    assert forecast.site_id == "VAD-PLANT-01"
    assert forecast.source == "open-meteo"
    assert len(forecast.hourly) == 72

    # Check timestamp semantics
    assert forecast.issued_at == datetime.fromisoformat("2026-10-12T00:23:04.640607Z")
    assert forecast.valid_from == datetime.fromisoformat("2026-10-11T18:30:00Z")
    assert forecast.valid_until == datetime.fromisoformat("2026-10-14T18:30:00Z")

    # valid_from precedes issued_at because Open-Meteo aligns to local midnight (Asia/Kolkata 00:00 = 18:30Z)
    assert forecast.valid_from < forecast.issued_at
    past_slots = [h for h in forecast.hourly if h.valid_at < forecast.issued_at]
    assert len(past_slots) == 6

    future_slots = forecast.future_hourly()
    assert len(future_slots) == 66
    assert future_slots[0].valid_at == datetime.fromisoformat("2026-10-12T00:30:00Z")

    # Check field units and physical semantics across all hours
    for hour in forecast.hourly:
        # valid_at is timezone-aware and matches observed_at alias
        assert hour.valid_at.tzinfo is not None
        assert hour.observed_at == hour.valid_at

        # Temperature: realistic industrial ambient Celsius range
        assert hour.temperature_c is not None and 20.0 <= hour.temperature_c <= 42.0

        # Humidity: 0 - 100 %
        assert hour.relative_humidity_pct is not None and 0.0 <= hour.relative_humidity_pct <= 100.0

        # Apparent temperature: feels-like in Celsius, distinct from WBGT
        assert hour.apparent_temperature_c is not None and 20.0 <= hour.apparent_temperature_c <= 45.0

        # Dew point in Celsius
        assert hour.dew_point_c is not None and 10.0 <= hour.dew_point_c <= 25.0

        # Wet bulb temperature: psychrometric wet bulb in Celsius, NOT WBGT
        assert hour.wet_bulb_temperature_c is not None and 18.0 <= hour.wet_bulb_temperature_c <= 26.0

        # Precipitation in mm
        assert hour.precipitation_mm is not None and hour.precipitation_mm >= 0.0

        # Wind speed in m/s
        assert hour.wind_speed_ms is not None and hour.wind_speed_ms >= 0.0

        # Shortwave radiation: hourly solar irradiance in W/m² (0 at night, up to ~835 W/m² peak daylight)
        # Not a daily sum in MJ/m²
        assert hour.shortwave_radiation_wm2 is not None
        assert 0.0 <= hour.shortwave_radiation_wm2 <= 1000.0

    # Verify radiation peaks during day and drops to 0 at night
    night_radiation = [h.shortwave_radiation_wm2 for h in forecast.hourly[:6]]
    day_radiation = [h.shortwave_radiation_wm2 for h in forecast.hourly[10:16]]
    assert all(r == 0.0 for r in night_radiation)
    assert any(r > 500.0 for r in day_radiation)


def test_mapper_models_hourly_and_daily_aggregates_separately(plant_site) -> None:
    payload = _payload()
    payload["daily"] = {
        "time": ["2026-05-12"],
        "temperature_2m_max": [42.0],
        "temperature_2m_min": [28.0],
        "precipitation_sum": [1.5],
        "shortwave_radiation_sum": [25.4],
    }
    issued_at = datetime(2026, 5, 12, 10, 5, tzinfo=IST)
    forecast = map_open_meteo_forecast(
        payload,
        site=plant_site,
        source="open-meteo",
        issued_at=issued_at,
    )

    # Hourly has hourly solar irradiance in W/m²
    assert forecast.hourly[0].shortwave_radiation_wm2 == 420.0

    # Daily has separate aggregate with daily radiation sum in MJ/m²
    assert len(forecast.daily) == 1
    daily_0 = forecast.daily[0]
    assert daily_0.valid_on == date(2026, 5, 12)
    assert daily_0.temperature_max_c == 42.0
    assert daily_0.temperature_min_c == 28.0
    assert daily_0.precipitation_sum_mm == 1.5
    assert daily_0.shortwave_radiation_sum_mj_m2 == 25.4


def test_mapper_quality_reports_past_hours_when_valid_from_precedes_issued_at(plant_site) -> None:
    issued_at = datetime(2026, 5, 12, 10, 5, tzinfo=IST)
    forecast = map_open_meteo_forecast(
        _payload(),
        site=plant_site,
        source="open-meteo",
        issued_at=issued_at,
    )
    # Slots at 08:00, 09:00, 10:00 all precede issued_at = 10:05 IST
    assert forecast.quality.past_hour_count == 3
    assert any("precede issued_at" in note for note in forecast.quality.notes)


def test_mapper_rejects_non_monotonic_hourly_timestamps(plant_site) -> None:
    payload = _payload()
    payload["hourly"]["time"][2] = payload["hourly"]["time"][1]  # duplicate timestamp
    with pytest.raises(WeatherIncompleteError, match="non-chronological or duplicate"):
        map_open_meteo_forecast(
            payload,
            site=plant_site,
            source="open-meteo",
            issued_at=datetime(2026, 5, 12, 10, 5, tzinfo=IST),
        )


def test_mapper_rejects_invalid_timestamp_format(plant_site) -> None:
    payload = _payload()
    payload["hourly"]["time"][0] = "invalid-date-string"
    with pytest.raises(WeatherIncompleteError, match="invalid provider timestamp"):
        map_open_meteo_forecast(
            payload,
            site=plant_site,
            source="open-meteo",
            issued_at=datetime(2026, 5, 12, 10, 5, tzinfo=IST),
        )


def test_weather_forecast_rejects_non_monotonic_hourly_sequence(planning_window) -> None:
    t0 = planning_window.start
    t1 = t0 + timedelta(hours=1)
    with pytest.raises(ValidationError, match="monotonically increasing"):
        WeatherForecast(
            site_id="VAD-PLANT-01",
            issued_at=t0,
            source="fixture",
            valid_from=t0,
            valid_until=t0 + timedelta(hours=5),
            hourly=[
                HourlyWeather(valid_at=t1, temperature_c=30.0),
                HourlyWeather(valid_at=t0, temperature_c=31.0),  # non-monotonic
            ],
            quality=forecast_quality_dummy(),
        )


def forecast_quality_dummy():
    from workforce_agent.schemas import WeatherDataQuality
    return WeatherDataQuality(
        is_complete=True,
        is_stale=False,
        covers_requested_window=True,
        missing_variables=[],
        incomplete_hour_count=0,
        past_hour_count=0,
        notes=[],
    )


def test_cli_execution_with_fixture(monkeypatch, capsys) -> None:
    monkeypatch.setenv("WORKFORCE_WEATHER_SOURCE", "fixture")
    monkeypatch.setenv("WORKFORCE_FIXTURE_PATH", str(OPEN_METEO_FIXTURE))

    ret = weather_cli.main(["--location-id", "vadodara-gujarat", "--site-id", "VAD-PLANT-01", "--forecast-days", "1"])
    assert ret == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["site_id"] == "VAD-PLANT-01"
    assert payload["source"] == "fixture"
    assert "hourly" in payload
    assert payload["hourly"][0]["valid_at"] is not None
