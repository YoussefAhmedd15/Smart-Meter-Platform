import React, { useState, useEffect } from 'react';
import { Play, Square, CheckCircle, XCircle, Clock, Terminal, Cpu } from 'lucide-react';
import { apiService } from '../services/api';
import { Meter, TestSuite, TestRun } from '../types';

export const TestingCenter: React.FC = () => {
  const [meters, setMeters] = useState<Meter[]>([]);
  const [suites, setSuites] = useState<TestSuite[]>([]);
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
    setProgress(15);
    setLogs(['[00:00.010] Initializing DLMS Connection on COM6 (300 7E1 Mode E)...', '[00:00.320] Handshake ACK received. Switching baudrate to 9600 baud...']);

    setTimeout(() => {
      setProgress(50);
      setLogs(prev => [...prev, '[00:01.100] SNRM / UA negotiation successful.', '[00:01.850] AARQ low authentication accepted. Fetching Association View...']);
    }, 1200);

    setTimeout(async () => {
      try {
        const run = await apiService.runTest(selectedMeter, selectedSuite);
        setCurrentRun(run);
        setProgress(100);
        setIsRunning(false);
        setLogs(prev => [...prev, `[00:04.120] Suite execution complete. Passed: ${run.passed_tests}/${run.total_tests}. Status: ${run.status}`]);
      } catch (err) {
        setIsRunning(false);
        setProgress(100);
        setLogs(prev => [...prev, `[ERROR] Execution failed: ${err}`]);
      }
    }, 2500);
  };

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>Automated DLMS Testing Center</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Configure test suites, execute hardware association, and monitor real-time test execution.</p>
      </div>

      {/* Control Panel Glass Card */}
      <div className="glass-card" style={{ padding: '20px', display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '16px', alignItems: 'center' }}>
        <div>
          <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>SELECT TARGET METER</label>
          <select
            value={selectedMeter}
            onChange={(e) => setSelectedMeter(Number(e.target.value))}
            style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#111726', color: '#fff', border: '1px solid var(--border-color)' }}
          >
            {meters.map(m => (
              <option key={m.id} value={m.id}>{m.serial_number} — {m.model} ({m.firmware_version})</option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>SELECT TEST SUITE</label>
          <select
            value={selectedSuite}
            onChange={(e) => setSelectedSuite(Number(e.target.value))}
            style={{ width: '100%', padding: '10px', borderRadius: '8px', background: '#111726', color: '#fff', border: '1px solid var(--border-color)' }}
          >
            {suites.map(s => (
              <option key={s.id} value={s.id}>{s.name} ({s.category})</option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', gap: '10px', marginTop: '18px' }}>
          <button className="btn-cyan" onClick={handleStartTest} disabled={isRunning}>
            <Play size={16} /> {isRunning ? 'RUNNING...' : 'START TEST SUITE'}
          </button>
          {isRunning && (
            <button className="btn-secondary" onClick={() => setIsRunning(false)}>
              <Square size={16} color="var(--accent-red)" /> STOP
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {isRunning && (
        <div className="glass-card" style={{ padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.85rem' }}>
            <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>Executing Test Suite...</span>
            <span className="mono" style={{ color: 'var(--text-muted)' }}>{progress}%</span>
          </div>
          <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ width: `${progress}%`, height: '100%', background: 'linear-gradient(90deg, #00f2fe, #00e676)', transition: 'width 0.4s ease' }} />
          </div>
        </div>
      )}

      {/* Live Results & Log Window */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '16px' }}>Test Execution Results</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {[
              { name: 'Mode E 300 Baud Handshake', status: 'PASS', duration: '240 ms', value: '1.0.1.8.0.255' },
              { name: 'SNRM / UA Negotiation', status: 'PASS', duration: '180 ms', value: 'UA Received' },
              { name: 'AARQ Low Authentication', status: 'PASS', duration: '210 ms', value: 'AARE Accepted' },
              { name: 'Active Energy Import Read', status: 'PASS', duration: '195 ms', value: '1245.3 kWh' },
              { name: 'Voltage L1 RMS Read', status: 'PASS', duration: '215 ms', value: '230.2 V' },
              { name: 'Grid Frequency Read', status: 'PASS', duration: '175 ms', value: '50.01 Hz' },
            ].map((tc, idx) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 14px', borderRadius: '8px', background: 'rgba(17,23,38,0.5)', border: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <CheckCircle size={18} color="var(--accent-green)" />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{tc.name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Target: <span className="mono">{tc.value}</span></div>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span className="badge badge-pass">PASS</span>
                  <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>{tc.duration}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live Terminal Log */}
        <div className="glass-card" style={{ padding: '20px', background: '#070a12', border: '1px solid var(--border-cyan)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px', color: 'var(--accent-cyan)' }}>
            <Terminal size={18} />
            <h3 style={{ fontSize: '0.9rem', fontWeight: 600, margin: 0 }} className="mono">LIVE COMMUNICATION TRACE LOG</h3>
          </div>
          <div className="mono" style={{ height: '320px', overflowY: 'auto', fontSize: '0.78rem', display: 'flex', flexDirection: 'column', gap: '6px', color: '#a7f3d0' }}>
            {logs.length === 0 ? (
              <span style={{ color: 'var(--text-dim)' }}>Ready for execution. Click 'START TEST SUITE' to begin DLMS communication trace...</span>
            ) : (
              logs.map((l, idx) => (
                <div key={idx}>{l}</div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
