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

By default, `VITE_API_BASE_URL` is set to `http://localhost:8000`. You can change this to point to your Python backend server.

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
- `npm run lint`: Runs code analysis via `oxlint`.

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
uvicorn workforce_agent.api:app --host 0.0.0.0 --port 8000 --reload
# Or using the installed CLI entrypoint:
workforce-api
```
