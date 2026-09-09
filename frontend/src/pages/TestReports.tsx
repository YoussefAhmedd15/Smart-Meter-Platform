import React, { useCallback, useEffect, useState } from 'react';
import { FileText, Download, CheckCircle2, XCircle, FileSpreadsheet, RefreshCw } from 'lucide-react';
import { apiService } from '../services/api';
import { TestRun } from '../types';

const EmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div style={{ textAlign: 'center', padding: '48px 24px', color: 'var(--text-dim)' }}>
    <FileText size={40} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
    <p style={{ fontSize: '0.9rem' }}>{message}</p>
  </div>
);

function triggerBrowserDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export const TestReports: React.FC = () => {
  const [runs, setRuns] = useState<TestRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [status, setStatus] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);
  const [generating, setGenerating] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const data = await apiService.getTestRuns();
      setRuns(data);
    } catch (err: any) {
      setLoadError(err?.message ?? 'Could not reach the backend.');
      setRuns([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const showStatus = (msg: string, type: 'success' | 'error' = 'success') => {
    setStatus({ msg, type });
    setTimeout(() => setStatus(null), 4000);
  };

  const handleDownload = async (runId: number, formatType: string) => {
    setGenerating(runId);
    try {
      const report = await apiService.generateReport(runId, formatType);
      const blob = await apiService.downloadReportFile(report.download_url);
      triggerBrowserDownload(blob, report.filename);
      showStatus(`Report for Test Run #${runId} downloaded.`, 'success');
    } catch (err: any) {
      showStatus(err?.message ?? 'Report generation failed. Check that the backend is running.', 'error');
    } finally {
      setGenerating(null);
    }
  };

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 className="section-title">Smart Meter Test Certificates &amp; Reports</h2>
          <p className="section-sub">Generate and export official testing certificates and data logs.</p>
        </div>
        <button className="btn-ghost" onClick={load} title="Refresh">
          <RefreshCw size={15} className={loading ? 'spin' : ''} />
        </button>
      </div>

      {status && (
        <div className={`alert-banner ${status.type === 'success' ? 'success' : 'danger'}`}>
          {status.type === 'success' ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
          <span>{status.msg}</span>
        </div>
      )}

      {loadError && (
        <div className="alert-banner danger">
          <XCircle size={18} style={{ flexShrink: 0 }} />
          <span>Could not load test runs: {loadError}</span>
        </div>
      )}

      {/* Reports List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {[1, 2, 3].map(i => <div key={i} className="skeleton" style={{ height: '120px', borderRadius: '12px' }} />)}
          </div>
        ) : runs.length === 0 ? (
          <EmptyState
            message={
              loadError
                ? 'Backend unreachable — no test run data available.'
                : 'No test runs recorded yet. Run a test suite from the Testing Center to generate a report.'
            }
          />
        ) : (
          runs.map(r => {
            const passed = r.status === 'COMPLETED';
            return (
              <div
                key={r.id}
                className="glass-card"
                style={{
                  padding: '22px',
                  borderLeft: `4px solid ${passed ? 'var(--accent-green)' : 'var(--accent-red)'}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                  <div>
                    <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>
                      Test Run Certificate #{r.id}
                    </h3>
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '3px' }}>
                      Meter #{r.meter_id} · Firmware <span style={{ color: 'var(--accent-cyan)' }}>{r.firmware_version}</span>
                    </p>
                  </div>
                  <span className={`badge ${passed ? 'badge-pass' : 'badge-fail'}`}>
                    {passed ? <CheckCircle2 size={12} /> : null}
                    {r.status}
                  </span>
                </div>

                <div style={{
                  display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px',
                  padding: '14px', borderRadius: '9px',
                  background: 'rgba(10,15,26,0.6)', marginBottom: '16px',
                }}>
                  {[
                    { label: 'Total Test Cases', value: `${r.passed_tests} / ${r.total_tests}`, color: 'var(--text-main)' },
                    { label: 'Execution Duration', value: `${r.duration_seconds}s`, color: 'var(--accent-cyan)' },
                    { label: 'Failed Cases', value: String(r.failed_tests), color: r.failed_tests > 0 ? 'var(--accent-red)' : 'var(--accent-green)' },
                    { label: 'Started At', value: r.started_at ? new Date(r.started_at).toLocaleString() : '—', color: 'var(--text-main)' },
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
                  <button className="btn-cyan" onClick={() => handleDownload(r.id, 'pdf')} disabled={generating === r.id}>
                    <Download size={15} /> {generating === r.id ? 'Generating…' : 'Download Report'}
                  </button>
                  <button className="btn-secondary" onClick={() => handleDownload(r.id, 'json')} disabled={generating === r.id}>
                    <FileSpreadsheet size={15} /> Export JSON
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
