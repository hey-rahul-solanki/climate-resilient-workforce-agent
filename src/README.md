# Climate-Resilient Workforce Agent — Backend

Core Python service for AI-powered workforce scheduling, real-time meteorological ingestion, and occupational heat-stress safety policy evaluation. Built with **FastAPI**, **Pydantic v2**, and **HTTPX**.

---

## 🎯 Hackathon AI Agent

**New AI Components for Hackathon:**
- `src/workforce_agent/ai/weather_safety.py` - Weather safety assessment
- `src/workforce_agent/ai/schedule_checker.py` - Free slot checking
- `src/workforce_agent/ai/location_service.py` - OpenStreetMap integration

**See [HACKATHON_AI_AGENT.md](../HACKATHON_AI_AGENT.md) for implementation details.**

---

## Quick Start

### 1. Environment Setup

Ensure you have Python 3.11+ installed. Activate your virtual environment and install the package with API and development extras:

#### Using `uv` (Recommended)
```bash
# Create and activate virtual environment (if not already created)
uv venv .venv
source .venv/bin/activate

# Install with backend API dependencies (FastAPI, Uvicorn) & dev tools
uv pip install -e ".[dev,api]"
```

#### Using standard `pip`
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with backend API dependencies & dev tools
pip install -e ".[dev,api]"
```

> [!IMPORTANT]
> The backend HTTP server requires the `api` optional dependencies (`fastapi`, `uvicorn`). If you only installed `.[dev]`, install `.[api]` before starting the server.

---

## Running the Backend Server

Always ensure your virtual environment is activated (`source .venv/bin/activate`) from the repository root.

### Recommended: Using Uvicorn with Auto-Reload
```bash
uvicorn workforce_agent.api:app --host 0.0.0.0 --port 8000 --reload
```

### Alternative: Using the CLI Entrypoint
```bash
workforce-api
```

### Alternative: Running as a Python Module
```bash
python -m workforce_agent.api
```

### Alternative: Using `uv run` directly
```bash
uv run uvicorn workforce_agent.api:app --host 0.0.0.0 --port 8000 --reload
```

> [!WARNING]
> **Common Error:** Do not run `python3 -m api.py` or `python3 api.py`. 
> - Python `-m` expects a module dot-path, not a filename with `.py`.
> - The package module is located at `workforce_agent.api`.
> - Always run with the virtual environment active so `fastapi` and `uvicorn` are resolved.

Once running:
- **API Base URL**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## REST API Endpoints

| Method | Endpoint | Description | Query / Path Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` or `/` | Liveness probe reporting status & version | None |
| `GET` | `/api/sites` | List all industrial facilities across registered location catalogs | None |
| `GET` | `/api/locations/{location_id}` | Retrieve full location catalog profile and site metadata | `location_id` (e.g. `vadodara-gujarat`) |
| `GET` | `/api/weather/{site_id}` | Fetch normalized hourly weather forecast with WBGT & heat index | `site_id` (e.g. `VAD-PLANT-01`), `forecast_days` (1–14, default 3) |
| `GET` | `/api/workers` | List available technician profiles and certifications | `site_id` (optional filter) |
| `GET` | `/api/schedules/{site_id}` | Retrieve generated schedule proposals and assignments | `site_id` |
| `POST` | `/api/safety/assessments` | Assess a proposed task window against a supplied climate policy and forecast | Work order, policy, forecast, proposed start |
| `POST` | `/api/planning-cycles` | Persist a planning cycle's original schedule and baseline metrics | Dataset, assignments, unscheduled work orders |
| `GET` | `/api/planning-cycles/{planning_cycle_id}/baseline` | Retrieve the immutable baseline snapshot | `planning_cycle_id` |

Planning cycle baselines are stored in SQLite at `WORKFORCE_PLANNING_CYCLES_DB_PATH` (default: `data/planning_cycles.sqlite3`). The snapshot captures the exact input dataset and original assignments. `evaluate_schedule()` in `workforce_agent.planning` is the shared, versioned metric implementation for baseline and later proposal evaluation; its version is stored with each snapshot. A planning cycle ID can be created only once.

### Sample Requests

```bash
# Health check
curl http://localhost:8000/health

# List registered industrial sites
curl http://localhost:8000/api/sites

# Fetch 3-day weather forecast for Vadodara Plant 01
curl "http://localhost:8000/api/weather/VAD-PLANT-01?forecast_days=3"
```

---

## Weather Ingestion CLI (`workforce-weather`)

The backend includes a standalone CLI tool for testing weather ingestion and inspecting normalized data:

### 1. Live Fetch from Open-Meteo
```bash
workforce-weather --location-id vadodara-gujarat --site-id VAD-PLANT-01 --forecast-days 3
```

### 2. Deterministic / Offline Mode using Fixture
```bash
export WORKFORCE_WEATHER_SOURCE=fixture
export WORKFORCE_FIXTURE_PATH=tests/fixtures/open_meteo_vadodara.json
workforce-weather --location-id vadodara-gujarat --site-id VAD-PLANT-01
```

---

## Environment Configuration

Backend configuration uses Pydantic Settings (`workforce_agent.config.Settings`). All variables can be configured via environment variables prefixed with `WORKFORCE_`:

| Environment Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `WORKFORCE_WEATHER_SOURCE` | `string` | `"open-meteo"` | Weather provider: `"open-meteo"` or `"fixture"` |
| `WORKFORCE_OPEN_METEO_BASE_URL` | `string` | `"https://api.open-meteo.com/v1/forecast"` | Open-Meteo API endpoint |
| `WORKFORCE_WEATHER_STALE_AFTER_MINUTES` | `int` | `180` | Maximum minutes before forecast is flagged stale |
| `WORKFORCE_WEATHER_TIMEOUT_SECONDS` | `float` | `20.0` | HTTP request timeout for weather provider calls |
| `WORKFORCE_FIXTURE_PATH` | `path` | `None` | Path to JSON fixture file when using fixture source |
| `WORKFORCE_DEFAULT_LOCATION_ID` | `string` | `"vadodara-gujarat"` | Fallback location profile identifier |

---

## Project Structure

```text
src/workforce_agent/
├── __init__.py           # Package root & exports
├── api.py                # FastAPI app, endpoints, CORS middleware, runner
├── config.py             # Pydantic Settings (WORKFORCE_* env configuration)
├── locations/            # Industrial site catalog definitions
│   ├── __init__.py       # Catalog loaders (load_location, load_site)
│   └── vadodara.json     # Demo industrial location profile (Vadodara, Gujarat)
├── schemas/              # Pydantic v2 validated domain schemas
│   ├── common.py         # GeoLocation, TimeInterval, RiskLevel, etc.
│   └── entities.py       # Site, Worker, WeatherForecast, ScheduleProposal, SafetyPolicy
└── weather/              # Meteorological ingestion subsystem
    ├── cli.py            # workforce-weather command-line interface
    ├── client.py         # OpenMeteoClient, FixtureWeatherClient, factory
    ├── exceptions.py     # WeatherUnavailableError, WeatherIncompleteError
    └── mapper.py         # OpenMeteo response parser & hourly normalization
```

---

## Running Backend Tests

The test suite uses `pytest` and `respx` for mock HTTP assertions:

```bash
# Run all unit and mock tests (runs fast, no internet needed)
pytest

# Or via uv:
uv run pytest

# Run live network integration tests against the live Open-Meteo API
pytest -m network
```

---

## Adding New Locations

Locations are pure data, not code. To add a new industrial site or geography:
1. Create a new JSON file in `src/workforce_agent/locations/` (e.g. `mumbai.json`).
2. Follow the structure of [vadodara.json](file:///Users/rahulsolanki/Documents/climate-resilient-workforce-agent/src/workforce_agent/locations/vadodara.json).
3. The catalog will be automatically discovered by `list_location_ids()` and exposed over `GET /api/sites`.
