import React from 'react';
import type { BackendHealth } from '../types';

export interface ApiStatusCardProps {
  health: BackendHealth;
  onRefresh: () => void;
}

export const ApiStatusCard: React.FC<ApiStatusCardProps> = ({
  health,
  onRefresh,
}) => {
  return (
    <div className="card api-connection-box" id="api-status-card">
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <span style={{ color: 'var(--cyan-400)' }}>🔌</span>
            Python Backend API Connection
          </h3>
          <p className="card-subtitle">
            Configure via <code style={{ color: 'var(--emerald-400)' }}>VITE_API_BASE_URL</code> in <code style={{ color: 'var(--text-light)' }}>frontend/.env</code>
          </p>
        </div>

        <button
          type="button"
          className="btn btn-secondary"
          id="test-connection-btn"
          onClick={onRefresh}
          disabled={health.status === 'checking'}
        >
          {health.status === 'checking' ? 'Probing...' : 'Test Connection'}
        </button>
      </div>

      <div className="api-endpoint-display">
        <div>
          <span style={{ color: 'var(--text-muted)', marginRight: '0.5rem' }}>BASE URL:</span>
          <strong>{health.url}</strong>
        </div>
        <span
          className={`badge badge-${
            health.status === 'connected'
              ? 'emerald'
              : health.status === 'checking'
                ? 'amber'
                : 'rose'
          }`}
        >
          {health.status.toUpperCase()}
        </span>
      </div>

      <div className={`status-callout ${health.status}`}>
        <div style={{ fontSize: '1.2rem', lineHeight: 1 }}>
          {health.status === 'connected' ? '✅' : health.status === 'checking' ? '⏳' : 'ℹ️'}
        </div>
        <div style={{ flex: 1 }}>
          <strong style={{ display: 'block', marginBottom: '0.2rem' }}>
            {health.status === 'connected'
              ? `Backend Connected (${health.latencyMs ?? 0} ms)`
              : health.status === 'checking'
                ? 'Connecting to backend...'
                : 'Python Backend Offline (Independent Mode)'}
          </strong>
          <span>{health.message || 'No health report available.'}</span>
          {health.timestamp && (
            <div style={{ marginTop: '0.35rem', fontSize: '0.75rem', opacity: 0.8 }}>
              Last probe: {new Date(health.timestamp).toLocaleTimeString()}
            </div>
          )}
        </div>
      </div>

      <div style={{ marginTop: '1rem' }}>
        <h4 style={{ fontSize: '0.85rem', color: 'var(--text-light)', marginBottom: '0.5rem' }}>
          How this Frontend communicates with Python:
        </h4>
        <p style={{ fontSize: '0.8rem', lineHeight: 1.6, color: 'var(--text-secondary)' }}>
          The React UI is designed to run independently or pair with a future Python HTTP service
          (such as FastAPI). All data models are strictly synchronized with Pydantic schemas in{' '}
          <code>src/workforce_agent/schemas/</code>. When the HTTP server is running, the frontend API
          service will automatically route queries for weather forecasts, worker availability, and schedule
          proposals to the configured endpoint.
        </p>
      </div>
    </div>
  );
};
