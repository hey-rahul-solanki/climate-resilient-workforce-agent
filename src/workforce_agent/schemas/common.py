from __future__ import annotations

from datetime import datetime, time
from enum import StrEnum
from zoneinfo import ZoneInfo, available_timezones

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TimeWindow(StrictModel):
    """Inclusive start, exclusive end, timezone-aware interval."""

    start: datetime
    end: datetime

    @field_validator("start", "end")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def end_after_start(self) -> TimeWindow:
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self


class OperatingHours(StrictModel):
    """Local operating hours for one weekday. Monday = 0, Sunday = 6."""

    weekday: int = Field(..., ge=0, le=6)
    start_local: time
    end_local: time

    @model_validator(mode="after")
    def end_after_start(self) -> OperatingHours:
        if self.end_local <= self.start_local:
            raise ValueError("end_local must be after start_local")
        return self


def validate_iana_timezone(value: str) -> str:
    if value not in available_timezones():
        raise ValueError(f"unknown IANA timezone: {value}")
    return value


def zoneinfo_of(timezone: str) -> ZoneInfo:
    return ZoneInfo(validate_iana_timezone(timezone))


class Priority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExposureType(StrEnum):
    OUTDOOR_HEAT = "outdoor_heat"
    OUTDOOR_STORM = "outdoor_storm"
    HEIGHT = "height"
    CONFINED_SPACE = "confined_space"
    ELECTRICAL = "electrical"
    INDOOR_CONTROLLED = "indoor_controlled"


class SiteHazard(StrEnum):
    EXTREME_HEAT = "extreme_heat"
    MONSOON = "monsoon"
    HIGH_WIND = "high_wind"
    LIGHTNING = "lightning"
    HEIGHT = "height"
    CONFINED_SPACE = "confined_space"
    ELECTRICAL = "electrical"
    CHEMICAL = "chemical"


class OperationalStatus(StrEnum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


class Certification(StrictModel):
    name: str = Field(..., min_length=1)
    expires_at: datetime | None = None

    @field_validator("expires_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("expires_at must be timezone-aware")
        return value


class BreakRequirements(StrictModel):
    min_break_minutes: int = Field(..., ge=0)
    max_continuous_work_minutes: int = Field(..., gt=0)
    cooling_break_minutes: int = Field(..., ge=0)


class HeatMetric(StrEnum):
    TEMPERATURE_C = "temperature_c"
    APPARENT_TEMPERATURE_C = "apparent_temperature_c"
    WET_BULB_TEMPERATURE_C = "wet_bulb_temperature_c"


class ScheduleDecision(StrEnum):
    PROCEED = "proceed"
    RESCHEDULE = "reschedule"
    EXTRA_BREAKS = "extra_breaks"
    BLOCKED = "blocked"


class MissingWeatherAction(StrEnum):
    BLOCK = "block"
    REQUIRE_REVIEW = "require_review"
