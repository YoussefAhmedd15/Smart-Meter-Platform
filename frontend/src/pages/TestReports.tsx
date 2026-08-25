import React from 'react';
import { FileText, Download, CheckCircle, FileSpreadsheet } from 'lucide-react';

export const TestReports: React.FC = () => {
  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>Smart Meter Test Certificate & Reports</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Generate and export official PDF testing certificates and Excel/JSON data logs.</p>
      </div>

      <div className="glass-card" style={{ padding: '24px', borderLeft: '4px solid var(--accent-cyan)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Test Run Certificate #104</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Target Meter: ISK-2026-984210 • Iskraemeco AM550-TD1 (v3.14.2)</p>
          </div>
          <span className="badge badge-pass">PASSED & CERTIFIED</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', margin: '16px 0', padding: '16px', borderRadius: '8px', background: 'rgba(17,23,38,0.6)' }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>TOTAL TEST CASES</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>6 / 6</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>EXECUTION DURATION</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>4.12s</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>METROLOGY ACCURACY</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-green)' }}>Class 0.2S</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>FIRMWARE STATUS</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-green)' }}>COMPLIANT</div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
          <button className="btn-cyan" onClick={() => alert('PDF Certificate Report downloaded!')}>
            <Download size={16} /> DOWNLOAD PDF REPORT
          </button>
          <button className="btn-secondary" onClick={() => alert('Excel JSON logs exported!')}>
            <FileSpreadsheet size={16} /> EXPORT EXCEL / JSON
          </button>
        </div>
      </div>
    </div>
  );
};
