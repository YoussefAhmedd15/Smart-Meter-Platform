import React, { useEffect, useState } from 'react';
import { ShieldAlert, Cpu, Sparkles, CheckCircle2, AlertOctagon } from 'lucide-react';
import { apiService } from '../services/api';

export const FailureIntelligence: React.FC = () => {
  const [analysis, setAnalysis] = useState<any>(null);

  useEffect(() => {
    apiService.getSimilarFailures(1).then(setAnalysis).catch(console.error);
  }, []);

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>Failure Intelligence & Similarity Engine</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Automated failure capture, historical similarity matching, root cause analysis, and AI recommendations.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        {/* Current Incident Card */}
        <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid var(--accent-red)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px', color: 'var(--accent-red)' }}>
            <AlertOctagon size={20} />
            <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Active Incident #1042</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>FAILED TEST CASE</span>
              <div style={{ fontSize: '1rem', fontWeight: 600, color: '#fff' }}>Mode E Optical Handshake 300 Baud</div>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ERROR CLASSIFICATION</span>
              <div className="mono" style={{ fontSize: '0.9rem', color: 'var(--accent-red)', fontWeight: 600 }}>TIMEOUT / HDLC_UA_NOT_RECEIVED</div>
            </div>

            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>RAW ERROR MESSAGE</span>
              <div className="mono" style={{ padding: '10px', borderRadius: '6px', background: 'rgba(7,10,18,0.8)', fontSize: '0.8rem', color: '#fca5a5', marginTop: '4px' }}>
                Communication timeout while waiting for UA response frame from optical head on COM6 during Mode E baudrate switch.
              </div>
            </div>

            <div style={{ display: 'flex', gap: '20px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              <span>Meter: <strong style={{ color: '#fff' }}>ISK-2026-984210</strong></span>
              <span>Firmware: <strong style={{ color: 'var(--accent-cyan)' }}>v3.13.0</strong></span>
            </div>
          </div>
        </div>

        {/* AI Analysis Panel */}
        <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid var(--accent-cyan)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px', color: 'var(--accent-cyan)' }}>
            <Sparkles size={20} />
            <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>Grounded AI Root Cause Assistance</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.85rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span className="badge badge-info">SIMILARITY MATCH: 94.2%</span>
              <span className="badge badge-pass">CONFIDENCE: HIGH</span>
            </div>

            <div>
              <strong style={{ color: 'var(--accent-cyan)' }}>IDENTIFIED ROOT CAUSE:</strong>
              <p style={{ color: 'var(--text-muted)', marginTop: '4px' }}>
                Optical probe baudrate switching delay during IEC 62056-21 Mode E protocol negotiation on 300 baud initial setting.
              </p>
            </div>

            <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(0,230,118,0.08)', border: '1px solid rgba(0,230,118,0.2)' }}>
              <strong style={{ color: 'var(--accent-green)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={16} /> RECOMMENDED SOLUTION:
              </strong>
              <p style={{ color: '#d1fae5', marginTop: '4px', fontSize: '0.8rem' }}>
                1. Re-align optical probe head on Iskraemeco meter lens.<br/>
                2. Set serial media parity to EVEN (7E1 mode) and stop bits to 1 in config.<br/>
                3. Update meter firmware to v3.14.2 which increases UA response timeout window.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
