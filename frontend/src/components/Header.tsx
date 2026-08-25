import React, { useEffect, useState } from 'react';
import { Zap, Activity } from 'lucide-react';
import { apiService } from '../services/api';

interface HeaderProps {
  appMode?: string;
}

export const Header: React.FC<HeaderProps> = ({ appMode: initialAppMode = 'hardware' }) => {
  const [currentMode, setCurrentMode] = useState<string>(initialAppMode);

  useEffect(() => {
    apiService.getHealth()
      .then(res => {
        if (res?.app_mode) {
          setCurrentMode(res.app_mode.toLowerCase());
        }
      })
      .catch(() => setCurrentMode('hardware'));
  }, []);

  const isHardware = currentMode === 'hardware';

  return (
    <header className="glass-card" style={{ borderRadius: 0, borderTop: 0, borderLeft: 0, borderRight: 0, padding: '16px 28px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', zIndex: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: 'linear-gradient(135deg, #00f2fe, #4facfe)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 15px rgba(0,242,254,0.4)' }}>
          <Zap size={24} color="#090d16" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            Smart Meter Intelligence Platform
            <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: '12px', background: 'rgba(0,242,254,0.15)', color: 'var(--accent-cyan)', border: '1px solid var(--border-cyan)' }}>v1.0-PROD</span>
          </h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>Iskraemeco Smart Meter DLMS/COSEM Test Automation & Failure Intelligence</p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 14px', borderRadius: '20px', background: 'rgba(17, 23, 38, 0.8)', border: '1px solid var(--border-color)' }}>
          <Activity size={16} color="var(--accent-cyan)" />
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Media Interface:</span>
          <span className="mono" style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>SONDA Optical Probe (COM / 300 7E1)</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 14px', borderRadius: '20px', background: isHardware ? 'rgba(0,230,118,0.15)' : 'rgba(255,171,0,0.15)', border: isHardware ? '1px solid rgba(0,230,118,0.3)' : '1px solid rgba(255,171,0,0.3)' }}>
          <div className={`dot ${isHardware ? 'dot-green pulse-green' : ''}`} style={{ backgroundColor: isHardware ? 'var(--accent-green)' : 'var(--accent-amber)' }} />
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: isHardware ? 'var(--accent-green)' : 'var(--accent-amber)', textTransform: 'uppercase' }}>
            {isHardware ? 'HARDWARE MODE (SONDA PROBE)' : 'DEMO / MOCK MODE'}
          </span>
        </div>
      </div>
    </header>
  );
};
