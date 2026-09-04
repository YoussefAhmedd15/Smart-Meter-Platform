import React, { useEffect, useState } from 'react';
import { Zap, Activity, Clock, Wifi, WifiOff, Bell } from 'lucide-react';
import { apiService } from '../services/api';

interface HeaderProps {
  appMode?: string;
}

export const Header: React.FC<HeaderProps> = ({ appMode: initialAppMode = 'hardware' }) => {
  const [currentMode, setCurrentMode] = useState<string>(initialAppMode);
  const [currentTime, setCurrentTime]  = useState<string>('');
  const [currentDate, setCurrentDate]  = useState<string>('');
  const [connected, setConnected]      = useState<boolean>(true);

  /* Fetch real app-mode from health endpoint */
  useEffect(() => {
    apiService.getHealth()
      .then(res => {
        if (res?.app_mode) setCurrentMode(res.app_mode.toLowerCase());
        setConnected(true);
      })
      .catch(() => {
        setCurrentMode(initialAppMode);
        setConnected(false);
      });
  }, [initialAppMode]);

  /* Live clock */
  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString('en-GB', { hour12: false }));
      setCurrentDate(now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }));
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  const isHardware = currentMode === 'hardware';

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        background: 'rgba(7, 11, 20, 0.92)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderBottom: '1px solid var(--border-color)',
        padding: '0 28px',
        height: '68px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 4px 24px rgba(0,0,0,0.4)',
      }}
    >
      {/* ── Left: Logo + Title ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '40px', height: '40px', borderRadius: '10px',
          background: 'linear-gradient(135deg, #00f2fe 0%, #4facfe 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 0 18px rgba(0,242,254,0.45)',
          flexShrink: 0,
        }}>
          <Zap size={22} color="#070b14" strokeWidth={2.5} />
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{
              fontSize: '1.15rem', fontWeight: 800,
              fontFamily: 'var(--font-head)',
              color: 'var(--text-main)', margin: 0,
              letterSpacing: '-0.02em',
            }}>
              Smart Meter Intelligence Platform
            </h1>
            <span style={{
              fontSize: '0.65rem', padding: '2px 8px', borderRadius: '12px',
              background: 'rgba(0,242,254,0.12)', color: 'var(--accent-cyan)',
              border: '1px solid var(--border-cyan)', fontWeight: 700,
              letterSpacing: '0.06em',
            }}>
              v1.0 · PROD
            </span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', margin: 0 }}>
            Iskraemeco DLMS/COSEM Test Automation &amp; Failure Intelligence
          </p>
        </div>
      </div>

      {/* ── Right: Status Indicators ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>

        {/* Live Clock */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          padding: '7px 14px', borderRadius: 'var(--radius-xl)',
          background: 'rgba(13,20,36,0.8)', border: '1px solid var(--border-subtle)',
        }}>
          <Clock size={14} color="var(--text-dim)" />
          <span className="mono" style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{currentDate}</span>
          <span className="mono" style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-main)' }}>{currentTime}</span>
        </div>

        {/* Backend Connection */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '7px',
          padding: '7px 13px', borderRadius: 'var(--radius-xl)',
          background: connected ? 'rgba(0,230,118,0.08)' : 'rgba(255,23,68,0.08)',
          border: connected ? '1px solid var(--border-green)' : '1px solid var(--border-red)',
        }}>
          {connected
            ? <Wifi size={14} color="var(--accent-green)" />
            : <WifiOff size={14} color="var(--accent-red)" />
          }
          <span style={{
            fontSize: '0.75rem', fontWeight: 600,
            color: connected ? 'var(--accent-green)' : 'var(--accent-red)',
          }}>
            {connected ? 'API CONNECTED' : 'API OFFLINE'}
          </span>
        </div>

        {/* Media Interface pill */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '7px',
          padding: '7px 13px', borderRadius: 'var(--radius-xl)',
          background: 'rgba(13,20,36,0.8)', border: '1px solid var(--border-color)',
        }}>
          <Activity size={14} color="var(--accent-cyan)" />
          <span className="mono" style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>
            COM6 · 300 7E1
          </span>
        </div>

        {/* App Mode */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '7px',
          padding: '7px 13px', borderRadius: 'var(--radius-xl)',
          background: isHardware ? 'rgba(0,230,118,0.10)' : 'rgba(255,171,0,0.10)',
          border: isHardware ? '1px solid var(--border-green)' : '1px solid var(--border-amber)',
        }}>
          <div className={`dot ${isHardware ? 'dot-green pulse-green' : 'dot-amber'}`} />
          <span style={{
            fontSize: '0.75rem', fontWeight: 700,
            color: isHardware ? 'var(--accent-green)' : 'var(--accent-amber)',
            letterSpacing: '0.04em',
          }}>
            {isHardware ? 'HARDWARE' : 'DEMO MODE'}
          </span>
        </div>

        {/* Notification bell */}
        <button
          className="btn-ghost"
          style={{ padding: '8px', borderRadius: 'var(--radius-md)', position: 'relative' }}
          title="Notifications"
        >
          <Bell size={18} color="var(--text-muted)" />
          <span style={{
            position: 'absolute', top: '4px', right: '4px',
            width: '8px', height: '8px', borderRadius: '50%',
            background: 'var(--accent-red)',
            border: '2px solid var(--bg-primary)',
          }} />
        </button>
      </div>
    </header>
  );
};
