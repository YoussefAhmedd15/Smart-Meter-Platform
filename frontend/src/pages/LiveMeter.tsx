import React, { useState, useEffect } from 'react';
import { Activity, Zap, Gauge, Flame, Clock, Radio } from 'lucide-react';
import { apiService } from '../services/api';
import { MeterReading } from '../types';

export const LiveMeter: React.FC = () => {
  const [readings, setReadings] = useState<MeterReading[]>([]);
  const [telemetry, setTelemetry] = useState({
    voltage: 230.2,
    current: 4.31,
    frequency: 50.01,
    power: 875,
    energy: 1245.3,
    powerFactor: 0.96,
  });

  const [commLogs, setCommLogs] = useState<any[]>([]);

  useEffect(() => {
    // Initial fetch
    apiService.getMeterReadings(1).then(setReadings).catch(console.error);

    // Live Telemetry Polling Simulation
    const interval = setInterval(() => {
      const now = new Date().toLocaleTimeString();
      const v = +(230.2 + (Math.random() * 2 - 1)).toFixed(1);
      const c = +(4.31 + (Math.random() * 0.4 - 0.2)).toFixed(2);
      const f = +(50.01 + (Math.random() * 0.04 - 0.02)).toFixed(2);
      const p = Math.round(875 + (Math.random() * 30 - 15));

      setTelemetry({
        voltage: v,
        current: c,
        frequency: f,
        power: p,
        energy: +(1245.3 + Math.random() * 0.005).toFixed(3),
        powerFactor: 0.96,
      });

      setCommLogs(prev => [
        { time: now, obis: '1.0.32.7.0.255', name: 'Voltage L1', response: `${v} V`, duration: `${Math.round(200 + Math.random() * 50)} ms`, status: 'PASS' },
        { time: now, obis: '1.0.31.7.0.255', name: 'Current L1', response: `${c} A`, duration: `${Math.round(190 + Math.random() * 40)} ms`, status: 'PASS' },
        ...prev.slice(0, 10),
      ]);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>Live Smart Meter Monitor</h2>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Real-time electrical telemetry streaming via DLMS/COSEM HDLC optical head probe.</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 14px', borderRadius: '20px', background: 'rgba(0,242,254,0.1)', border: '1px solid var(--border-cyan)' }}>
          <Radio size={16} color="var(--accent-cyan)" className="pulse-green" />
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>POLLING INTERVAL: 2000ms</span>
        </div>
      </div>

      {/* Telemetry Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
        <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #00f2fe' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '8px' }}>VOLTAGE L1</div>
          <div className="mono" style={{ fontSize: '2.2rem', fontWeight: 800, color: '#00f2fe' }}>{telemetry.voltage} <span style={{ fontSize: '1rem', color: 'var(--text-dim)' }}>V</span></div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>OBIS: 1.0.32.7.0.255</div>
        </div>

        <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #00e676' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '8px' }}>CURRENT L1</div>
          <div className="mono" style={{ fontSize: '2.2rem', fontWeight: 800, color: '#00e676' }}>{telemetry.current} <span style={{ fontSize: '1rem', color: 'var(--text-dim)' }}>A</span></div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>OBIS: 1.0.31.7.0.255</div>
        </div>

        <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #ffab00' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '8px' }}>FREQUENCY</div>
          <div className="mono" style={{ fontSize: '2.2rem', fontWeight: 800, color: '#ffab00' }}>{telemetry.frequency} <span style={{ fontSize: '1rem', color: 'var(--text-dim)' }}>Hz</span></div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>OBIS: 1.0.14.7.0.255</div>
        </div>

        <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #4facfe' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '8px' }}>ACTIVE POWER</div>
          <div className="mono" style={{ fontSize: '2.2rem', fontWeight: 800, color: '#4facfe' }}>{telemetry.power} <span style={{ fontSize: '1rem', color: 'var(--text-dim)' }}>W</span></div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>OBIS: 1.0.1.7.0.255</div>
        </div>

        <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #7f00ff' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '8px' }}>ACTIVE ENERGY (+A)</div>
          <div className="mono" style={{ fontSize: '1.8rem', fontWeight: 800, color: '#a7f3d0' }}>{telemetry.energy} <span style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>kWh</span></div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>OBIS: 1.0.1.8.0.255</div>
        </div>

        <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid #e2e8f0' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '8px' }}>POWER FACTOR</div>
          <div className="mono" style={{ fontSize: '2.2rem', fontWeight: 800, color: '#f1f5f9' }}>{telemetry.powerFactor}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>OBIS: 1.0.13.7.0.255</div>
        </div>
      </div>

      {/* Communication Monitor Table */}
      <div className="glass-card" style={{ padding: '20px' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '16px' }}>Communication Monitor Log</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '10px' }}>TIMESTAMP</th>
              <th style={{ padding: '10px' }}>REQUEST OBIS</th>
              <th style={{ padding: '10px' }}>PARAMETER NAME</th>
              <th style={{ padding: '10px' }}>RESPONSE VALUE</th>
              <th style={{ padding: '10px' }}>DURATION</th>
              <th style={{ padding: '10px' }}>STATUS</th>
            </tr>
          </thead>
          <tbody>
            {commLogs.map((log, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td className="mono" style={{ padding: '10px', color: 'var(--text-muted)' }}>{log.time}</td>
                <td className="mono" style={{ padding: '10px', color: 'var(--accent-cyan)' }}>{log.obis}</td>
                <td style={{ padding: '10px' }}>{log.name}</td>
                <td className="mono" style={{ padding: '10px', fontWeight: 600, color: 'var(--accent-green)' }}>{log.response}</td>
                <td className="mono" style={{ padding: '10px', color: 'var(--text-muted)' }}>{log.duration}</td>
                <td style={{ padding: '10px' }}><span className="badge badge-pass">PASS</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
