from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, Query, Depends, Response

from workforce_agent.agent import Principal
from workforce_agent.config import get_settings
from workforce_agent.locations import (
    LocationProfile,
    list_location_ids,
    load_location,
    load_site,
)
from workforce_agent.planning import BaselineExistsError, PlanningCycleStore
from workforce_agent.schemas import (
    BaselineSnapshot,
    ClimateRiskAssessment,
    PlanningCycleRequest,
    SafetyAssessmentRequest,
    ScheduleProposal,
    Site,
    WeatherForecast,
    Worker,
)
from workforce_agent.weather.client import build_weather_client
from workforce_agent.safety import assess_work_window
from workforce_agent.weather.exceptions import (
    WeatherError,
    WeatherIncompleteError,
    WeatherUnavailableError,
)

logger = logging.getLogger("calendar_backend.http_api")
router = APIRouter()


def _planning_cycle_store() -> PlanningCycleStore:
    return PlanningCycleStore(get_settings().planning_cycles_db_path)


@router.get("/api/sites", response_model=list[Site], tags=["Catalog"])
def get_sites() -> list[Site]:
    """List all industrial sites across registered location catalogs."""
    sites: list[Site] = []
    for loc_id in list_location_ids():
        try:
            profile = load_location(loc_id)
            sites.extend(profile.sites)
        except Exception as err:
            logger.warning("Failed to load catalog %s: %s", loc_id, err)
    return sites


@router.get("/api/locations/{location_id}", response_model=LocationProfile, tags=["Catalog"])
def get_location_catalog(location_id: str) -> LocationProfile:
    """Get location catalog profile including display name and facilities."""
    try:
        return load_location(location_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Location catalog '{location_id}' not found.",
        )


@router.get("/api/weather/{site_id}", response_model=WeatherForecast, tags=["Weather"])
def get_weather_forecast(
    site_id: str,
    forecast_days: int = Query(default=3, ge=1, le=14),
    location_id: str | None = None,
) -> WeatherForecast:
    """Fetch normalized hourly weather forecast for a site."""
    try:
        site = load_site(site_id, location_id=location_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Site '{site_id}' not found.",
        )

    settings = get_settings()
    client = build_weather_client(settings)

    try:
        return client.get_forecast(site, forecast_days=forecast_days)
    except (WeatherUnavailableError, WeatherIncompleteError) as err:
        raise HTTPException(status_code=503, detail=str(err))
    except WeatherError as err:
        raise HTTPException(status_code=502, detail=str(err))


@router.get("/api/workers", response_model=list[Worker], tags=["Workforce"])
def get_workers(site_id: str | None = None) -> list[Worker]:
    """List available technician profiles and certifications."""
    # When persistent worker DB is added, filter by site_id
    return []


@router.get("/api/schedules/{site_id}", response_model=list[ScheduleProposal], tags=["Schedules"])
def get_schedule_proposals(site_id: str) -> list[ScheduleProposal]:
    """Retrieve active schedule proposals generated for a site."""
    return []


@router.post(
    "/api/safety/assessments",
    response_model=ClimateRiskAssessment,
    tags=["Safety"],
)
def create_safety_assessment(request: SafetyAssessmentRequest) -> ClimateRiskAssessment:
    """Evaluate a proposed task window against the supplied policy and forecast."""
    if request.work_order.site_id != request.forecast.site_id:
        raise HTTPException(status_code=422, detail="work order and forecast site IDs must match")
    return assess_work_window(
        request.work_order,
        request.policy,
        request.forecast,
        window_start=request.proposed_start,
    )


@router.post("/api/planning-cycles", response_model=BaselineSnapshot, status_code=201, tags=["Planning"])
def create_planning_cycle(request: PlanningCycleRequest) -> BaselineSnapshot:
    """Capture and persist the original schedule and its baseline evaluation."""
    try:
        return _planning_cycle_store().create_baseline(
            request.planning_cycle_id, request.dataset, request.assignments, request.unscheduled
        )
    except BaselineExistsError as err:
        raise HTTPException(status_code=409, detail=str(err)) from err
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err


@router.get(
    "/api/planning-cycles/{planning_cycle_id}/baseline",
    response_model=BaselineSnapshot,
    tags=["Planning"],
)
def get_planning_cycle_baseline(planning_cycle_id: str) -> BaselineSnapshot:
    """Retrieve the immutable baseline captured for a planning cycle."""
    snapshot = _planning_cycle_store().get_baseline(planning_cycle_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Baseline snapshot not found.")
    return snapshot


@router.get('/api/calendar/demo', tags=['Calendar'])
def get_demo_calendar(day: str = '2026-10-17'):
    """Explicit fixture endpoint; never represents connected calendar or forecast data."""
    from datetime import date
    from workforce_agent.calendar import demo_calendar
    try:
        return demo_calendar(date.fromisoformat(day))
    except ValueError as err:
        raise HTTPException(status_code=422, detail='Expected an ISO date') from err


from datetime import date as CalendarDate
from calendar_backend.auth import browser_identity
from workforce_agent.day_schedule import get_day_schedule
from workforce_agent.schemas.calendar import DayCalendarResponse


@router.get('/api/calendar/day', response_model=DayCalendarResponse, tags=['Calendar'])
def get_calendar_day(response: Response, site_id: str, date: CalendarDate, principal: Principal = Depends(browser_identity)):
    """Read one site-local day; fixture source is explicit and provider credentials are unnecessary."""
    response.headers['Cache-Control'] = 'no-store'
    if 'read' not in principal.permissions or site_id not in principal.sites:
        raise HTTPException(403, 'Not authorized to read this site schedule')
    try:
        return get_day_schedule(site_id,date)
    except KeyError as err:
        raise HTTPException(404, 'No schedule source configured for this site') from err


