import React from 'react';

export type NavigationTab = 'overview' | 'sites' | 'weather' | 'safety' | 'api';

export interface NavigationProps {
  activeTab: NavigationTab;
  onTabChange: (tab: NavigationTab) => void;
}

export const Navigation: React.FC<NavigationProps> = ({
  activeTab,
  onTabChange,
}) => {
  const tabs: Array<{ id: NavigationTab; label: string; icon: string }> = [
    { id: 'overview', label: 'Overview & Operations', icon: '📊' },
    { id: 'sites', label: 'Sites & Locations', icon: '🏭' },
    { id: 'weather', label: 'Weather Intelligence', icon: '☀️' },
    { id: 'safety', label: 'Safety & Scheduling', icon: '🛡️' },
    { id: 'api', label: 'Backend API & Integration', icon: '🔌' },
  ];

  return (
    <nav className="app-nav" aria-label="Main Navigation">
      <div className="nav-inner">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              id={`nav-tab-${tab.id}`}
              className={`nav-tab ${isActive ? 'active' : ''}`}
              onClick={() => onTabChange(tab.id)}
              aria-current={isActive ? 'page' : undefined}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};
