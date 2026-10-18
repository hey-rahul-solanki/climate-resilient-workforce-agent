# Climate-Resilient Workforce Agent — Frontend

Modern, responsive web interface for the Climate-Resilient Workforce Agent platform, built with React, Vite, and TypeScript.

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Copy the example environment configuration:

```bash
cp .env.example .env
```

By default, `VITE_API_BASE_URL` is set to `http://localhost:8010`. You can change this to point to your Python backend server.

### 3. Start Development Server

```bash
npm run dev
```

The application will start locally at [http://localhost:5173](http://localhost:5173). The frontend can run completely independently in standalone mode even when the backend is offline.

### 4. Build for Production

```bash
npm run build
```

Build outputs are generated in `frontend/dist/`.

### 5. Preview Production Build

```bash
npm run preview
```

## Available Scripts

- `npm run dev`: Starts the Vite development server with hot module reloading (HMR).
- `npm run build`: Type-checks with `tsc` and builds optimized production bundles.
- `npm run preview`: Locally previews the production build in `dist/`.
- `npm run typecheck`: Runs strict TypeScript type-checking (`tsc -b`).
- `npm run lint`: Runs code analysis via `eslint .`.

## Project Structure

```text
frontend/
├── public/                 # Static assets (favicons, icons)
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── ApiStatusCard.tsx   # Live connection probe & configuration
│   │   ├── Header.tsx          # App header & real-time status pill
│   │   ├── Layout.tsx          # Shell wrapper
│   │   ├── Navigation.tsx      # Main tab navigation
│   │   ├── SiteCard.tsx        # Industrial facility card
│   │   ├── StatCard.tsx        # Metric display card
│   │   └── StatusBadge.tsx     # Risk & status indicator badge
│   ├── data/               # Seed data matching Python catalogs
│   │   └── defaultCatalog.ts
│   ├── pages/              # Application views
│   │   ├── ApiPage.tsx         # Backend REST API documentation
│   │   ├── DashboardPage.tsx   # Executive overview & operations
│   │   ├── SchedulePlanningPage.tsx # Physiological policies & schedules
│   │   ├── SitesPage.tsx       # Industrial facilities & catalogs
│   │   └── WeatherViewPage.tsx # Meteorological ingestion contract
│   ├── services/           # Typed API communication layer
│   │   └── api.ts              # Base client, health check & endpoints
│   ├── types/              # TypeScript interfaces mirroring Pydantic models
│   │   ├── api.ts              # Connection & response schemas
│   │   └── workforce.ts        # Site, Worker, Weather, Schedule schemas
│   ├── App.tsx             # Root component & state management
│   ├── index.css           # Glassmorphic dark design system
│   └── main.tsx            # React application entry point
├── .env.example            # Sample environment variables
├── index.html              # HTML entry template
├── package.json            # Dependencies and scripts
├── tsconfig.json           # TypeScript configuration
└── vite.config.ts          # Vite configuration
```

## Backend Communication

The frontend interacts with the backend using the service client in `src/services/api.ts`:

- **Environment Config**: Uses `VITE_API_BASE_URL` to route requests.
- **Health Probing**: Performs non-blocking health checks against `GET /health`.
- **Domain Modeling**: Types in `src/types/workforce.ts` directly reflect Python Pydantic v2 schemas from `src/workforce_agent/schemas/`.
- **Standalone Capability**: When no backend server is active, the UI gracefully operates in standalone mode, allowing inspection of facility locations, weather rules, and policy thresholds without mock falsification.

### Starting the Python FastAPI Backend

To run the backend server alongside the frontend, run from the repository root:

```bash
# In the root repository directory (with virtual environment active):
uvicorn calendar_backend.main:app --host 0.0.0.0 --port 8010 --reload --env-file calendar_backend/.env
# Or using the installed CLI entrypoint:
calendar-backend
```

## MVP day calendar

The app opens directly to the employee day calendar. `npm run dev` uses an
explicit deterministic demo by default, without credentials or a running backend.
The bundled `src/data/calendarDemo.json` is a snapshot of the Python
`workforce_agent.calendar.demo_calendar` service, not browser-generated risk flags.
Date navigation shifts fixture dates only. The backend demo is also available at
`GET /api/calendar/demo?day=2026-10-17`.

The source selector switches to authenticated backend mode, using
`VITE_API_BASE_URL` and `credentials: include` (a backend-issued session cookie).
No provider secrets or Gemini calls belong in the frontend. Deploy the API behind
an authenticated same-origin gateway, or configure explicit CORS origins and secure
cookie settings at the backend. Enterprise authentication, live-provider calendar loading, Gemini chat,
and calendar writes are not implemented. The panel now supports isolated backend
demo sessions, deterministic chat and validated proposals; see
[the agent contract](../docs/CLIMATE_AGENT.md).

### Live calendar contract

`GET /api/calendar/day?site_id=VAD-PLANT-01&date=YYYY-MM-DD` must return the same
shape as `src/data/calendarDemo.json`. The Python API now implements this typed, authenticated endpoint with an explicit
fixture source (`mode: fixture`), baseline event versions and stable source IDs.
No live provider is connected. See [the day API contract](../docs/DAY_SCHEDULE_API.md).
A backend demo login or provisioned bearer identity with read/site grants is required.

- `site.timezone`: IANA timezone; all start/end fields are offset-bearing ISO timestamps.
- `window`: visible start/end timestamps; geometry is proportional to elapsed time.
- `employees`: stable IDs, operational names and roles.
- `activities`: stable IDs, employee ID, title, timestamps, kind
  (`indoor`, `outdoor`, `unknown`), location, backend-calculated status
  (`affected`, `needs-review`, `unflagged`), reason and warning IDs.
- `warnings`: ID, severity, title, timestamps, measure and configured policy context.
- `suggestions`: activity ID, proposed timestamps (or null for no feasible slot),
  validation status and rationale. Backend validation must include policy and availability.
- `weather`: source, freshness status and updated-at timestamp.
- `integrations`: truthful agent, MCP and calendar status labels.

The browser renders server decisions; `unflagged` is never labeled safe. The live
service must return needs-review for unknown type/location, missing policy or
stale/incomplete weather. It must calculate all strict interval overlaps
(`activity.start < warning.end && activity.end > warning.start`).
Review/approve/reject/revision controls now call backend decisions for the isolated
demo calendar; see [approval details](../docs/RESCHEDULING_APPROVAL.md). A production approval API must record actor/decision, revalidate policy,
availability and source event version, and apply only explicitly approved changes.
The chat explicitly reports its simulated/unavailable status and does not send
constraints to a model.

Warning derivation now runs in `workforce_agent.calendar.analyze_calendar` on the
backend. It accepts normalized `WeatherForecast`, `SafetyPolicy`, activities with
site IDs, and an explicit evaluation time. It creates and merges hourly heat,
wind, precipitation and prohibited-weather intervals, matches all overlapping
outdoor activities at the forecast site, and reports unique affected counts.
Missing policy, unsupported free-form policy rules, missing metrics, uncovered
hours, stale forecasts and unknown activity classifications require review.
Known overlaps remain discoverable even when freshness prevents clearance.
The bundled demo snapshot is generated through this same service.


### Backend supervisor chat

Docker enables isolated demo identities. Click **Start isolated demo session** in
the panel, ask **who is affected**, then try **reschedule before 12:00**. Use the
earliest/latest time fields to revise constraints. The panel shows exact warning
and policy evidence, validation results, and session expiry. Apply requires review and explicit approval, and updates only the isolated demo calendar.
Local Vite development proxies both `/api` and `/agent` to the unified backend on
port 8010; set
`WORKFORCE_AGENT_DEMO_ENABLED=true WORKFORCE_AGENT_SECURE_COOKIES=false` for a local
HTTP backend. Production identity and GCP components are documented separately.

### Activity location and policy scope

The backend `CalendarActivity` contract carries stable activity ID, offset-aware
start/end, `site_id`, work `location`, `kind` (`indoor`, `outdoor`, `unknown`) and
optional explicit `exposure_type`. Missing/unrecognized classification becomes
unknown; blank, unknown and TBD location/site values become missing. Location
names never imply indoor/outdoor classification.

Policies optionally restrict `applies_to_site_ids` and
`applies_to_work_locations`; empty lists mean no further restriction within the
forecast site. Outdoor activities require an applicable outdoor policy (or a match
for their explicit exposure type). Out-of-scope or missing policy requires review,
not clearance. Indoor events receive no outdoor-weather warning IDs. The UI shows
site, classification, work location, and the backend's warning/policy/review reason.
All fixture thresholds remain explicitly labeled illustrative demo policy.


For the complete repeatable journey, automatic notes, and infeasible-task example,
see [the demo walkthrough](../docs/DEMO_WALKTHROUGH.md).

### Employee day timeline

The schedule uses explicit `Calendar`, `CalendarActivity`, `CalendarWarning` and
`CalendarSuggestion` interfaces in `src/types/calendar.ts`. Both the bundled JSON
fixture and schedule response are validated at the boundary. Rendering never
computes safety flags. Loading, empty schedules and rejected/unavailable responses
have dedicated states; the authenticated day endpoint is fixture-backed; live-provider integration remains unwired.

`src/utils/timeline.ts` derives clipped geometry and tick positions from offset-aware
timestamps. Overlapping events use separate lanes inside their employee's row;
back-to-back events reuse a lane. Row height grows with simultaneous events. Short
cards retain their actual duration, with clipped text available through keyboard
selection/details and the full tooltip. The narrow-screen calendar scrolls within
its panel, supports keyboard scrolling, and keeps employee/role labels sticky.

Run `npm test` for deterministic layout/contract tests (nested/simultaneous events,
exact boundaries, timezone offsets, clipping, short durations and invalid input),
plus `npm run build` and `npm run lint`.

### Warning banner and exhaustive card flags

`ClimateWarningBanner` renders severity, full site-local warning intervals, measures,
policy context and forecast source/update time from the typed calendar response.
Affected counts use all outdoor activity flags/references, independently of the
suggestion list; multiple warnings do not double-count an event in the total.
Every event card uses the same backend-state presentation helper and includes an
icon, text label and accessible name. Indoor activities never receive weather-only
affected styling. Existing warning references remain visible alongside needs-review.

Forecast statuses `stale`, `incomplete`, `unavailable`, `missing`, `unknown` and
`needs-review` have explicit review labels. Unrecognized statuses and missing update
timestamps also require review in the summary; an empty warning list is not presented
as reassuring when forecast data is uncertain. No browser overlap/policy evaluation
is added. `npm test` includes rendered banner checks and activity-state coverage.

### Agent side panel

The panel uses structured fixture/API suggestions, displaying the employee,
activity, original/proposed times, backend validation state, rationale and resolved
source warning (severity, interval, measure and policy). A null time pair shows
infeasible or needs-review text rather than inventing a slot. Empty API responses
clear earlier suggestions. Loading and request failures are explicit and retryable.
No model provider is called by the browser; runtime/session identity is displayed
separately from the unverified MCP connection status.

**View more · all flagged activities** includes every backend-flagged outdoor task
and all needs-review activities, independently of suggestion count or active chat.
Selecting one focuses/highlights its timeline card and opens event details.
**Select event & review** on a suggestion also opens the proposal review. Fixture
previews are explicitly read-only with checks not refreshed; server-reviewed session
proposals still require explicit approval and fresh validation before applying.
Generated rationale and validation labels never constitute safety clearance.


Optional backend Vertex reasoning and its truthful status/model metadata are
documented in [the reasoning service guide](../docs/AGENT_REASONING.md).
The default Docker demo continues to use deterministic reasoning without credentials.
