import React from 'react';
import { StatusBadge } from '../components/StatusBadge';

export const SchedulePlanningPage: React.FC = () => {
  const policies = [
    {
      level: 'Moderate Heat',
      condition: 'Wet Bulb 28°C - 30°C',
      action: '15 min cooling break per 45 min work',
      severity: 'warning',
    },
    {
      level: 'High Heat Alert',
      condition: 'Wet Bulb 30°C - 32°C',
      action: '30 min cooling break per 30 min work, hydration monitoring',
      severity: 'high',
    },
    {
      level: 'Critical Heat Stop',
      condition: 'Wet Bulb > 32°C or Heat Index > 46°C',
      action: 'Halt outdoor heavy physical tasks; reschedule to morning/evening windows',
      severity: 'critical',
    },
    {
      level: 'High Wind / Storm',
      condition: 'Wind > 45 km/h or Lightning Detected',
      action: 'Immediate cessation of height and crane operations',
      severity: 'critical',
    },
  ];

  return (
    <div id="safety-page">
      <div style={{ marginBottom: '1.75rem' }}>
        <h1 style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>
          Safety Policies & Automated Schedule Proposals
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          The workforce planning agent pairs validated worker qualifications, shift limits, and break
          rules with dynamic environmental forecasts to generate safe, compliant schedule proposals.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '1.5rem' }}>
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              <span>🛡️</span> Physiological Work-Rest Decision Matrix
            </h2>
            <StatusBadge label="ISO 7243 & OSHA Compliant" variant="emerald" />
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Risk Tier</th>
                  <th>Environmental Trigger</th>
                  <th>Automated Policy Action</th>
                </tr>
              </thead>
              <tbody>
                {policies.map((p) => (
                  <tr key={p.level}>
                    <td>
                      <StatusBadge
                        label={p.level}
                        variant={p.severity === 'critical' ? 'rose' : p.severity === 'high' ? 'amber' : 'cyan'}
                      />
                    </td>
                    <td><code>{p.condition}</code></td>
                    <td style={{ fontSize: '0.825rem' }}>{p.action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <h3 className="card-title" style={{ marginBottom: '0.75rem' }}>
            <span>📋</span> Data Contract Integration
          </h3>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '1rem' }}>
            Work orders define exposure types (<code>outdoor_heat</code>, <code>height</code>, <code>confined_space</code>).
            The Python agent evaluates workers’ <code>break_requirements</code> and certifies eligible shifts.
          </p>

          <div style={{ background: '#050811', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
              SCHEDULE PROPOSAL LIFECYCLE:
            </div>
            <ol style={{ paddingLeft: '1.25rem', fontSize: '0.8rem', color: 'var(--text-light)', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <li>Read Site & Work Order operational windows</li>
              <li>Ingest hourly meteorological forecast</li>
              <li>Filter unavailable intervals matching HeatThreshold limits</li>
              <li>Insert required CoolingBreaks into ScheduleAssignments</li>
              <li>Flag unscheduled work orders with actionable explanations</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
};
