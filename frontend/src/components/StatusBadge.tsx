import React from 'react';

export interface StatusBadgeProps {
  label: string;
  variant?: 'emerald' | 'amber' | 'rose' | 'cyan' | 'indigo' | 'muted';
  icon?: React.ReactNode;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  label,
  variant = 'emerald',
  icon,
}) => {
  return (
    <span className={`badge badge-${variant}`}>
      {icon && <span style={{ display: 'inline-flex', fontSize: '0.9em' }}>{icon}</span>}
      <span>{label}</span>
    </span>
  );
};
