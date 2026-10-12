import React, { useState } from 'react';
import type { Site } from '../types';
import { SiteCard } from '../components/SiteCard';

export interface SitesPageProps {
  sites: Site[];
}

export const SitesPage: React.FC<SitesPageProps> = ({ sites }) => {
  const [selectedSiteId, setSelectedSiteId] = useState<string>(sites[0]?.site_id || '');
  const selectedSite = sites.find((s) => s.site_id === selectedSiteId) || sites[0];

  return (
    <div id="sites-page">
      <div style={{ marginBottom: '1.75rem' }}>
        <h1 style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>
          Industrial Facilities & Location Catalogs
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Location catalogs are purely data-driven. New geographies and industrial facilities can be added
          as JSON files next to <code>src/workforce_agent/locations/vadodara.json</code> without altering weather client code.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.5fr', gap: '1.5rem' }}>
        {/* Site List */}
        <div>
          <h2 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--text-light)' }}>
            Available Sites ({sites.length})
          </h2>
          <div className="site-list">
            {sites.map((site) => (
              <SiteCard
                key={site.site_id}
                site={site}
                isSelected={site.site_id === selectedSiteId}
                onSelect={() => setSelectedSiteId(site.site_id)}
              />
            ))}
          </div>
        </div>

        {/* Selected Site Details */}
        {selectedSite && (
          <div className="card">
            <div className="card-header">
              <div>
                <h3 className="card-title">
                  <span>📍</span> {selectedSite.name}
                </h3>
                <p className="card-subtitle">
                  Site Identifier: <code>{selectedSite.site_id}</code> &bull; Timezone: <code>{selectedSite.timezone}</code>
                </p>
              </div>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.75rem' }}>
                Operating Hours (Weekly Schedule)
              </h4>
              <div className="table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Day</th>
                      <th>Shift Start</th>
                      <th>Shift End</th>
                      <th>Duration</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedSite.operating_hours.map((hours) => {
                      const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
                      const dayName = dayNames[hours.weekday] || `Day ${hours.weekday}`;
                      return (
                        <tr key={hours.weekday}>
                          <td><strong>{dayName}</strong></td>
                          <td><code>{hours.start_local}</code></td>
                          <td><code>{hours.end_local}</code></td>
                          <td>Active</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                Climate Resilience Configuration
              </h4>
              <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                Workers scheduled at this facility are automatically evaluated against ambient wet-bulb temperatures and heat index metrics.
                Outdoor shifts exceeding safety limits trigger required cooling intervals or rescheduling actions in the proposal engine.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
