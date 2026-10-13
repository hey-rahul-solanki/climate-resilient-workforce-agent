import React from 'react';
import { StatusBadge } from '../components/StatusBadge';

export const WeatherViewPage: React.FC = () => {
  const metrics = [
    {
      name: 'Wet Bulb Temperature (°C)',
      code: 'wet_bulb_temperature_c',
      role: 'Physiological heat stress indicator measuring cooling capacity via sweat evaporation.',
      riskThreshold: '≥ 29°C (Caution), ≥ 31°C (Dangerous), ≥ 35°C (Lethal limit)',
    },
    {
      name: 'Heat Index (°C)',
      code: 'heat_index_c',
      role: 'Combined perception of relative humidity and ambient dry bulb temperature.',
      riskThreshold: '≥ 38°C (Extreme Caution), ≥ 42°C (Danger)',
    },
    {
      name: 'Ambient Temperature (°C)',
      code: 'temperature_c',
      role: 'Direct dry bulb atmospheric temperature.',
      riskThreshold: 'Evaluated alongside solar flux and humidity.',
    },
    {
      name: 'Direct Normal Irradiance (W/m²)',
      code: 'direct_normal_irradiance_wm2',
      role: 'Solar radiant heat load on unshaded field workers.',
      riskThreshold: 'High solar flux lowers allowable work windows.',
    },
    {
      name: 'Precipitation & Wind',
      code: 'precipitation_mm, wind_speed_kmh',
      role: 'Storm, monsoon, and high-wind flags for elevated work (e.g. height, electrical).',
      riskThreshold: 'Wind ≥ 40 km/h halts elevated tasks.',
    },
  ];

  return (
    <div id="weather-page">
      <div style={{ marginBottom: '1.75rem' }}>
        <h1 style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>
          Weather Intelligence & Ingestion Contract
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          The weather client ingests conditions from Open-Meteo into the provider-neutral{' '}
          <code>WeatherForecast</code> Pydantic schema. Missing values are preserved as{' '}
          <code>null</code> and never assumed to be safe.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              <span>🌦️</span> Monitored Meteorological Metrics
            </h2>
            <StatusBadge label="Provider-Neutral" variant="cyan" />
          </div>

          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Metric Name</th>
                  <th>Schema Property</th>
                  <th>Operational Significance</th>
                  <th>Safety Threshold</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((m) => (
                  <tr key={m.code}>
                    <td><strong>{m.name}</strong></td>
                    <td><code>{m.code}</code></td>
                    <td style={{ fontSize: '0.8rem' }}>{m.role}</td>
                    <td><span style={{ color: 'var(--amber-400)', fontSize: '0.75rem' }}>{m.riskThreshold}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <h3 className="card-title" style={{ marginBottom: '0.75rem' }}>
            <span>🔒</span> Data Integrity Principles
          </h3>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <li style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              <strong style={{ color: 'var(--emerald-400)', display: 'block' }}>Zero Silent Defaults:</strong>
              Missing forecast intervals do not default to 20°C. They raise explicit completeness flags.
            </li>
            <li style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              <strong style={{ color: 'var(--amber-400)', display: 'block' }}>Staleness Awareness:</strong>
              Forecasts older than configured freshness thresholds are marked stale, triggering alerts.
            </li>
            <li style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              <strong style={{ color: 'var(--cyan-400)', display: 'block' }}>Fixture Replay:</strong>
              Deterministic offline testing via <code>tests/fixtures/open_meteo_vadodara.json</code>.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};
