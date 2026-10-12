import React from 'react';

export interface StatCardProps {
  label: string;
  value: string | number;
  caption?: string;
  icon?: React.ReactNode;
  badge?: {
    text: string;
    variant: 'emerald' | 'amber' | 'rose' | 'cyan' | 'indigo' | 'muted';
  };
  accentColor?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  caption,
  icon,
  badge,
  accentColor = 'rgba(16, 185, 129, 0.15)',
}) => {
  return (
    <div className="stat-card">
      <div className="stat-header">
        <span className="stat-label">{label}</span>
        {icon && (
          <div
            className="stat-icon"
            style={{
              backgroundColor: accentColor,
              color: 'var(--text-primary)',
            }}
          >
            {icon}
          </div>
        )}
      </div>
      <div className="stat-value">{value}</div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '0.4rem' }}>
        {caption && <span className="stat-caption">{caption}</span>}
        {badge && (
          <span className={`badge badge-${badge.variant}`} style={{ fontSize: '0.7rem' }}>
            {badge.text}
          </span>
        )}
      </div>
    </div>
  );
};
