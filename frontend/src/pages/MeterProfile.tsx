import React from 'react';
import { Cpu, ShieldCheck, Activity, AlertTriangle, FileText, CheckCircle2 } from 'lucide-react';

export const MeterProfile: React.FC = () => {
  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>Digital Meter Profile</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Unified hardware identity, testing history, quality score, and firmware intelligence.</p>
      </div>

      {/* Identity Card */}
      <div className="glass-card" style={{ padding: '24px', display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px', alignItems: 'center' }}>
        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(17,23,38,0.8)', border: '1px solid var(--border-cyan)', textAlign: 'center' }}>
          <Cpu size={48} color="var(--accent-cyan)" style={{ marginBottom: '12px' }} />
          <h3 className="mono" style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>ISK-2026-984210</h3>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>Iskraemeco AM550-TD1</div>
          <div className="badge badge-pass" style={{ marginTop: '12px' }}>
            <div className="dot dot-green pulse-green" /> ONLINE & CERTIFIED
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>MANUFACTURER</span>
            <div style={{ fontSize: '1.1rem', fontWeight: 600, marginTop: '2px' }}>Iskraemeco d.d.</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>INSTALLED FIRMWARE</span>
            <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--accent-cyan)', marginTop: '2px' }}>v3.14.2 (Mode E 7E1)</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>HARDWARE REVISION</span>
            <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 600, marginTop: '2px' }}>HW-2.1 (3-Phase)</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>MEDIA INTERFACE</span>
            <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--accent-green)', marginTop: '2px' }}>HDLC_WITH_MODE_E (COM6)</div>
          </div>
        </div>
      </div>

      {/* Profile Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>QUALITY SCORE</div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-cyan)', marginTop: '4px' }}>98.2 <span style={{ fontSize: '1rem', color: 'var(--text-dim)' }}>/ 100</span></div>
          <div style={{ fontSize: '0.75rem', color: 'var(--accent-green)', marginTop: '4px' }}>Class A Metrology Compliance</div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>TOTAL TEST RUNS</div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#f1f5f9', marginTop: '4px' }}>148</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>1,840 COSEM Objects Read</div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>HISTORICAL PASS RATE</div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-green)', marginTop: '4px' }}>97.8%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>4 failures resolved</div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>LAST TEST RUN</div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent-cyan)', marginTop: '8px' }}>Passed (4.12s)</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>2026-08-25 12:30 UTC</div>
        </div>
      </div>
    </div>
  );
};
