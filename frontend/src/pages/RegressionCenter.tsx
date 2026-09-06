import React, { useState } from 'react';
import { GitCompare, ArrowRight, CheckCircle2, XCircle, TrendingUp } from 'lucide-react';
import { apiService } from '../services/api';
import { RegressionComparison } from '../types';

export const RegressionCenter: React.FC = () => {
  const [fwA, setFwA] = useState('v3.13.0');
  const [fwB, setFwB] = useState('v3.14.2');
  const [comparison, setComparison] = useState<RegressionComparison | null>(null);

  const handleCompare = async () => {
    try {
      const res = await apiService.compareRegression(fwA, fwB);
      setComparison(res);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 className="section-title">Firmware Regression Comparison Center</h2>
        <p className="section-sub">Compare testing pass rates, fixed defects, and new regressions between firmware releases.</p>
      </div>

      {/* Selectors */}
      <div className="glass-card" style={{ padding: '22px', display: 'grid', gridTemplateColumns: '1fr auto 1fr auto', gap: '16px', alignItems: 'end' }}>
        <div>
          <label className="form-label">Baseline Firmware (A)</label>
          <select className="form-select" value={fwA} onChange={e => setFwA(e.target.value)}>
            <option value="v3.12.1">v3.12.1</option>
            <option value="v3.13.0">v3.13.0</option>
          </select>
        </div>

        <ArrowRight size={24} color="var(--accent-cyan)" />

        <div>
          <label className="form-label">Target Firmware (B)</label>
          <select className="form-select" value={fwB} onChange={e => setFwB(e.target.value)}>
            <option value="v3.14.2">v3.14.2</option>
            <option value="v3.15.0-RC1">v3.15.0-RC1</option>
          </select>
        </div>

        <button className="btn-cyan" onClick={handleCompare}>
          <GitCompare size={16} /> Run Regression Comparison
        </button>
      </div>

      {/* Comparison Outcome */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr 1fr', gap: '20px' }}>
        {/* Firmware A */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>BASELINE FIRMWARE A</div>
          <h3 className="mono" style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-muted)', marginTop: '4px' }}>{fwA}</h3>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#f1f5f9', marginTop: '12px' }}>94.2%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>29 failures out of 500 tests</div>
        </div>

        {/* Delta Highlight */}
        <div className="glass-card" style={{ padding: '20px', border: '1px solid var(--border-cyan)', textAlign: 'center' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>REGRESSION SUMMARY OUTCOME</div>
          <div style={{ fontSize: '2.4rem', fontWeight: 800, color: 'var(--accent-green)', marginTop: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <TrendingUp size={28} /> +2.9%
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginTop: '8px' }}>
            <strong>17 Issues Fixed</strong> • <span style={{ color: 'var(--accent-red)' }}>4 New Failures</span>
          </div>
        </div>

        {/* Firmware B */}
        <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid var(--accent-green)' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--accent-green)' }}>TARGET FIRMWARE B</div>
          <h3 className="mono" style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-green)', marginTop: '4px' }}>{fwB}</h3>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-green)', marginTop: '12px' }}>97.1%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>12 failures out of 500 tests</div>
        </div>
      </div>

      {/* Fixed vs New Failures Details */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--accent-green)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircle2 size={18} /> Fixed Defect Test Cases (17)
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {['Mode E 300 Baud Baudrate Switch Timeout', 'HDLC FCS Checksum Error on Block Transfer', 'Load Profile 1 Buffer Memory Leak', 'Clock Synchronization Drift'].map((c, i) => (
              <div key={i} style={{ padding: '10px 12px', borderRadius: '6px', background: 'rgba(0,230,118,0.08)', border: '1px solid rgba(0,230,118,0.2)', fontSize: '0.85rem', color: '#a7f3d0' }}>
                ✓ {c}
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--accent-red)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <XCircle size={18} /> New Regression Failures (4)
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {['Clock Drift under 60Hz Electrical Noise', 'High Auth Dedicated Key Handshake Timeout'].map((c, i) => (
              <div key={i} style={{ padding: '10px 12px', borderRadius: '6px', background: 'rgba(255,23,68,0.08)', border: '1px solid rgba(255,23,68,0.2)', fontSize: '0.85rem', color: '#fca5a5' }}>
                ✗ {c}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
