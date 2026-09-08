import React from 'react';
import {
  LayoutDashboard, PlaySquare, Activity, UserCheck,
  ShieldAlert, BarChart3, GitCompare, Bot, BookOpen,
  FileText, Settings, ChevronRight, ClipboardList,
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  badge?: string;
  badgeColor?: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const navSections: NavSection[] = [
  {
    title: 'Overview',
    items: [
      { id: 'dashboard',    label: 'Executive Dashboard', icon: LayoutDashboard },
      { id: 'analytics',   label: 'Analytics',           icon: BarChart3 },
    ],
  },
  {
    title: 'Meter Operations',
    items: [
      { id: 'live-meter',    label: 'Live Meter',     icon: Activity, badge: 'LIVE', badgeColor: 'var(--accent-green)' },
      { id: 'meter-profile', label: 'Meter Profile',  icon: UserCheck },
    ],
  },
  {
    title: 'Testing & Quality',
    items: [
      { id: 'testing',           label: 'Testing Center',        icon: PlaySquare },
      { id: 'test-case-manager', label: 'Test Case Manager',     icon: ClipboardList, badge: 'ADO', badgeColor: 'var(--accent-purple)' },
      { id: 'failures',          label: 'Failure Intelligence',  icon: ShieldAlert },
      { id: 'regression',        label: 'Regression Center',     icon: GitCompare },
    ],
  },
  {
    title: 'Intelligence',
    items: [
      { id: 'ai-agent',  label: 'AI Agent',       icon: Bot, badge: 'AI', badgeColor: 'var(--accent-purple)' },
      { id: 'knowledge', label: 'Knowledge Base', icon: BookOpen },
    ],
  },
  {
    title: 'Reports & Config',
    items: [
      { id: 'reports',  label: 'Test Reports', icon: FileText },
      { id: 'settings', label: 'Settings',     icon: Settings },
    ],
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  return (
    <aside
      style={{
        width: '252px',
        minHeight: 'calc(100vh - 68px)',
        background: 'rgba(7, 11, 20, 0.7)',
        backdropFilter: 'blur(16px)',
        borderRight: '1px solid var(--border-color)',
        padding: '16px 10px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '0',
        overflowY: 'auto',
        flexShrink: 0,
      }}
    >
      {navSections.map((section, si) => (
        <div key={si} style={{ marginBottom: '4px' }}>
          {/* Section label */}
          <div style={{
            padding: '10px 14px 6px',
            fontSize: '0.65rem',
            fontWeight: 700,
            color: 'var(--text-dim)',
            textTransform: 'uppercase',
            letterSpacing: '0.09em',
            marginTop: si === 0 ? 0 : '6px',
          }}>
            {section.title}
          </div>

          {/* Items */}
          {section.items.map(item => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '9px 12px',
                  borderRadius: '8px',
                  border: 'none',
                  background: isActive
                    ? 'linear-gradient(90deg, rgba(0,242,254,0.14) 0%, rgba(79,172,254,0.04) 100%)'
                    : 'transparent',
                  color: isActive ? 'var(--accent-cyan)' : 'var(--text-muted)',
                  borderLeft: isActive ? '2px solid var(--accent-cyan)' : '2px solid transparent',
                  fontWeight: isActive ? 600 : 400,
                  fontSize: '0.86rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease',
                  marginBottom: '2px',
                  position: 'relative',
                }}
                onMouseEnter={e => {
                  if (!isActive) {
                    (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.04)';
                    (e.currentTarget as HTMLElement).style.color = 'var(--text-main)';
                  }
                }}
                onMouseLeave={e => {
                  if (!isActive) {
                    (e.currentTarget as HTMLElement).style.background = 'transparent';
                    (e.currentTarget as HTMLElement).style.color = 'var(--text-muted)';
                  }
                }}
              >
                <Icon
                  size={17}
                  color={isActive ? 'var(--accent-cyan)' : 'currentColor'}
                  strokeWidth={isActive ? 2.2 : 1.8}
                />
                <span style={{ flex: 1 }}>{item.label}</span>

                {/* Badge */}
                {item.badge && (
                  <span style={{
                    fontSize: '0.58rem',
                    fontWeight: 800,
                    padding: '1px 6px',
                    borderRadius: '99px',
                    background: `${item.badgeColor}22`,
                    color: item.badgeColor,
                    border: `1px solid ${item.badgeColor}44`,
                    letterSpacing: '0.05em',
                  }}>
                    {item.badge}
                  </span>
                )}

                {/* Active arrow */}
                {isActive && (
                  <ChevronRight size={14} color="var(--accent-cyan)" style={{ flexShrink: 0 }} />
                )}
              </button>
            );
          })}
        </div>
      ))}

      {/* Bottom version */}
      <div style={{
        marginTop: 'auto',
        paddingTop: '16px',
        borderTop: '1px solid var(--border-subtle)',
        padding: '16px 14px 0',
        fontSize: '0.7rem',
        color: 'var(--text-dim)',
        lineHeight: '1.6',
      }}>
        <div style={{ fontWeight: 600 }}>Smart Meter Platform</div>
        <div>DLMS/COSEM · Gurux Integration</div>
        <div style={{ color: 'var(--accent-cyan)', marginTop: '2px' }}>v1.0.0-PROD</div>
      </div>
    </aside>
  );
};
