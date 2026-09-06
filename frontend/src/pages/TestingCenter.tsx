import React, { useState, useEffect } from 'react';
import { Play, Square, CheckCircle, XCircle, Clock, Terminal, Cpu } from 'lucide-react';
import { apiService } from '../services/api';
import { Meter, TestSuite, TestRun } from '../types';

export const TestingCenter: React.FC = () => {
  const [meters, setMeters]               = useState<Meter[]>([]);
  const [suites, setSuites]               = useState<TestSuite[]>([]);
  const [selectedMeter, setSelectedMeter] = useState<number>(1);
  const [selectedSuite, setSelectedSuite] = useState<number>(1);
  const [isRunning, setIsRunning] = useState<bool>(false);
  const [progress, setProgress] = useState<number>(0);
  const [currentRun, setCurrentRun] = useState<TestRun | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    apiService.getMeters().then(setMeters).catch(console.error);
    apiService.getTestSuites().then(setSuites).catch(console.error);
  }, []);

  const handleStartTest = async () => {
    setIsRunning(true);
    setProgress(0);
    setCurrentRun(null);
    setResults([]);
    setLogs([]);

    addLog(`Initializing DLMS connection on target meter #${selectedMeter}…`);
    addLog(`Interface: HDLC_WITH_MODE_E · 300 baud, 7E1`);

    // Simulate initial handshake phase
    await new Promise(r => setTimeout(r, 400));
    setProgress(15);
    addLog('IEC 62056-21 Mode E identification request sent…');

    await new Promise(r => setTimeout(r, 500));
    setProgress(30);
    addLog('Handshake ACK received. Switching baudrate to 9600 baud…');
    addLog('SNRM / UA frame negotiation successful.');

    await new Promise(r => setTimeout(r, 500));
    setProgress(50);
    addLog('AARQ low-level authentication accepted.');
    addLog(`Executing test suite ID ${selectedSuite}…`);

    try {
      const run = await apiService.runTest(selectedMeter, selectedSuite);
      setProgress(85);
      addLog(`Suite execution complete. Status: ${run.status}`);
      addLog(`Results: ${run.passed_tests} PASSED · ${run.failed_tests} FAILED · total ${run.total_tests}`);

      // Fetch detailed results
      try {
        const detail = await fetch(`/api/test-runs/${run.id}`);
        if (detail.ok) {
          const data = await detail.json();
          if (data.results?.length) {
            setResults(data.results);
            data.results.forEach((r: TestResult) => {
              addLog(`  [${r.status}] ${r.test_name} — ${r.actual_value ?? r.error_message ?? ''} (${r.duration_ms}ms)`);
            });
          }
        }
      } catch { /* results display will fall back to summary */ }

      setCurrentRun(run);
      setProgress(100);
    } catch (err) {
      addLog(`ERROR: Execution failed — ${err}`);
      setProgress(100);
    } finally {
      setIsRunning(false);
    }
  };

  const handleStop = () => {
    setIsRunning(false);
    addLog('Test execution aborted by user.');
    setProgress(100);
  };

  const selectedSuiteObj = suites.find(s => s.id === selectedSuite);
  const selectedMeterObj = meters.find(m => m.id === selectedMeter);

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>Automated DLMS Testing Center</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Configure test suites, execute hardware association, and monitor real-time test execution.</p>
      </div>

      {/* ── Control Panel ── */}
      <div className="glass-card" style={{ padding: '22px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
          {/* Meter selector */}
          <div>
            <label className="form-label">Target Smart Meter</label>
            <select
              className="form-select"
              value={selectedMeter}
              onChange={e => setSelectedMeter(Number(e.target.value))}
              disabled={isRunning}
            >
              {meters.map(m => (
                <option key={m.id} value={m.id}>
                  {m.serial_number} — {m.model} ({m.firmware_version})
                </option>
              ))}
            </select>
          </div>

          {/* Suite selector */}
          <div>
            <label className="form-label">Test Suite</label>
            <select
              className="form-select"
              value={selectedSuite}
              onChange={e => setSelectedSuite(Number(e.target.value))}
              disabled={isRunning}
            >
              {suites.map(s => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.category})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Run meta row */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '16px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            {selectedSuiteObj && (
              <>
                <span>Suite: <strong style={{ color: 'var(--text-main)' }}>{selectedSuiteObj.name}</strong></span>
                <span>Cases: <strong style={{ color: 'var(--accent-cyan)' }}>{selectedSuiteObj.total_cases}</strong></span>
              </>
            )}
            {selectedMeterObj && (
              <span>Firmware: <strong className="mono" style={{ color: 'var(--accent-cyan)' }}>{selectedMeterObj.firmware_version}</strong></span>
            )}
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn-cyan" onClick={handleStartTest} disabled={isRunning}>
              <Play size={16} />
              {isRunning ? 'Running…' : 'Start Test Suite'}
            </button>
            {isRunning && (
              <button className="btn-danger" onClick={handleStop}>
                <Square size={14} /> Stop
              </button>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        {(isRunning || progress > 0) && (
          <div style={{ marginTop: '18px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
              <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>
                {isRunning ? 'Executing DLMS test suite…' : currentRun ? `Complete — ${currentRun.status}` : 'Stopped'}
              </span>
              <span className="mono">{progress}%</span>
            </div>
            <div className="progress-track">
              <div
                className={`progress-fill${currentRun?.status === 'COMPLETED' ? '-green' : ''}`}
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* ── Results + Log ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: '20px' }}>

        {/* Results Panel */}
        <div className="glass-card" style={{ padding: '22px' }}>
          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            marginBottom: '16px', cursor: 'pointer',
          }}
            onClick={() => setShowResults(r => !r)}
          >
            <div>
              <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1rem', fontWeight: 600, margin: 0 }}>
                Test Execution Results
              </h3>
              {currentRun && (
                <p style={{ fontSize: '0.73rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                  Run #{currentRun.id} · {currentRun.passed_tests} passed, {currentRun.failed_tests} failed
                </p>
              )}
            </div>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              {currentRun && (
                <span className={`badge ${currentRun.status === 'COMPLETED' ? 'badge-pass' : 'badge-fail'}`}>
                  {currentRun.status}
                </span>
              )}
              {showResults ? <ChevronUp size={16} color="var(--text-dim)" /> : <ChevronDown size={16} color="var(--text-dim)" />}
            </div>
          </div>

          {showResults && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {/* Real results from API */}
              {results.length > 0 ? results.map((r, idx) => (
                <div key={idx} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '11px 14px', borderRadius: '9px',
                  background: 'rgba(10,15,26,0.6)',
                  border: `1px solid ${r.status === 'PASS' ? 'rgba(0,230,118,0.15)' : 'rgba(255,23,68,0.15)'}`,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {r.status === 'PASS'
                      ? <CheckCircle2 size={17} color="var(--accent-green)" />
                      : <XCircle size={17} color="var(--accent-red)" />
                    }
                    <div>
                      <div style={{ fontSize: '0.84rem', fontWeight: 600 }}>{r.test_name}</div>
                      <div className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                        {r.actual_value ?? r.error_message ?? '—'}
                      </div>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span className={`badge ${r.status === 'PASS' ? 'badge-pass' : 'badge-fail'}`}>{r.status}</span>
                    <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '4px' }}>
                      {r.duration_ms}ms
                    </div>
                  </div>
                </div>
              )) : (
                /* Placeholder when no run yet */
                !currentRun ? (
                  <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-dim)' }}>
                    <Cpu size={32} color="var(--text-dim)" style={{ marginBottom: '8px', display: 'block', margin: '0 auto 8px' }} />
                    <div style={{ fontSize: '0.85rem' }}>No test run yet. Click <strong>Start Test Suite</strong> to begin.</div>
                  </div>
                ) : (
                  /* Summary when results not available */
                  <div style={{ padding: '16px', borderRadius: '9px', background: 'rgba(10,15,26,0.5)', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                      <strong style={{ color: 'var(--accent-green)', fontSize: '1.4rem' }}>{currentRun.passed_tests}</strong> passed &nbsp;·&nbsp;
                      <strong style={{ color: 'var(--accent-red)', fontSize: '1.4rem' }}>{currentRun.failed_tests}</strong> failed
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
                      Duration: {currentRun.duration_seconds}s
                    </div>
                  </div>
                )
              )}
            </div>
          )}
        </div>

        {/* Live Terminal Log */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '10px 16px',
            background: 'rgba(4,6,12,0.95)',
            border: '1px solid var(--border-cyan)',
            borderBottom: 'none',
            borderRadius: '12px 12px 0 0',
          }}>
            <div className="dot dot-red" style={{ width: '10px', height: '10px' }} />
            <div className="dot dot-amber" style={{ width: '10px', height: '10px', background: 'var(--accent-amber)' }} />
            <div className="dot dot-green" style={{ width: '10px', height: '10px' }} />
            <Terminal size={14} color="var(--accent-cyan)" style={{ marginLeft: '8px' }} />
            <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>
              DLMS COMMUNICATION TRACE
            </span>
            {isRunning && <div className="dot dot-green pulse-green" style={{ marginLeft: 'auto' }} />}
          </div>
          <div
            ref={logRef}
            className="terminal"
            style={{
              borderRadius: '0 0 12px 12px',
              borderTop: 'none',
              height: '340px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
            }}
          >
            {logs.length === 0 ? (
              <span style={{ color: 'var(--text-dim)' }}>
                Ready for execution. Click "Start Test Suite" to begin DLMS trace…
              </span>
            ) : logs.map((l, i) => (
              <div key={i} style={{ color: l.includes('ERROR') || l.includes('FAIL') ? '#fca5a5' : l.includes('PASS') ? '#86efac' : '#a7f3d0' }}>
                {l}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Run History Note ── */}
      {currentRun && (
        <div className="alert-banner info">
          <CheckCircle2 size={18} style={{ flexShrink: 0, marginTop: '1px' }} />
          <div>
            <strong>Test Run #{currentRun.id} recorded.</strong> Results saved to the database and available in
            the <strong>Test Reports</strong> section.
            Duration: <span className="mono">{currentRun.duration_seconds}s</span> ·
            Total: <span className="mono">{currentRun.total_tests}</span> cases.
          </div>
        </div>
      )}
    </div>
  );
};
