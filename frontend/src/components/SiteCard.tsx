import React from 'react';
import type { Site, SiteHazard } from '../types';
import { StatusBadge } from './StatusBadge';

export interface SiteCardProps {
  site: Site;
  isSelected?: boolean;
  onSelect?: () => void;
}

const hazardColorMap: Record<
  SiteHazard,
  'rose' | 'amber' | 'cyan' | 'indigo' | 'emerald' | 'muted'
> = {
  extreme_heat: 'rose',
  monsoon: 'cyan',
  high_wind: 'cyan',
  lightning: 'amber',
  height: 'amber',
  confined_space: 'rose',
  electrical: 'amber',
  chemical: 'rose',
};

export const SiteCard: React.FC<SiteCardProps> = ({
  site,
  isSelected,
  onSelect,
}) => {
  return (
    <div
      className="site-item"
      style={{
        borderColor: isSelected ? 'var(--emerald-400)' : undefined,
        cursor: onSelect ? 'pointer' : 'default',
      }}
      onClick={onSelect}
    >
      <div className="site-item-header">
        <span className="site-name">{site.name}</span>
        <span className="site-id-badge">{site.site_id}</span>
      </div>

      <div className="site-meta">
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Coordinates: </span>
          <span>
            {site.latitude.toFixed(4)}°N, {site.longitude.toFixed(4)}°E
          </span>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Timezone: </span>
          <span>{site.timezone}</span>
        </div>
        <div>
          <span style={{ color: 'var(--text-muted)' }}>Operating Days: </span>
          <span>{site.operating_hours.length} / week</span>
        </div>
      </div>

      <div>
        <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
          MONITORED CLIMATE & OPERATIONAL HAZARDS:
        </div>
        <div className="hazard-tags">
          {site.hazards.map((hazard) => (
            <StatusBadge
              key={hazard}
              label={hazard.replace(/_/g, ' ').toUpperCase()}
              variant={hazardColorMap[hazard] || 'muted'}
            />
          ))}
        </div>
      </div>
    </div>
  );
};
