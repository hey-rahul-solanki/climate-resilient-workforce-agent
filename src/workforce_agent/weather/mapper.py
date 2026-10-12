from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

from workforce_agent.schemas import (
    DailyWeather,
    HourlyWeather,
    Site,
    TimeWindow,
    WeatherDataQuality,
    WeatherForecast,
)
from workforce_agent.schemas.common import zoneinfo_of
from workforce_agent.weather.exceptions import WeatherIncompleteError

HOURLY_VARIABLE_MAP = {
    "temperature_2m": "temperature_c",
    "relative_humidity_2m": "relative_humidity_pct",
    "apparent_temperature": "apparent_temperature_c",
    "dew_point_2m": "dew_point_c",
    "wet_bulb_temperature_2m": "wet_bulb_temperature_c",
    "precipitation": "precipitation_mm",
    "precipitation_probability": "precipitation_probability_pct",
    "weather_code": "weather_code",
    "wind_speed_10m": "wind_speed_ms",
    "wind_gusts_10m": "wind_gusts_ms",
    "shortwave_radiation": "shortwave_radiation_wm2",
}

REQUIRED_HOURLY_VARIABLES = (
    "temperature_2m",
    "relative_humidity_2m",
    "apparent_temperature",
    "precipitation",
    "weather_code",
    "wind_speed_10m",
)

DAILY_VARIABLE_MAP = {
    "temperature_2m_max": "temperature_max_c",
    "temperature_2m_min": "temperature_min_c",
    "precipitation_sum": "precipitation_sum_mm",
    "shortwave_radiation_sum": "shortwave_radiation_sum_mj_m2",
}


def parse_provider_time(value: str, tz: ZoneInfo) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise WeatherIncompleteError(f"invalid provider timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=tz)
    return parsed.astimezone(tz)


def _series(hourly: Mapping[str, Any], name: str, length: int) -> Sequence[Any]:
    values = hourly.get(name)
    if values is None:
        return [None] * length
    if len(values) != length:
        raise WeatherIncompleteError(
            f"hourly.{name} length {len(values)} does not match hourly.time length {length}"
        )
    return values


def _staleness(
    payload: Mapping[str, Any],
    last_hour: datetime,
    issued: datetime,
    tz: ZoneInfo,
    stale_after: timedelta,
) -> tuple[bool, str | None]:
    current = payload.get("current")
    if isinstance(current, Mapping) and current.get("time"):
        current_time = parse_provider_time(str(current["time"]), tz).astimezone(timezone.utc)
        if issued - current_time > stale_after:
            return True, "provider current observation is older than the staleness threshold"
        return False, None
    if issued - last_hour > stale_after:
        return True, "latest hourly timestamp is older than the staleness threshold"
    return False, None


def map_open_meteo_forecast(
    payload: Mapping[str, Any],
    *,
    site: Site,
    source: str,
    issued_at: datetime,
    requested_window: TimeWindow | None = None,
    stale_after: timedelta = timedelta(hours=3),
) -> WeatherForecast:
    hourly = payload.get("hourly")
    if not isinstance(hourly, Mapping) or "time" not in hourly:
        raise WeatherIncompleteError("Open-Meteo payload is missing hourly.time")

    times = hourly["time"]
    if not times:
        raise WeatherIncompleteError("Open-Meteo payload has an empty hourly.time series")

    tz_name = payload.get("timezone") or site.timezone
    tz = zoneinfo_of(tz_name)
    valid_times = [parse_provider_time(item, tz) for item in times]

    for i in range(1, len(valid_times)):
        if valid_times[i] <= valid_times[i - 1]:
            raise WeatherIncompleteError(
                f"Open-Meteo hourly.time series contains non-chronological or duplicate timestamps: "
                f"{times[i - 1]} -> {times[i]}"
            )

    missing_variables = [name for name in REQUIRED_HOURLY_VARIABLES if name not in hourly]
    series = {
        provider_name: _series(hourly, provider_name, len(times))
        for provider_name in HOURLY_VARIABLE_MAP
    }

    hours: list[HourlyWeather] = []
    incomplete_hour_count = 0
    for index, timestamp in enumerate(valid_times):
        fields = {
            model_field: series[provider_name][index]
            for provider_name, model_field in HOURLY_VARIABLE_MAP.items()
        }
        hour = HourlyWeather(valid_at=timestamp.astimezone(timezone.utc), **fields)
        if hour.missing_fields():
            incomplete_hour_count += 1
        hours.append(hour)

    valid_from = hours[0].valid_at
    last_hour = hours[-1].valid_at
    valid_until = last_hour + timedelta(hours=1)

    issued = issued_at.astimezone(timezone.utc)
    past_hour_count = sum(1 for h in hours if h.valid_at < issued)

    covers_requested = True
    notes: list[str] = []
    if requested_window is not None:
        request_start = requested_window.start.astimezone(timezone.utc)
        request_end = requested_window.end.astimezone(timezone.utc)
        covers_requested = valid_from <= request_start and valid_until >= request_end
        if not covers_requested:
            notes.append("forecast does not fully cover the requested planning window")

    is_stale, stale_note = _staleness(payload, last_hour, issued, tz, stale_after)
    if stale_note:
        notes.append(stale_note)

    if missing_variables:
        notes.append("missing required hourly variables: " + ", ".join(missing_variables))
    if incomplete_hour_count:
        notes.append(f"{incomplete_hour_count} hourly slots have null required fields")
    if past_hour_count:
        notes.append(f"{past_hour_count} hourly slots precede issued_at (elapsed on local calendar day)")

    is_complete = not missing_variables and incomplete_hour_count == 0
    quality = WeatherDataQuality(
        is_complete=is_complete,
        is_stale=is_stale,
        covers_requested_window=covers_requested,
        missing_variables=missing_variables,
        incomplete_hour_count=incomplete_hour_count,
        past_hour_count=past_hour_count,
        notes=notes,
    )

    daily_models: list[DailyWeather] = []
    daily = payload.get("daily")
    if isinstance(daily, Mapping) and "time" in daily:
        daily_times = daily["time"]
        if isinstance(daily_times, Sequence):
            daily_series = {
                provider_name: _series(daily, provider_name, len(daily_times))
                for provider_name in DAILY_VARIABLE_MAP
            }
            for idx, date_item in enumerate(daily_times):
                valid_date = (
                    date_item
                    if isinstance(date_item, date)
                    else date.fromisoformat(str(date_item))
                )
                daily_fields = {
                    model_field: daily_series[provider_name][idx]
                    for provider_name, model_field in DAILY_VARIABLE_MAP.items()
                }
                daily_models.append(DailyWeather(valid_on=valid_date, **daily_fields))

    return WeatherForecast(
        site_id=site.site_id,
        issued_at=issued,
        source=source,
        valid_from=valid_from,
        valid_until=valid_until,
        hourly=hours,
        daily=daily_models,
        quality=quality,
    )
