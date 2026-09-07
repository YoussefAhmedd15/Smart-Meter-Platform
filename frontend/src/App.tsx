import React from 'react';
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ExecutiveDashboard } from './pages/ExecutiveDashboard';
import { TestingCenter } from './pages/TestingCenter';
import { LiveMeter } from './pages/LiveMeter';
import { MeterProfile } from './pages/MeterProfile';
import { FailureIntelligence } from './pages/FailureIntelligence';
import { Analytics } from './pages/Analytics';
import { RegressionCenter } from './pages/RegressionCenter';
import { AIAgent } from './pages/AIAgent';
import { KnowledgeBase } from './pages/KnowledgeBase';
import { TestReports } from './pages/TestReports';
import { SettingsPage } from './pages/SettingsPage';

// The old tab-state ids <-> the new URL paths. Sidebar.tsx is untouched and
// still speaks entirely in these ids (activeTab / setActiveTab(tab: string))
// — this table is the only place that translates between that and routing,
// so Sidebar's props contract, and everything it renders, is unchanged.
const TAB_PATHS: Record<string, string> = {
  dashboard: '/',
  analytics: '/analytics',
  'live-meter': '/live-meter',
  'meter-profile': '/meter-profile',
  testing: '/testing',
  failures: '/failures',
  regression: '/regression',
  'ai-agent': '/ai-agent',
  knowledge: '/knowledge',
  reports: '/reports',
  settings: '/settings',
};
const PATH_TABS: Record<string, string> = Object.fromEntries(
  Object.entries(TAB_PATHS).map(([tab, path]) => [path, tab]),
);

const AppShell: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const activeTab = PATH_TABS[location.pathname] ?? 'dashboard';
  const setActiveTab = (tab: string) => navigate(TAB_PATHS[tab] ?? '/');

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-primary)' }}>
      <Header appMode="hardware" />
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        <main
          key={location.pathname}
          className="page-enter"
          style={{
            flex: 1,
            backgroundColor: 'var(--bg-primary)',
            overflowY: 'auto',
            minWidth: 0,
          }}
        >
          <Routes>
            <Route path="/" element={<ExecutiveDashboard />} />
            <Route path="/testing" element={<TestingCenter />} />
            <Route path="/live-meter" element={<LiveMeter />} />
            <Route path="/meter-profile" element={<MeterProfile />} />
            <Route path="/failures" element={<FailureIntelligence />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/regression" element={<RegressionCenter />} />
            <Route path="/ai-agent" element={<AIAgent />} />
            <Route path="/knowledge" element={<KnowledgeBase />} />
            <Route path="/reports" element={<TestReports />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};
