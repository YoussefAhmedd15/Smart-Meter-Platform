import React, { useState, useEffect } from 'react';
import { Download, CheckCircle2, FileSpreadsheet, Info, AlertCircle, Loader2 } from 'lucide-react';
import { apiService } from '../services/api';
import { TestRun, Meter } from '../types';

export const TestReports: React.FC = () => {
  const [testRuns, setTestRuns] = useState<TestRun[]>([]);
  const [meters, setMeters] = useState<Meter[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadStatus, setDownloadStatus] = useState<string | null>(null);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [runsData, metersData] = await Promise.all([
          apiService.getTestRuns().catch(() => []),
          apiService.getMeters().catch(() => []),
        ]);
        setTestRuns(runsData);
        setMeters(metersData);
      } catch (err) {
        console.error('Failed to load test runs for reports', err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const meterMap = new Map<number, Meter>();
  meters.forEach(m => {
    const id = m.meter_id || m.id;
    if (id) meterMap.set(id, m);
  });

  const handleDownload = async (runId: number, format: 'pdf' | 'json' = 'pdf') => {
    try {
      setDownloadingId(runId);
      setDownloadStatus(`Generating ${format.toUpperCase()} report for Test Run #${runId}...`);
      const res = await apiService.generateReport(runId, format);
      const downloadUrl = apiService.getReportDownloadUrl(res.filename);

      // Trigger automatic browser download
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = res.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      setDownloadStatus(`Report generated successfully: ${res.filename}`);
      setTimeout(() => setDownloadStatus(null), 5000);
    } catch (err: any) {
      console.error('Failed to generate report', err);
      setDownloadStatus(`Error generating report: ${err?.response?.data?.detail || err.message}`);
      setTimeout(() => setDownloadStatus(null), 6000);
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      <div>
        <h2 className="section-title">Smart Meter Test Certificates &amp; Reports</h2>
        <p className="section-sub">Generate and export official testing certificates and live data logs.</p>
      </div>

      {downloadStatus && (
        <div className="alert-banner info" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Info size={18} style={{ flexShrink: 0 }} />
          <span>{downloadStatus}</span>
        </div>
      )}

      {loading ? (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <Loader2 size={32} className="spin" style={{ margin: '0 auto 12px' }} />
          <div>Loading test certificates and reports...</div>
        </div>
      ) : testRuns.length === 0 ? (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <AlertCircle size={32} style={{ margin: '0 auto 12px', color: 'var(--accent-yellow)' }} />
          <div>No test runs recorded yet. Execute a test in Testing Center to generate certificates.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {testRuns.map(r => {
            const runId = r.test_run_id || r.id;
            const meter = meterMap.get(r.meter_id);
            const isPassed = (r.status as string) === 'COMPLETED' || (r.status as string) === 'PASSED';
            const totalCases = r.total_tests || (r.passed_tests + r.failed_tests);
            const passRate = totalCases > 0 ? ((r.passed_tests / totalCases) * 100).toFixed(0) : '0';
            const duration = r.duration_seconds != null ? `${r.duration_seconds.toFixed(2)}s` : 'N/A';
            const isCurrentDownloading = downloadingId === runId;

            return (
              <div
                key={runId}
                className="glass-card"
                style={{
                  padding: '22px',
                  borderLeft: `4px solid ${isPassed ? 'var(--accent-green)' : 'var(--accent-red)'}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                  <div>
                    <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>
                      Test Run Certificate #{runId}
                    </h3>
                    <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '3px' }}>
                      Meter: <span style={{ color: 'var(--accent-cyan)' }}>{meter?.meter_number || meter?.serial_number || `Meter #${r.meter_id}`}</span> · {meter?.meter_model || meter?.model || 'Generic Model'} ({r.firmware_version || meter?.firmware_version || 'v3.14'})
                    </p>
                  </div>
                  <span className={`badge ${isPassed ? 'badge-pass' : 'badge-fail'}`}>
                    {isPassed ? <CheckCircle2 size={12} /> : null}
                    {isPassed ? 'PASSED & CERTIFIED' : `${r.status || 'FAILED'}`}
                  </span>
                </div>

                <div style={{
                  display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px',
                  padding: '14px', borderRadius: '9px',
                  background: 'rgba(10,15,26,0.6)', marginBottom: '16px',
                }}>
                  {[
                    { label: 'Total Test Cases', value: `${r.passed_tests} / ${totalCases}`, color: 'var(--text-main)' },
                    { label: 'Execution Duration', value: duration, color: 'var(--accent-cyan)' },
                    { label: 'Pass Rate', value: `${passRate}%`, color: 'var(--accent-green)' },
                    { label: 'Firmware Status', value: isPassed ? 'COMPLIANT' : 'REVIEW', color: isPassed ? 'var(--accent-green)' : 'var(--accent-red)' },
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
                  <button
                    className="btn-cyan"
                    disabled={isCurrentDownloading}
                    onClick={() => handleDownload(runId, 'pdf')}
                  >
                    {isCurrentDownloading ? <Loader2 size={15} className="spin" /> : <Download size={15} />}
                    Download PDF Certificate
                  </button>
                  <button
                    className="btn-secondary"
                    disabled={isCurrentDownloading}
                    onClick={() => handleDownload(runId, 'json')}
                  >
                    <FileSpreadsheet size={15} /> Export JSON Certificate
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
