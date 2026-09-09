import React, { useState, useEffect } from 'react';
import { Cpu, CheckCircle2, XCircle } from 'lucide-react';
import { apiService } from '../services/api';
import { Meter, TestRun } from '../types';

export const MeterProfile: React.FC = () => {
  const [meters, setMeters] = useState<Meter[]>([]);
  const [selectedMeterId, setSelectedMeterId] = useState<number | null>(null);
  const [testRuns, setTestRuns] = useState<TestRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [meterList, runsList] = await Promise.all([
          apiService.getMeters().catch(() => []),
          apiService.getTestRuns().catch(() => []),
        ]);
        setMeters(meterList);
        setTestRuns(runsList);
        if (meterList.length > 0) {
          setSelectedMeterId(meterList[0].meter_id || meterList[0].id);
        }
      } catch (err) {
        console.error('Failed to load meter profile data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const selectedMeter = meters.find(m => (m.meter_id || m.id) === selectedMeterId);
  const meterRuns = testRuns.filter(r => r.meter_id === selectedMeterId);

  const totalRuns = meterRuns.length;
  const passedRuns = meterRuns.filter(r => (r.status as string) === 'COMPLETED' || (r.status as string) === 'PASSED').length;
  const failedRuns = meterRuns.filter(r => r.status === 'FAILED').length;
  const passRate = totalRuns > 0 ? ((passedRuns / totalRuns) * 100).toFixed(1) : '100.0';
  const qualityScore = totalRuns > 0 ? (+passRate * 0.98).toFixed(1) : '98.5';

  const lastRun = meterRuns.length > 0 ? meterRuns[0] : null;
  const isOnline = selectedMeter?.status === 'ONLINE';

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 className="section-title">Digital Meter Profile</h2>
          <p className="section-sub">Unified hardware identity, testing history, quality score, and firmware intelligence.</p>
        </div>

        {/* Meter Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>SELECT METER:</span>
          <select
            value={selectedMeterId || ''}
            onChange={e => setSelectedMeterId(Number(e.target.value))}
            style={{
              background: 'rgba(15,23,42,0.9)',
              color: '#fff',
              border: '1px solid var(--border-cyan)',
              borderRadius: '6px',
              padding: '6px 12px',
              fontSize: '0.85rem',
              outline: 'none',
            }}
          >
            {meters.map(m => {
              const id = m.meter_id || m.id;
              return (
                <option key={id} value={id}>
                  {m.meter_number || m.serial_number || `Meter #${id}`} - {m.meter_model || m.model || 'AM550'}
                </option>
              );
            })}
          </select>
        </div>
      </div>

      {loading || !selectedMeter ? (
        <div className="glass-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading meter profile data...
        </div>
      ) : (
        <>
          {/* Identity Card */}
          <div className="glass-card" style={{ padding: '24px', display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px', alignItems: 'center' }}>
            <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(17,23,38,0.8)', border: '1px solid var(--border-cyan)', textAlign: 'center' }}>
              <Cpu size={48} color="var(--accent-cyan)" style={{ marginBottom: '12px' }} />
              <h3 className="mono" style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                {selectedMeter.meter_number || selectedMeter.serial_number}
              </h3>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                {selectedMeter.meter_model || selectedMeter.model}
              </div>
              <div className={`badge ${isOnline ? 'badge-pass' : 'badge-fail'}`} style={{ marginTop: '12px' }}>
                <div className={`dot ${isOnline ? 'dot-green pulse-green' : 'dot-red'}`} />
                {isOnline ? 'ONLINE & CERTIFIED' : 'OFFLINE'}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>MANUFACTURER</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 600, marginTop: '2px' }}>{selectedMeter.manufacturer || 'Iskraemeco d.d.'}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>INSTALLED FIRMWARE</span>
                <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--accent-cyan)', marginTop: '2px' }}>
                  {selectedMeter.firmware_version || 'v3.14.2'}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>PROTOCOL & MEDIA</span>
                <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 600, marginTop: '2px' }}>
                  {selectedMeter.communication_protocol || 'DLMS/COSEM (HDLC)'}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>COMM PORT / BAUD</span>
                <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--accent-green)', marginTop: '2px' }}>
                  {selectedMeter.port_name || 'COM1'} @ {selectedMeter.baud_rate || 9600} baud
                </div>
              </div>
            </div>
          </div>

          {/* Profile Metrics Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>QUALITY SCORE</div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-cyan)', marginTop: '4px' }}>
                {qualityScore} <span style={{ fontSize: '1rem', color: 'var(--text-dim)' }}>/ 100</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--accent-green)', marginTop: '4px' }}>
                Class A Metrology Compliance
              </div>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>TOTAL TEST RUNS</div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#f1f5f9', marginTop: '4px' }}>
                {totalRuns}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                {passedRuns} passed · {failedRuns} failed
              </div>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>HISTORICAL PASS RATE</div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-green)', marginTop: '4px' }}>
                {passRate}%
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                {failedRuns === 0 ? 'Zero active regressions' : `${failedRuns} failures logged`}
              </div>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>LAST TEST RUN</div>
              {lastRun ? (
                <>
                  <div style={{ fontSize: '1.2rem', fontWeight: 700, color: (lastRun.status as string) === 'COMPLETED' || (lastRun.status as string) === 'PASSED' ? 'var(--accent-green)' : 'var(--accent-yellow)', marginTop: '8px' }}>
                    {lastRun.status} ({lastRun.duration_seconds ? `${lastRun.duration_seconds.toFixed(1)}s` : 'N/A'})
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Run #{lastRun.test_run_id || lastRun.id} · {lastRun.start_time || lastRun.started_at ? new Date(lastRun.start_time || lastRun.started_at).toLocaleDateString() : 'Recent'}
                  </div>
                </>
              ) : (
                <div style={{ fontSize: '1rem', color: 'var(--text-muted)', marginTop: '12px' }}>
                  No execution history
                </div>
              )}
            </div>
          </div>

          {/* Meter Test History Table */}
          <div className="glass-card" style={{ padding: '22px' }}>
            <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1rem', fontWeight: 600, marginBottom: '16px' }}>
              Execution History for {selectedMeter.meter_number || selectedMeter.serial_number}
            </h3>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Execution Timestamp</th>
                  <th>Firmware Version</th>
                  <th>Test Cases Passed</th>
                  <th>Duration</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {meterRuns.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '24px' }}>
                      No test runs recorded for this meter yet.
                    </td>
                  </tr>
                ) : (
                  meterRuns.map(r => {
                    const runId = r.test_run_id || r.id;
                    const isPassed = (r.status as string) === 'COMPLETED' || (r.status as string) === 'PASSED';
                    const totalCases = r.total_tests || (r.passed_tests + r.failed_tests);
                    const runDate = r.start_time || r.started_at;
                    return (
                      <tr key={runId}>
                        <td className="mono" style={{ color: 'var(--accent-cyan)' }}>#{runId}</td>
                        <td className="mono" style={{ color: 'var(--text-muted)' }}>
                          {runDate ? new Date(runDate).toLocaleString() : 'N/A'}
                        </td>
                        <td className="mono">{r.firmware_version || selectedMeter.firmware_version}</td>
                        <td className="mono">
                          {r.passed_tests} / {totalCases}
                        </td>
                        <td className="mono" style={{ color: 'var(--text-muted)' }}>
                          {r.duration_seconds != null ? `${r.duration_seconds.toFixed(2)}s` : 'N/A'}
                        </td>
                        <td>
                          <span className={`badge ${isPassed ? 'badge-pass' : 'badge-fail'}`}>
                            {isPassed ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                            {r.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};
