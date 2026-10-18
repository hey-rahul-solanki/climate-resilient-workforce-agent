"""Calendar activity input contract shared by deterministic climate services."""
from datetime import datetime, date as CalendarDate, time, timedelta
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from zoneinfo import ZoneInfo
from workforce_agent.schemas.common import ExposureType, TimeWindow, validate_iana_timezone


from workforce_agent.policy_windows import RestInterval


class CalendarActivity(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: str = Field(min_length=1)
    employee_id: str | None = Field(default=None, min_length=1)
    title: str | None = Field(default=None, min_length=1)
    start: datetime
    end: datetime
    site_id: str | None = None
    location: str | None = None
    kind: Literal['indoor','outdoor','unknown'] = 'unknown'
    exposure_type: ExposureType | None = None
    scheduled_rest: list[RestInterval] = Field(default_factory=list)
    mandatory_rest_intervals: list[TimeWindow] = Field(default_factory=list)

    @field_validator('site_id','location', mode='before')
    @classmethod
    def clean_location(cls, value):
        if isinstance(value,str):
            value = value.strip()
            return None if value.lower() in ('', 'unknown', 'unknown location', 'unspecified', 'tbd') else value
        return value

    @field_validator('kind', mode='before')
    @classmethod
    def unknown_classification(cls, value):
        return value if value in ('indoor','outdoor') else 'unknown'

    @model_validator(mode='after')
    def valid_interval(self):
        if self.start.tzinfo is None or self.end.tzinfo is None or self.end <= self.start:
            raise ValueError('Calendar activity requires an increasing timezone-aware interval')
        return self


class DaySite(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    timezone: str

    @field_validator('timezone')
    @classmethod
    def known_timezone(cls, value):
        return validate_iana_timezone(value)


class DayEmployee(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    team: str | None = None


class WarningMatch(BaseModel):
    """One warning's exact intersection with an activity, never safety clearance."""
    warning_id: str = Field(min_length=1)
    overlap: TimeWindow
    severity: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    policy: str | None = None


class DayActivity(CalendarActivity):
    employee_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    status: Literal['affected','needs-review','unflagged']
    reason: str
    warning_ids: list[str] = Field(default_factory=list)
    warning_matches: list[WarningMatch] = Field(default_factory=list)
    version: int = Field(default=1, ge=1)
    source_event_id: str = Field(min_length=1)


class DayWarning(TimeWindow):
    model_config = ConfigDict(extra='allow')
    id: str
    title: str
    severity: str
    measure: str
    policy: str


class DaySuggestion(BaseModel):
    id: str
    activity_id: str
    start: datetime | None
    end: datetime | None
    validation: str
    rationale: str

    @model_validator(mode='after')
    def valid_proposed_window(self):
        if self.start is not None or self.end is not None:
            if self.start is None or self.end is None:
                raise ValueError('Both proposed timestamps must be supplied')
            TimeWindow(start=self.start,end=self.end)
        return self


class DayWeather(BaseModel):
    status: str
    source: str
    updated_at: datetime | None

    @field_validator('updated_at')
    @classmethod
    def aware_update(cls, value):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError('Weather update timestamp must be timezone-aware')
        return value


class DayIntegrations(BaseModel):
    agent: str
    mcp: str
    calendar: str


class DayContextSubmission(BaseModel):
    """Consumer-owned schedule input, composed from the canonical day models."""
    model_config = ConfigDict(extra='forbid')
    date: CalendarDate
    site: DaySite
    window: TimeWindow
    employees: list[DayEmployee]
    activities: list[CalendarActivity]

    @model_validator(mode='after')
    def validate_submitted_schedule(self):
        timezone = ZoneInfo(self.site.timezone)
        day_start = datetime.combine(self.date, time.min, tzinfo=timezone)
        day_end = datetime.combine(self.date + timedelta(days=1), time.min, tzinfo=timezone)
        if not day_start <= self.window.start < self.window.end <= day_end:
            raise ValueError('Display window must be inside the selected site-local day')
        employee_ids = {employee.id for employee in self.employees}
        activity_ids = set()
        derived_fields = {'status', 'reason', 'warning_ids', 'warning_matches', 'policy_context', 'policy_blocks'}
        for activity in self.activities:
            if activity.id in activity_ids:
                raise ValueError('Activity IDs must be unique within the submitted day')
            activity_ids.add(activity.id)
            if not activity.employee_id or not activity.title:
                raise ValueError('Each submitted activity requires employee_id and title')
            if activity.employee_id not in employee_ids:
                raise ValueError('Activity references an unknown employee')
            if activity.site_id is not None and activity.site_id != self.site.id:
                raise ValueError('Activity site differs from the submitted site')
            if not activity.start < day_end or not activity.end > day_start:
                raise ValueError('Activity must overlap the selected site-local day')
            if derived_fields.intersection(activity.model_extra or {}):
                raise ValueError('Submit source activities without derived climate status or warning fields')
        return self


class DayCalendarResponse(BaseModel):
    """Selected local day. All event intervals are [start, end)."""
    date: CalendarDate
    site: DaySite
    window: TimeWindow
    employees: list[DayEmployee]
    activities: list[DayActivity]
    warnings: list[DayWarning]
    suggestions: list[DaySuggestion] = Field(default_factory=list)
    weather: DayWeather
    integrations: DayIntegrations
    mode: Literal['fixture', 'consumer-submitted'] = 'fixture'

    @model_validator(mode='after')
    def validate_day_and_references(self):
        timezone = ZoneInfo(self.site.timezone)
        start = datetime.combine(self.date,time.min,tzinfo=timezone)
        end = datetime.combine(self.date+timedelta(days=1),time.min,tzinfo=timezone)
        if not start <= self.window.start < self.window.end <= end:
            raise ValueError('Display window must be inside selected site-local day')
        employee_ids = {e.id for e in self.employees}
        activity_ids = {a.id for a in self.activities}
        if len(employee_ids) != len(self.employees) or len(activity_ids) != len(self.activities):
            raise ValueError('Employee and activity IDs must be unique within day')
        for activity in self.activities:
            if activity.employee_id not in employee_ids:
                raise ValueError('Activity references an unknown employee')
            if activity.site_id is not None and activity.site_id != self.site.id:
                raise ValueError('Activity site differs from selected site')
            if not activity.start < end or not activity.end > start:
                raise ValueError('Activity must overlap selected site-local day')
        return self
