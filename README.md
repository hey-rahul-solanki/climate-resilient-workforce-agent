# climate-resilient-workforce-agent

AI-powered workforce scheduling that combines real-time weather intelligence, operational constraints and safety policies to protect field workers and reduce operational delays.

The first milestone is the planning data contract and weather ingestion. Location catalogs are data, not code: Vadodara, Gujarat is the demo catalog, and additional sites can be added as JSON without changing the weather client.

A companion modern React + Vite frontend is located in `frontend/` to monitor sites, inspect weather ingestion parameters, and visualize schedule safety policies.

---

## Python Backend Setup & Testing

### 1. Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

*(Alternatively, if using `uv`: `uv run --extra dev pytest`)*

### 2. Data Contracts

Validated Pydantic v2 models live in `src/workforce_agent/schemas`:

- `Worker`, `Site`, `WorkOrder`, `Equipment`
- `WeatherForecast` (provider-neutral hourly conditions)
- `SafetyPolicy`
- `ScheduleAssignment`, `ScheduleProposal`

Required planning fields have no silent defaults. Invalid or missing values raise actionable `ValidationError`s.

### 3. Weather Ingestion

Open-Meteo is the default provider. Forecasts are normalized to `WeatherForecast`, including completeness and staleness flags. Missing values are preserved as `null` and never treated as safe working conditions.

Deterministic tests and demos can use a fixture:

```bash
export WORKFORCE_WEATHER_SOURCE=fixture
export WORKFORCE_FIXTURE_PATH=tests/fixtures/open_meteo_vadodara.json
workforce-weather --location-id vadodara-gujarat --site-id VAD-PLANT-01
```

Live fetch for the demo plant (22.3072, 73.1812):

```bash
workforce-weather --location-id vadodara-gujarat --site-id VAD-PLANT-01 --forecast-days 3
```

Add another geography by placing a JSON file next to `src/workforce_agent/locations/vadodara.json`.

### 4. Starting the FastAPI Backend Server

Install the API dependencies (FastAPI and Uvicorn):

```bash
pip install -e ".[dev,api]"
```

Start the FastAPI server:

```bash
# Option 1: Using uvicorn with live auto-reload
uvicorn workforce_agent.api:app --host 0.0.0.0 --port 8000 --reload

# Option 2: Using the CLI entrypoint
workforce-api

# Option 3: Running the Python module directly
python -m workforce_agent.api
```

Once started:
- **API Base URL**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Sites API**: [http://localhost:8000/api/sites](http://localhost:8000/api/sites)
- **Weather API**: [http://localhost:8000/api/weather/VAD-PLANT-01?forecast_days=3](http://localhost:8000/api/weather/VAD-PLANT-01?forecast_days=3)

CORS is enabled by default to allow communication with the frontend development server at [http://localhost:5173](http://localhost:5173).

### 5. Running Python Tests

Run the test suite:

```bash
pytest
```

Run optional live network tests calling Open-Meteo:

```bash
pytest -m network
```


---

## Frontend Setup & Development

The frontend is a standalone React + Vite + TypeScript application in `frontend/`.

### 1. Installing Frontend Dependencies

```bash
cd frontend
npm install
```

### 2. Configuring the Backend API URL

The frontend communicates with the Python backend via the `VITE_API_BASE_URL` environment variable.

Create a `.env` file from the example template:

```bash
cd frontend
cp .env.example .env
```

Default configuration in `frontend/.env`:

```env
# URL where your Python API server will run
VITE_API_BASE_URL=http://localhost:8000
```

You can change this URL to any running backend host or port.

### 3. Starting the React Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at [http://localhost:5173](http://localhost:5173).

> **Independent Operation:** The frontend can run completely independently in standalone mode. When the Python backend is offline or not yet started, the UI displays clear connection diagnostics and defaults to local location catalog data without throwing unhandled errors or fabricating mock backend responses.

### 4. Building the Frontend for Production

```bash
cd frontend
npm run build
```

Production build artifacts will be generated in `frontend/dist/`.

To test or preview the production build locally:

```bash
npm run preview
```

---

## Frontend & Backend Communication

The project uses a clean, decoupled architecture:

```text
┌─────────────────────────────────┐           HTTP / REST           ┌───────────────────────────────────┐
│       React + Vite Frontend     │  ◄────────────────────────────► │           Python Backend          │
│   (frontend/src/services/api.ts)│  VITE_API_BASE_URL=http://...   │      (workforce_agent core)       │
└─────────────────────────────────┘                                 └───────────────────────────────────┘
               │                                                                      │
        TypeScript Types                                                       Pydantic Models
 (frontend/src/types/workforce.ts) ◄───────── Synchronized Contract ────────► (src/workforce_agent/schemas/)
```

1. **Decoupled Lifecycle**: The Python core handles data validation, weather ingestion, and schedule optimization. The React frontend handles user visualization, site overview, and schedule monitoring.
2. **Synchronized Types**: TypeScript interfaces in `frontend/src/types/workforce.ts` mirror the Pydantic v2 models in `src/workforce_agent/schemas/` (`Site`, `Worker`, `WeatherForecast`, `ScheduleProposal`).
3. **HTTP Client**: The frontend API service (`frontend/src/services/api.ts`) contains typed request functions and non-blocking health checks (`checkBackendHealth()`).
4. **Planned Endpoints**:
   - `GET /health`: Liveness probe and version check.
   - `GET /api/sites`: Returns registered industrial facility sites.
   - `GET /api/weather/{site_id}?forecast_days=3`: Returns normalized hourly forecast.
   - `GET /api/workers`: Returns worker skills and availability.
   - `POST /api/schedules/proposals`: Triggers agent schedule optimization.
