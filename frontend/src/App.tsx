import React, { useState } from 'react';
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

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [pageKey, setPageKey] = useState(0);

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    setPageKey(k => k + 1); // forces re-mount → triggers fade-in animation
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':    return <ExecutiveDashboard />;
      case 'testing':      return <TestingCenter />;
      case 'live-meter':   return <LiveMeter />;
      case 'meter-profile':return <MeterProfile />;
      case 'failures':     return <FailureIntelligence />;
      case 'analytics':    return <Analytics />;
      case 'regression':   return <RegressionCenter />;
      case 'ai-agent':     return <AIAgent />;
      case 'knowledge':    return <KnowledgeBase />;
      case 'reports':      return <TestReports />;
      case 'settings':     return <SettingsPage />;
      default:             return <ExecutiveDashboard />;
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-primary)' }}>
      <Header appMode="hardware" />
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        <Sidebar activeTab={activeTab} setActiveTab={handleTabChange} />
        <main
          key={pageKey}
          className="page-enter"
          style={{
            flex: 1,
            backgroundColor: 'var(--bg-primary)',
            overflowY: 'auto',
            minWidth: 0,
          }}
        >
          {renderContent()}
        </main>
      </div>
    </div>
  );
};
