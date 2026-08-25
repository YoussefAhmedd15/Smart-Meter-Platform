import React from 'react';
import {
  LayoutDashboard, PlaySquare, Activity, ShieldAlert, BarChart3,
  GitCompare, Bot, BookOpen, FileText, Settings, UserCheck
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Executive Dashboard', icon: LayoutDashboard },
    { id: 'testing', label: 'Testing Center', icon: PlaySquare },
    { id: 'live-meter', label: 'Live Meter', icon: Activity },
    { id: 'meter-profile', label: 'Meter Profile', icon: UserCheck },
    { id: 'failures', label: 'Failure Intelligence', icon: ShieldAlert },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'regression', label: 'Regression Center', icon: GitCompare },
    { id: 'ai-agent', label: 'AI Agent', icon: Bot },
    { id: 'knowledge', label: 'Knowledge Base', icon: BookOpen },
    { id: 'reports', label: 'Test Reports', icon: FileText },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="glass-card" style={{ width: '260px', minHeight: 'calc(100vh - 74px)', borderRadius: 0, borderTop: 0, borderBottom: 0, borderLeft: 0, padding: '20px 12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
      <div style={{ padding: '8px 12px 14px 12px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Navigation Menu
      </div>
      {menuItems.map((item) => {
        const Icon = item.icon;
        const isActive = activeTab === item.id;
        return (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '11px 16px',
              borderRadius: '8px',
              border: 'none',
              background: isActive ? 'linear-gradient(90deg, rgba(0,242,254,0.15) 0%, rgba(79,172,254,0.05) 100%)' : 'transparent',
              color: isActive ? 'var(--accent-cyan)' : 'var(--text-muted)',
              borderLeft: isActive ? '3px solid var(--accent-cyan)' : '3px solid transparent',
              fontWeight: isActive ? 600 : 400,
              fontSize: '0.9rem',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.15s ease-in-out',
            }}
          >
            <Icon size={18} color={isActive ? 'var(--accent-cyan)' : 'var(--text-muted)'} />
            <span>{item.label}</span>
          </button>
        );
      })}
    </aside>
  );
};
