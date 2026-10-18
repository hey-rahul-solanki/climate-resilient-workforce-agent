import React from 'react';
import type { BackendHealth } from '../types';
import { ApiStatusCard } from '../components/ApiStatusCard';

export interface ApiPageProps {
  health: BackendHealth;
  onRefreshHealth: () => void;
}

export const ApiPage: React.FC<ApiPageProps> = ({
  health,
  onRefreshHealth,
}) => {
  const endpoints = [
    {
      method: 'GET',
      path: '/health',
      description: 'Liveness & health check reporting API version and status.',
      response: '{ "status": "ok", "version": "0.1.0" }',
    },
    {
      method: 'GET',
      path: '/api/sites',
      description: 'List all industrial sites configured in location catalogs.',
      response: 'Site[] (e.g., Vadodara Process Plant, Substation 02)',
    },
    {
      method: 'GET',
      path: '/api/weather/{site_id}?forecast_days=3',
      description: 'Fetch normalized WeatherForecast with hourly WBGT and heat metrics.',
      response: 'WeatherForecast (hourly conditions, quality, staleness flag)',
    },
    {
      method: 'GET',
      path: '/api/workers',
      description: 'List technician profiles, active certifications, and break requirements.',
      response: 'Worker[] (skills, availability, shift constraints)',
    },
    {
      method: 'POST',
      path: '/api/schedules/proposals',
      description: 'Generate climate-resilient schedule assignments for open work orders.',
      response: 'ScheduleProposal (assignments with cooling breaks, unscheduled orders)',
    },
  ];

  return (
    <div id="api-integration-page">
      <div style={{ marginBottom: '1.75rem' }}>
        <h1 style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>
          Backend API Architecture & Service Contracts
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          The frontend client communicates via a typed API service module located at{' '}
          <code>frontend/src/services/api.ts</code>. You can run the React frontend independently, or
          point it at any running Python API server.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.8fr', gap: '1.5rem', marginBottom: '2rem' }}>
        <div>
          <ApiStatusCard health={health} onRefresh={onRefreshHealth} />

          <div className="card" style={{ marginTop: '1.5rem' }}>
            <h3 className="card-title" style={{ fontSize: '1rem', marginBottom: '0.75rem' }}>
              <span>⚙️</span> Environment Configuration
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
              Create or edit <code>frontend/.env</code> to point to your backend:
            </p>
            <pre className="code-block">
              <code>{`# frontend/.env
VITE_API_BASE_URL=http://localhost:8010`}</code>
            </pre>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
              Vite automatically injects variables prefixed with <code>VITE_</code> at build and dev time.
            </p>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              <span>📡</span> Target REST Service Endpoints
            </h2>
          </div>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            When wrapping <code>workforce_agent</code> with a Python web framework (e.g. FastAPI, Starlette, or Flask),
            implement the following contract:
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {endpoints.map((ep) => (
              <div
                key={ep.path}
                style={{
                  background: 'rgba(15, 23, 42, 0.7)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.85rem 1rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.35rem' }}>
                  <span
                    className={`badge badge-${ep.method === 'GET' ? 'cyan' : 'emerald'}`}
                    style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}
                  >
                    {ep.method}
                  </span>
                  <code style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>{ep.path}</code>
                </div>
                <div style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                  {ep.description}
                </div>
                <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>
                  Returns: <code>{ep.response}</code>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
