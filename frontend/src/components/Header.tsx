import React from 'react';
import type { BackendHealth } from '../types';

export interface HeaderProps {
  health: BackendHealth;
  onCheckHealth: () => void;
  onOpenApiTab: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  onCheckHealth,
  onOpenApiTab,
}) => {
  return (
    <header className="app-header" id="app-header">
      <div className="header-inner">
        <div className="header-brand">
          <div className="brand-icon-wrapper" aria-hidden="true">
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="m9 12 2 2 4-4" />
            </svg>
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span className="brand-title">Climate Resilience Agent</span>
              <span className="brand-badge">UI v0.1.0</span>
            </div>
            <p className="header-subtitle">
              Intelligent Workforce Scheduling & Weather Safety Platform
            </p>
          </div>
        </div>

        <div className="header-actions">
          <button
            type="button"
            className="status-pill"
            id="backend-status-pill"
            onClick={onOpenApiTab}
            title={`Backend: ${health.url} (${health.message || health.status}). Click to inspect API.`}
          >
            <span className={`status-dot ${health.status}`} />
            <span>
              {health.status === 'connected'
                ? `Connected (${health.latencyMs ?? 0}ms)`
                : health.status === 'checking'
                  ? 'Checking Backend...'
                  : 'Backend Offline'}
            </span>
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            id="refresh-health-btn"
            style={{ padding: '0.4rem 0.75rem', fontSize: '0.75rem' }}
            onClick={onCheckHealth}
            disabled={health.status === 'checking'}
            title="Ping backend API to verify connectivity"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{
                animation: health.status === 'checking' ? 'spin 1s linear infinite' : 'none',
              }}
            >
              <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
            </svg>
            <span>Ping</span>
          </button>
        </div>
      </div>
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </header>
  );
};
