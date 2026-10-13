import React from 'react';
import type { BackendHealth } from '../types';
import { Header } from './Header';
import { Navigation, type NavigationTab } from './Navigation';

export interface LayoutProps {
  children: React.ReactNode;
  activeTab: NavigationTab;
  onTabChange: (tab: NavigationTab) => void;
  health: BackendHealth;
  onCheckHealth: () => void;
}

export const Layout: React.FC<LayoutProps> = ({
  children,
  activeTab,
  onTabChange,
  health,
  onCheckHealth,
}) => {
  return (
    <div className="app-container">
      <Header
        health={health}
        onCheckHealth={onCheckHealth}
        onOpenApiTab={() => onTabChange('api')}
      />
      <Navigation activeTab={activeTab} onTabChange={onTabChange} />

      <main className="main-content" id="main-content">
        {children}
      </main>

      <footer className="app-footer">
        <div className="footer-inner">
          <div>
            <strong>Climate-Resilient Workforce Agent</strong> &bull; Industrial Field Maintenance Safety & Scheduling
          </div>
          <div>
            <span>Vite + React + TypeScript Frontend</span> &bull; <span>Python Pydantic Schemas</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
