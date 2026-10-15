from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import uuid4

from pydantic import AliasChoices, Field, field_validator, model_validator

from workforce_agent.schemas.common import (
    BreakRequirements,
    Certification,
    ExposureType,
    HeatMetric,
    MissingWeatherAction,
    OperatingHours,
    OperationalStatus,
    PolicyAction,
    Priority,
    RuleAction,
    RuleSeverity,
    ScheduleDecision,
    SiteHazard,
    StrictModel,
    TimeWindow,
    validate_iana_timezone,
)



class Worker(StrictModel):
    worker_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    skills: list[str] = Field(..., min_length=1)
    certifications: list[Certification]
    availability_windows: list[TimeWindow] = Field(..., min_length=1)
    break_requirements: BreakRequirements
    max_shift_duration_minutes: int = Field(..., gt=0)

    @field_validator("skills")
    @classmethod
    def skills_not_blank(cls, values: list[str]) -> list[str]:
        cleaned = [item.strip() for item in values]
        if any(not item for item in cleaned):
            raise ValueError("skills must not contain blank values")
        return cleaned


class Site(StrictModel):
    site_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timezone: str
    operating_hours: list[OperatingHours] = Field(..., min_length=1)
    hazards: list[SiteHazard]

    @field_validator("timezone")
    @classmethod
    def iana_timezone(cls, value: str) -> str:
        return validate_iana_timezone(value)


class WorkOrder(StrictModel):
    work_order_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    duration_minutes: int = Field(..., gt=0)
    priority: Priority
    site_id: str = Field(..., min_length=1)
    required_skills: list[str] = Field(..., min_length=1)
    required_certifications: list[str]
    min_crew_size: int = Field(..., ge=1)
    max_crew_size: int = Field(..., ge=1)
    depends_on: list[str]
    required_equipment_ids: list[str]
    planning_window: TimeWindow
    deadline: datetime | None = None
    exposure_type: ExposureType
    expected_exposure_duration_minutes: int = Field(..., ge=0)
    exposure_windows: list[TimeWindow] | None = None
    is_weather_exposed: bool | None = Field(
        default=None,
        description="Whether the task is weather-exposed. Inferred from exposure_type if omitted.",
    )

    @field_validator("required_skills", "required_certifications", "depends_on", "required_equipment_ids")
    @classmethod
    def no_blank_ids(cls, values: list[str]) -> list[str]:
        cleaned = [item.strip() for item in values]
        if any(not item for item in cleaned):
            raise ValueError("list values must not contain blanks")
        return cleaned

    @field_validator("deadline")
    @classmethod
    def deadline_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("deadline must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_planning_constraints(self) -> WorkOrder:
        if self.max_crew_size < self.min_crew_size:
            raise ValueError("max_crew_size must be greater than or equal to min_crew_size")
        if self.work_order_id in self.depends_on:
            raise ValueError("a work order cannot depend on itself")
        if self.expected_exposure_duration_minutes > self.duration_minutes:
            raise ValueError("expected_exposure_duration_minutes cannot exceed duration_minutes")
        if self.deadline is not None and self.deadline < self.planning_window.start:
            raise ValueError("deadline cannot be before planning_window.start")

        outdoor_types = {ExposureType.OUTDOOR_HEAT, ExposureType.OUTDOOR_STORM}
        if self.is_weather_exposed is None:
            object.__setattr__(self, "is_weather_exposed", self.exposure_type in outdoor_types)
        else:
            if self.is_weather_exposed and self.exposure_type == ExposureType.INDOOR_CONTROLLED:
                raise ValueError("indoor_controlled work order cannot be weather-exposed")
            if not self.is_weather_exposed and self.exposure_type in outdoor_types:
                raise ValueError(
                    f"work order with exposure_type '{self.exposure_type}' cannot have is_weather_exposed=False"
                )
        return self


class Equipment(StrictModel):
    equipment_id: str = Field(..., min_length=1)
    equipment_type: str = Field(..., min_length=1)
    availability_windows: list[TimeWindow] = Field(..., min_length=1)
    operational_status: OperationalStatus
    compatible_task_types: list[str] = Field(..., min_length=1)
    inspection_valid_until: datetime | None = None
    site_id: str | None = Field(
        default=None,
        min_length=1,
        description="Site ID where equipment is stationed, where applicable.",
    )

    @field_validator("compatible_task_types")
    @classmethod
    def task_types_not_blank(cls, values: list[str]) -> list[str]:
        cleaned = [item.strip() for item in values]
        if any(not item for item in cleaned):
            raise ValueError("compatible_task_types must not contain blank values")
        return cleaned

    @field_validator("inspection_valid_until")
    @classmethod
    def inspection_timezone(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("inspection_valid_until must be timezone-aware")
        return value


class HourlyWeather(StrictModel):
    valid_at: datetime = Field(
        ...,
        validation_alias=AliasChoices("valid_at", "observed_at"),
        description="UTC start of the hour these forecast values are valid for. Not an observation time.",
    )
    temperature_c: float | None = Field(default=None, description="Air temperature at 2 m, Celsius.")
    relative_humidity_pct: float | None = Field(default=None, ge=0, le=100, description="Relative humidity at 2 m, percent.")
    apparent_temperature_c: float | None = Field(
        default=None,
        description="Apparent temperature (feels-like) in Celsius, not WBGT.",
    )
    dew_point_c: float | None = Field(default=None, description="Dew point at 2 m, Celsius.")
    wet_bulb_temperature_c: float | None = Field(
        default=None,
        description=(
            "Psychrometric wet-bulb temperature at 2 m, Celsius "
            "(Open-Meteo wet_bulb_temperature_2m). This is not WBGT."
        ),
    )
    precipitation_mm: float | None = Field(
        default=None,
        ge=0,
        description="Precipitation sum over the preceding hour, millimetres.",
    )
    precipitation_probability_pct: float | None = Field(
        default=None, ge=0, le=100, description="Probability of precipitation, percent."
    )
    weather_code: int | None = Field(default=None, description="WMO weather interpretation code.")
    wind_speed_ms: float | None = Field(default=None, ge=0, description="Wind speed at 10 m, metres per second.")
    wind_gusts_ms: float | None = Field(default=None, ge=0, description="Wind gusts at 10 m, metres per second.")
    shortwave_radiation_wm2: float | None = Field(
        default=None,
        ge=0,
        description=(
            "Hourly shortwave radiation as preceding-hour mean, W/m² "
            "(Open-Meteo hourly shortwave_radiation). Not daily shortwave_radiation_sum."
        ),
    )

    @field_validator("weather_code", mode="before")
    @classmethod
    def coerce_weather_code(cls, value: object) -> int | None:
        if value is None or value == "":
            return None
        return int(value)

    @field_validator("valid_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("valid_at must be timezone-aware")
        return value

    def missing_fields(self) -> list[str]:
        required = (
            "temperature_c",
            "relative_humidity_pct",
            "apparent_temperature_c",
            "precipitation_mm",
            "weather_code",
            "wind_speed_ms",
        )
        return [name for name in required if getattr(self, name) is None]

    @property
    def observed_at(self) -> datetime:
        """Alias for valid_at for backward compatibility."""
        return self.valid_at


class DailyWeather(StrictModel):
    valid_on: date = Field(..., description="Local calendar date for these daily aggregates.")
    temperature_max_c: float | None = Field(default=None, description="Daily maximum air temperature, Celsius.")
    temperature_min_c: float | None = Field(default=None, description="Daily minimum air temperature, Celsius.")
    precipitation_sum_mm: float | None = Field(default=None, ge=0, description="Daily precipitation sum, millimetres.")
    shortwave_radiation_sum_mj_m2: float | None = Field(
        default=None,
        ge=0,
        description=(
            "Daily shortwave radiation sum, MJ/m² (Open-Meteo daily shortwave_radiation_sum). "
            "Do not treat this as hourly W/m²."
        ),
    )


class WeatherDataQuality(StrictModel):
    is_complete: bool
    is_stale: bool
    covers_requested_window: bool
    missing_variables: list[str]
    incomplete_hour_count: int = Field(..., ge=0)
    past_hour_count: int = Field(default=0, ge=0)
    notes: list[str]


class WeatherForecast(StrictModel):
    forecast_id: str = Field(default_factory=lambda: str(uuid4()))
    site_id: str = Field(..., min_length=1)
    issued_at: datetime = Field(
        ...,
        description="UTC timestamp when this forecast was retrieved from the provider.",
    )
    source: str = Field(..., min_length=1)
    valid_from: datetime = Field(
        ...,
        description="UTC start of the first hourly slot. Open-Meteo includes hours already elapsed on the local start day.",
    )
    valid_until: datetime = Field(
        ...,
        description="Exclusive UTC end of coverage (last hourly valid_at plus one hour).",
    )
    hourly: list[HourlyWeather]
    daily: list[DailyWeather] = Field(default_factory=list)
    quality: WeatherDataQuality

    @field_validator("issued_at", "valid_from", "valid_until")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("forecast timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validity_order(self) -> WeatherForecast:
        if self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be after valid_from")
        for i in range(1, len(self.hourly)):
            if self.hourly[i].valid_at <= self.hourly[i - 1].valid_at:
                raise ValueError("hourly timestamps must be strictly monotonically increasing")
        return self

    def future_hourly(self) -> list[HourlyWeather]:
        """Return hourly forecast slots that begin at or after issued_at."""
        return [h for h in self.hourly if h.valid_at >= self.issued_at]


class HeatThreshold(StrictModel):
    metric: HeatMetric
    caution_c: float
    high_c: float
    prohibitive_c: float

    @model_validator(mode="after")
    def ordered_thresholds(self) -> HeatThreshold:
        if not (self.caution_c < self.high_c < self.prohibitive_c):
            raise ValueError("heat thresholds must increase: caution < high < prohibitive")
        return self


class WorkRestRule(StrictModel):
    metric: HeatMetric
    min_c: float
    max_c: float
    work_minutes: int = Field(..., ge=0)
    rest_minutes: int = Field(..., ge=0)
    cooling_required: bool
    severity: RuleSeverity = RuleSeverity.WARNING
    required_action: PolicyAction = PolicyAction.EXTRA_BREAKS

    @model_validator(mode="after")
    def band_order(self) -> WorkRestRule:
        if self.max_c <= self.min_c:
            raise ValueError("max_c must be greater than min_c")
        return self


class SafetyRule(StrictModel):
    rule_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    severity: RuleSeverity
    required_action: PolicyAction
    description: str | None = None
    rule_type: str | None = None
    condition: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


OperationalConstraint = SafetyRule


class SafetyPolicy(StrictModel):
    policy_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    applies_to_exposure_types: list[ExposureType] = Field(..., min_length=1)
    heat_thresholds: list[HeatThreshold] = Field(..., min_length=1)
    work_rest_rules: list[WorkRestRule]
    rules: list[SafetyRule] = Field(default_factory=list)
    operational_constraints: list[SafetyRule] = Field(default_factory=list)
    max_wind_speed_ms: float | None = Field(default=None, gt=0)
    max_precipitation_mm: float | None = Field(default=None, ge=0)
    lightning_prohibits_work: bool
    prohibited_weather_codes: list[int]
    missing_weather_action: MissingWeatherAction


class ClimateRiskAssessment(StrictModel):
    """Policy result for one proposed work window, with its source forecast."""

    decision: ScheduleDecision
    reasons: list[str] = Field(..., min_length=1)
    requires_review: bool = False
    cooling_break_minutes: int = Field(..., ge=0)
    proposed_window: TimeWindow
    forecast_id: str = Field(..., min_length=1)
    forecast_issued_at: datetime

    @field_validator("forecast_issued_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("forecast_issued_at must be timezone-aware")
        return value


class SafetyAssessmentRequest(StrictModel):
    """Inputs to a single deterministic assessment call."""

    work_order: WorkOrder
    policy: SafetyPolicy
    forecast: WeatherForecast
    proposed_start: datetime

    @field_validator("proposed_start")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("proposed_start must be timezone-aware")
        return value


class CoolingBreak(StrictModel):
    window: TimeWindow
    reason: str = Field(..., min_length=1)


class ScheduleAssignment(StrictModel):
    assignment_id: str = Field(..., min_length=1)
    work_order_id: str = Field(..., min_length=1)
    site_id: str = Field(..., min_length=1)
    worker_ids: list[str] = Field(..., min_length=1)
    equipment_ids: list[str]
    scheduled_window: TimeWindow
    cooling_breaks: list[CoolingBreak]
    decision: ScheduleDecision
    rationale: str = Field(..., min_length=1)


class UnscheduledWorkOrder(StrictModel):
    work_order_id: str = Field(..., min_length=1)
    reasons: list[str] = Field(..., min_length=1)


class ScheduleProposal(StrictModel):
    proposal_id: str = Field(..., min_length=1)
    planning_cycle_id: str = Field(..., min_length=1)
    generated_at: datetime
    horizon: TimeWindow
    policy_id: str = Field(..., min_length=1)
    weather_forecast_ids: list[str]
    assignments: list[ScheduleAssignment]
    unscheduled: list[UnscheduledWorkOrder]
    notes: str | None = None

    @field_validator("generated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("generated_at must be timezone-aware")
        return value


class PlanningDataset(StrictModel):
    """Inputs captured once and reused to evaluate schedules in a planning cycle."""

    work_orders: list[WorkOrder]
    workers: list[Worker]
    equipment: list[Equipment]


class ScheduleMetrics(StrictModel):
    """Versioned, schedule-independent metrics shared by baseline and proposals."""

    definition_version: str = Field(..., min_length=1)
    input_work_order_count: int = Field(..., ge=0)
    input_worker_count: int = Field(..., ge=0)
    input_equipment_count: int = Field(..., ge=0)
    assignment_count: int = Field(..., ge=0)
    scheduled_work_order_count: int = Field(..., ge=0)
    worker_allocation_count: int = Field(..., ge=0)
    equipment_allocation_count: int = Field(..., ge=0)
    scheduled_minutes: int = Field(..., ge=0)
    unscheduled_work_order_count: int = Field(..., ge=0)


class BaselineSnapshot(StrictModel):
    """Immutable source schedule and its evaluation for a planning cycle."""

    snapshot_id: str = Field(..., min_length=1)
    planning_cycle_id: str = Field(..., min_length=1)
    captured_at: datetime
    dataset: PlanningDataset
    assignments: list[ScheduleAssignment]
    unscheduled: list[UnscheduledWorkOrder]
    metrics: ScheduleMetrics

    @field_validator("captured_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("captured_at must be timezone-aware")
        return value


class PlanningCycleRequest(StrictModel):
    planning_cycle_id: str = Field(..., min_length=1)
    dataset: PlanningDataset
    assignments: list[ScheduleAssignment]
    unscheduled: list[UnscheduledWorkOrder] = Field(default_factory=list)
