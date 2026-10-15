import React, { useCallback, useEffect, useState } from 'react';
import { Layout } from './components/Layout';
import type { NavigationTab } from './components/Navigation';
import { defaultVadodaraCatalog } from './data/defaultCatalog';
import { ApiPage } from './pages/ApiPage';
import { DashboardPage } from './pages/DashboardPage';
import { SchedulePlanningPage } from './pages/SchedulePlanningPage';
import { SitesPage } from './pages/SitesPage';
import { WeatherViewPage } from './pages/WeatherViewPage';
import { checkBackendHealth, getApiBaseUrl, workforceApi } from './services/api';
import type { BackendHealth, Site } from './types';


export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavigationTab>('overview');
  const [sites, setSites] = useState<Site[]>(defaultVadodaraCatalog.sites);
  const [health, setHealth] = useState<BackendHealth>(() => ({
    status: 'checking',
    url: getApiBaseUrl(),
    timestamp: '',
    message: 'Testing connection to Python backend...',
  }));

  const runHealthCheck = useCallback(async () => {
    setHealth({
      status: 'checking',
      url: getApiBaseUrl(),
      timestamp: new Date().toISOString(),
      message: `Probing backend at ${getApiBaseUrl()}...`,
    });

    const result = await checkBackendHealth();
    setHealth(result);

    if (result.status === 'connected') {
      try {
        const liveSitesRes = await workforceApi.getSites();
        if (liveSitesRes.data && Array.isArray(liveSitesRes.data) && liveSitesRes.data.length > 0) {
          setSites(liveSitesRes.data);
        }
      } catch {
        // Fallback to default catalog
      }
    }
  }, []);

  useEffect(() => {
    let ignore = false;
    async function initCheck() {
      const result = await checkBackendHealth();
      if (!ignore) {
        setHealth(result);
        if (result.status === 'connected') {
          try {
            const liveSitesRes = await workforceApi.getSites();
            if (!ignore && liveSitesRes.data && Array.isArray(liveSitesRes.data) && liveSitesRes.data.length > 0) {
              setSites(liveSitesRes.data);
            }
          } catch {
            // Standalone mode
          }
        }
      }
    }
    void initCheck();
    return () => {
      ignore = true;
    };
  }, []);

  return (
    <Layout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      health={health}
      onCheckHealth={runHealthCheck}
    >
      {activeTab === 'overview' && (
        <DashboardPage
          health={health}
          onRefreshHealth={runHealthCheck}
          sites={sites}
          onNavigateToTab={setActiveTab}
        />
      )}

      {activeTab === 'sites' && <SitesPage sites={sites} />}

      {activeTab === 'weather' && <WeatherViewPage />}

      {activeTab === 'safety' && <SchedulePlanningPage />}

      {activeTab === 'api' && (
        <ApiPage health={health} onRefreshHealth={runHealthCheck} />
      )}
    </Layout>
  );
};

export default App;
