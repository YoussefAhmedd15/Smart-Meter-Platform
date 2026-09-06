import React, { useState } from 'react';
import { FileText, Download, CheckCircle2, FileSpreadsheet, Info } from 'lucide-react';

export const TestReports: React.FC = () => {
  const [downloadStatus, setDownloadStatus] = useState<string | null>(null);

  const handleDownload = (type: string) => {
    // Backend report generation endpoint exists at POST /api/reports/test-run/{run_id}
    // For now the feature is UI-ready; the backend team will wire up actual file generation.
    setDownloadStatus(`${type} export requested — check backend /api/reports endpoint.`);
    setTimeout(() => setDownloadStatus(null), 4000);
  };

  const reportData = [
    { runId: 104, meter: 'ISK-2026-984210', model: 'Iskraemeco AM550-TD1', firmware: 'v3.14.2', totalCases: 6, passedCases: 6, duration: '4.12s', accuracy: 'Class 0.2S', status: 'PASSED' },
    { runId: 103, meter: 'ISK-2026-984211', model: 'Iskraemeco MT880-D2',  firmware: 'v3.13.0', totalCases: 9, passedCases: 7, duration: '6.34s', accuracy: 'Class 0.5',  status: 'FAILED' },
    { runId: 102, meter: 'ISK-2026-984210', model: 'Iskraemeco AM550-TD1', firmware: 'v3.13.0', totalCases: 6, passedCases: 5, duration: '5.01s', accuracy: 'Class 1',    status: 'FAILED' },
  ];

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      <div>
        <h2 className="section-title">Smart Meter Test Certificates &amp; Reports</h2>
        <p className="section-sub">Generate and export official testing certificates and data logs.</p>
      </div>

      {downloadStatus && (
        <div className="alert-banner info">
          <Info size={18} style={{ flexShrink: 0 }} />
          <span>{downloadStatus}</span>
        </div>
      )}

      {/* Reports List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {reportData.map(r => (
          <div
            key={r.runId}
            className="glass-card"
            style={{
              padding: '22px',
              borderLeft: `4px solid ${r.status === 'PASSED' ? 'var(--accent-green)' : 'var(--accent-red)'}`,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>
                  Test Run Certificate #{r.runId}
                </h3>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '3px' }}>
                  Meter: <span style={{ color: 'var(--accent-cyan)' }}>{r.meter}</span> · {r.model} ({r.firmware})
                </p>
              </div>
              <span className={`badge ${r.status === 'PASSED' ? 'badge-pass' : 'badge-fail'}`}>
                {r.status === 'PASSED' ? <CheckCircle2 size={12} /> : null}
                {r.status} &amp; CERTIFIED
              </span>
            </div>

            <div style={{
              display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px',
              padding: '14px', borderRadius: '9px',
              background: 'rgba(10,15,26,0.6)', marginBottom: '16px',
            }}>
              {[
                { label: 'Total Test Cases', value: `${r.passedCases} / ${r.totalCases}`, color: 'var(--text-main)' },
                { label: 'Execution Duration', value: r.duration, color: 'var(--accent-cyan)' },
                { label: 'Metrology Accuracy', value: r.accuracy, color: 'var(--accent-green)' },
                { label: 'Firmware Status', value: r.status === 'PASSED' ? 'COMPLIANT' : 'REVIEW', color: r.status === 'PASSED' ? 'var(--accent-green)' : 'var(--accent-red)' },
              ].map(s => (
                <div key={s.label}>
                  <div className="label">{s.label}</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: s.color, fontFamily: 'var(--font-head)', marginTop: '4px' }}>
                    {s.value}
                  </div>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="btn-cyan" onClick={() => handleDownload('PDF')}>
                <Download size={15} /> Download PDF Report
              </button>
              <button className="btn-secondary" onClick={() => handleDownload('Excel/JSON')}>
                <FileSpreadsheet size={15} /> Export Excel / JSON
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
