from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from workforce_agent.config import get_settings
from workforce_agent.locations import (
    LocationProfile,
    list_location_ids,
    load_location,
    load_site,
)
from workforce_agent.planning import BaselineExistsError, PlanningRunStore
from workforce_agent.schemas import (
    BaselineSnapshot,
    PlanningRunRequest,
    ScheduleProposal,
    Site,
    WeatherForecast,
    Worker,
)
from workforce_agent.weather.client import build_weather_client
from workforce_agent.weather.exceptions import (
    WeatherError,
    WeatherIncompleteError,
    WeatherUnavailableError,
)

logger = logging.getLogger("workforce_agent.api")

app = FastAPI(
    title="Climate-Resilient Workforce Agent API",
    version="0.1.0",
    description="HTTP API for climate-resilient workforce scheduling, weather ingestion, and safety policies.",
)


def _planning_run_store() -> PlanningRunStore:
    return PlanningRunStore(get_settings().planning_runs_db_path)


# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
@app.get("/", tags=["Health"])
def health_check() -> dict[str, Any]:
    """Liveness probe reporting API version and status."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "message": "Climate-Resilient Workforce Agent API is running.",
    }


@app.get("/api/sites", response_model=list[Site], tags=["Catalog"])
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


@app.get("/api/locations/{location_id}", response_model=LocationProfile, tags=["Catalog"])
def get_location_catalog(location_id: str) -> LocationProfile:
    """Get location catalog profile including display name and facilities."""
    try:
        return load_location(location_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Location catalog '{location_id}' not found.",
        )


@app.get("/api/weather/{site_id}", response_model=WeatherForecast, tags=["Weather"])
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


@app.get("/api/workers", response_model=list[Worker], tags=["Workforce"])
def get_workers(site_id: str | None = None) -> list[Worker]:
    """List available technician profiles and certifications."""
    # When persistent worker DB is added, filter by site_id
    return []


@app.get("/api/schedules/{site_id}", response_model=list[ScheduleProposal], tags=["Schedules"])
def get_schedule_proposals(site_id: str) -> list[ScheduleProposal]:
    """Retrieve active schedule proposals generated for a site."""
    return []


@app.post("/api/planning-runs", response_model=BaselineSnapshot, status_code=201, tags=["Planning"])
def create_planning_run(request: PlanningRunRequest) -> BaselineSnapshot:
    """Capture and persist the original schedule and its baseline evaluation."""
    try:
        return _planning_run_store().create_baseline(
            request.planning_run_id, request.dataset, request.assignments, request.unscheduled
        )
    except BaselineExistsError as err:
        raise HTTPException(status_code=409, detail=str(err)) from err
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err


@app.get(
    "/api/planning-runs/{planning_run_id}/baseline",
    response_model=BaselineSnapshot,
    tags=["Planning"],
)
def get_planning_run_baseline(planning_run_id: str) -> BaselineSnapshot:
    """Retrieve the immutable baseline captured for a planning run."""
    snapshot = _planning_run_store().get_baseline(planning_run_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Baseline snapshot not found.")
    return snapshot


def run() -> None:
    """Entry point for running the API with uvicorn."""
    import uvicorn

    uvicorn.run("workforce_agent.api:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
