# climate-resilient-workforce-agent

AI-powered workforce scheduling that combines real-time weather intelligence, operational constraints and safety policies to protect field workers and reduce operational delays.

The first milestone is the planning data contract and weather ingestion. Location catalogs are data, not code: Vadodara, Gujarat is the demo catalog, and additional sites can be added as JSON without changing the weather client.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Data contracts

Validated Pydantic v2 models live in `src/workforce_agent/schemas`:

- `Worker`, `Site`, `WorkOrder`, `Equipment`
- `WeatherForecast` (provider-neutral hourly conditions)
- `SafetyPolicy`
- `ScheduleAssignment`, `ScheduleProposal`

Required planning fields have no silent defaults. Invalid or missing values raise actionable `ValidationError`s.

## Weather

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

## Tests

```bash
pytest
pytest -m network   # optional live Open-Meteo call
```
