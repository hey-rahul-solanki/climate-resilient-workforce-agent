import React from 'react';
import type { BackendHealth, Site } from '../types';
import { StatCard } from '../components/StatCard';
import { ApiStatusCard } from '../components/ApiStatusCard';
import { SiteCard } from '../components/SiteCard';

export interface DashboardPageProps {
  health: BackendHealth;
  onRefreshHealth: () => void;
  sites: Site[];
  onNavigateToTab: (tab: 'sites' | 'weather' | 'safety' | 'api') => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  health,
  onRefreshHealth,
  sites,
  onNavigateToTab,
}) => {
  const primarySite = sites[0];

  return (
    <div id="dashboard-page">
      {/* Hero Section */}
      <section className="hero-banner" aria-labelledby="hero-title">
        <div className="hero-tag">
          <span>🛡️</span> Climate-Aware Field Operations
        </div>
        <h1 className="hero-title" id="hero-title">
          Autonomous Workforce Scheduling Resilient to Extreme Weather
        </h1>
        <p className="hero-subtitle">
          Protecting industrial maintenance technicians through predictive weather intelligence,
          physiological heat-stress limits (wet bulb & heat index), and automated work-rest scheduling.
        </p>
      </section>

      {/* Metrics Row */}
      <section className="stats-grid" aria-label="System Metrics">
        <StatCard
          label="Demo Geography"
          value="Vadodara, IN"
          caption="Western India Industrial Corridor"
          icon={<span>📍</span>}
          badge={{ text: 'Catalog Loaded', variant: 'emerald' }}
        />
        <StatCard
          label="Industrial Sites"
          value={sites.length}
          caption="Process plant, substation, pipeline"
          icon={<span>🏭</span>}
          badge={{ text: 'Active Profiles', variant: 'cyan' }}
          accentColor="rgba(6, 182, 212, 0.15)"
        />
        <StatCard
          label="Weather Intelligence"
          value="Open-Meteo"
          caption="Hourly heat index, wet bulb, solar flux"
          icon={<span>☀️</span>}
          badge={{ text: 'Provider-Neutral', variant: 'amber' }}
          accentColor="rgba(245, 158, 11, 0.15)"
        />
        <StatCard
          label="Backend API Status"
          value={health.status === 'connected' ? 'Connected' : 'Standalone'}
          caption={health.url}
          icon={<span>🔌</span>}
          badge={{
            text: health.status === 'connected' ? 'Online' : 'Offline',
            variant: health.status === 'connected' ? 'emerald' : 'rose',
          }}
          accentColor="rgba(99, 102, 241, 0.15)"
        />
      </section>

      {/* Main 2-Column Grid */}
      <div className="dashboard-grid">
        {/* Left Column: Industrial Site & Operations */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">
                  <span>🏭</span>
                  Featured Site: {primarySite?.name || 'Vadodara Process Plant'}
                </h2>
                <p className="card-subtitle">
                  Demo plant configured in <code>src/workforce_agent/locations/vadodara.json</code>
                </p>
              </div>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => onNavigateToTab('sites')}
              >
                View All Sites &rarr;
              </button>
            </div>

            {primarySite && <SiteCard site={primarySite} />}

            <div style={{ marginTop: '1.25rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem' }}>
              <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>PRIMARY HAZARDS</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--amber-400)', marginTop: '0.2rem' }}>
                  Extreme Heat (Wet Bulb &gt; 30°C)
                </div>
              </div>
              <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SAFETY POLICY</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--emerald-400)', marginTop: '0.2rem' }}>
                  Mandatory Cooling Breaks
                </div>
              </div>
              <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>TIMEZONE SPEC</div>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--cyan-400)', marginTop: '0.2rem' }}>
                  Asia/Kolkata (IST)
                </div>
              </div>
            </div>
          </div>

          {/* Architecture Overview */}
          <div className="card">
            <h2 className="card-title" style={{ marginBottom: '0.75rem' }}>
              <span>🏗️</span> Architecture: Python Core & React Frontend
            </h2>
            <p style={{ fontSize: '0.875rem', marginBottom: '1rem', lineHeight: 1.6 }}>
              The application follows a decoupled client-server architecture:
            </p>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Layer</th>
                    <th>Technology</th>
                    <th>Role & Responsibility</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Frontend UI</strong></td>
                    <td>React + Vite + TypeScript</td>
                    <td>Interactive dashboard, real-time safety monitoring, and schedule adjustments.</td>
                  </tr>
                  <tr>
                    <td><strong>Domain Core</strong></td>
                    <td>Python 3.11+, Pydantic v2</td>
                    <td>Strictly validated schemas (Worker, Site, WeatherForecast, ScheduleProposal).</td>
                  </tr>
                  <tr>
                    <td><strong>Weather Agent</strong></td>
                    <td>Open-Meteo, HTTPX</td>
                    <td>Hourly weather ingestion, wet-bulb calculations, and staleness validation.</td>
                  </tr>
                  <tr>
                    <td><strong>API Gateway</strong></td>
                    <td>REST / HTTP (Configurable)</td>
                    <td>Bridges the frontend client with the Python workforce planner service.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Connection & Python CLI */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <ApiStatusCard health={health} onRefresh={onRefreshHealth} />

          <div className="card">
            <div className="card-header">
              <div>
                <h3 className="card-title">
                  <span>⚡</span> Python CLI Integration
                </h3>
                <p className="card-subtitle">Local weather ingestion and testing</p>
              </div>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
              Test deterministic weather ingestion for the demo plant using the Python CLI:
            </p>
            <pre className="code-block" style={{ marginBottom: '1rem' }}>
              <code>{`# Deterministic weather fixture run:
export WORKFORCE_WEATHER_SOURCE=fixture
export WORKFORCE_FIXTURE_PATH=tests/fixtures/open_meteo_vadodara.json
workforce-weather --location-id vadodara-gujarat --site-id VAD-PLANT-01

# Live Open-Meteo forecast:
workforce-weather --location-id vadodara-gujarat --site-id VAD-PLANT-01 --forecast-days 3`}</code>
            </pre>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ width: '100%', fontSize: '0.8rem' }}
                onClick={() => onNavigateToTab('weather')}
              >
                Inspect Weather Specs &rarr;
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
