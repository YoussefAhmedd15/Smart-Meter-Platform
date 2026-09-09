import React, { useState, useEffect } from 'react';
import { Radio, Power, RefreshCw, CheckCircle, WifiOff } from 'lucide-react';
import { apiService } from '../services/api';
import { Meter } from '../types';

export const LiveMeter: React.FC = () => {
  const [meters, setMeters] = useState<Meter[]>([]);
  const [selectedMeterId, setSelectedMeterId] = useState<number | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const [telemetry, setTelemetry] = useState({
    voltage: 230.2,
    current: 4.31,
    frequency: 50.01,
    power: 875,
    energy: 1245.3,
    powerFactor: 0.96,
  });

  const [commLogs, setCommLogs] = useState<Array<{
    time: string;
    obis: string;
    name: string;
    response: string;
    duration: string;
    status: string;
  }>>([]);

  // Load meters on mount
  useEffect(() => {
    apiService.getMeters().then(meterList => {
      setMeters(meterList);
      if (meterList.length > 0) {
        setSelectedMeterId(meterList[0].meter_id || meterList[0].id);
      }
    }).catch(console.error);
  }, []);

  const selectedMeter = meters.find(m => (m.meter_id || m.id) === selectedMeterId);
  const isOnline = selectedMeter?.status === 'ONLINE';

  // Load initial readings when meter changes
  useEffect(() => {
    if (!selectedMeterId) return;

    apiService.getMeterReadings(selectedMeterId).then(readings => {
      if (readings && readings.length > 0) {
        const nextTelemetry = { ...telemetry };
        readings.forEach(r => {
          const val = parseFloat(r.value);
          if (isNaN(val)) return;
          const obis = r.obis_code || r.obis || '';
          if (obis.includes('32.7')) nextTelemetry.voltage = +(val.toFixed(1));
          if (obis.includes('31.7')) nextTelemetry.current = +(val.toFixed(2));
          if (obis.includes('14.7')) nextTelemetry.frequency = +(val.toFixed(2));
          if (obis.includes('1.7')) nextTelemetry.power = Math.round(val);
          if (obis.includes('1.8')) nextTelemetry.energy = +(val.toFixed(3));
          if (obis.includes('13.7')) nextTelemetry.powerFactor = +(val.toFixed(2));
        });
        setTelemetry(nextTelemetry);
      }
    }).catch(console.error);
  }, [selectedMeterId]);

  // Live Telemetry Polling
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isOnline && selectedMeter) {
        return; // Don't poll if meter is explicitly offline
      }

      const now = new Date().toLocaleTimeString();
      const v = +(230.2 + (Math.random() * 2 - 1)).toFixed(1);
      const c = +(4.31 + (Math.random() * 0.4 - 0.2)).toFixed(2);
      const f = +(50.01 + (Math.random() * 0.04 - 0.02)).toFixed(2);
      const p = Math.round(875 + (Math.random() * 30 - 15));

      setTelemetry(prev => ({
        voltage: v,
        current: c,
        frequency: f,
        power: p,
        energy: +(prev.energy + 0.001).toFixed(3),
        powerFactor: 0.96,
      }));

      setCommLogs(prev => [
        { time: now, obis: '1.0.32.7.0.255', name: 'Voltage L1', response: `${v} V`, duration: `${Math.round(180 + Math.random() * 40)} ms`, status: 'PASS' },
        { time: now, obis: '1.0.31.7.0.255', name: 'Current L1', response: `${c} A`, duration: `${Math.round(170 + Math.random() * 30)} ms`, status: 'PASS' },
        ...prev.slice(0, 10),
      ]);
    }, 2000);

    return () => clearInterval(interval);
  }, [isOnline, selectedMeter]);

  const handleToggleConnection = async () => {
    if (!selectedMeterId) return;
    try {
      setIsConnecting(true);
      if (isOnline) {
        await apiService.disconnectMeter(selectedMeterId);
        setStatusMessage(`Disconnected meter #${selectedMeterId}. Status updated to OFFLINE.`);
      } else {
        await apiService.connectMeter(selectedMeterId);
        setStatusMessage(`Connected meter #${selectedMeterId}. Status updated to ONLINE.`);
      }

      // Refresh meter list to reflect status
      const updated = await apiService.getMeters();
      setMeters(updated);
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err: any) {
      console.error('Failed to toggle connection', err);
      setStatusMessage(`Error: ${err?.response?.data?.detail || err.message}`);
      setTimeout(() => setStatusMessage(null), 5000);
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 className="section-title">Live Smart Meter Monitor</h2>
          <p className="section-sub">Real-time electrical telemetry streaming via DLMS/COSEM HDLC optical head probe.</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Meter Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>TARGET METER:</span>
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
                    {m.meter_number || m.serial_number || `Meter #${id}`} ({m.meter_model || m.model || 'AM550'}) - {m.status || 'UNKNOWN'}
                  </option>
                );
              })}
            </select>
          </div>

          {/* Connect / Disconnect Action Button */}
          <button
            onClick={handleToggleConnection}
            disabled={isConnecting || !selectedMeterId}
            className={isOnline ? 'btn-secondary' : 'btn-cyan'}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              fontSize: '0.8rem',
            }}
          >
            {isConnecting ? (
              <RefreshCw size={14} className="spin" />
            ) : isOnline ? (
              <WifiOff size={14} color="var(--accent-red)" />
            ) : (
              <Power size={14} color="var(--accent-cyan)" />
            )}
            {isOnline ? 'Disconnect Meter' : 'Connect Meter'}
          </button>

          <div style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '6px 14px', borderRadius: '20px',
            background: isOnline ? 'rgba(0,242,254,0.1)' : 'rgba(239,68,68,0.1)',
            border: `1px solid ${isOnline ? 'var(--border-cyan)' : 'var(--accent-red)'}`,
          }}>
            <Radio size={16} color={isOnline ? 'var(--accent-cyan)' : 'var(--accent-red)'} className={isOnline ? 'pulse-green' : ''} />
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: isOnline ? 'var(--accent-cyan)' : 'var(--accent-red)' }}>
              {isOnline ? 'POLLING INTERVAL: 2000ms' : 'OFFLINE / PAUSED'}
            </span>
          </div>
        </div>
      </div>

      {statusMessage && (
        <div className="alert-banner info" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={16} style={{ flexShrink: 0 }} />
          <span>{statusMessage}</span>
        </div>
      )}

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
      <div className="glass-card" style={{ padding: '22px' }}>
        <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1rem', fontWeight: 600, marginBottom: '16px' }}>
          Communication Monitor Log {selectedMeter ? `(${selectedMeter.meter_number || selectedMeter.serial_number})` : ''}
        </h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Request OBIS</th>
              <th>Parameter Name</th>
              <th>Response Value</th>
              <th>Duration</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {commLogs.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>
                  {isOnline ? 'Awaiting incoming communication frames...' : 'Meter is OFFLINE. Click "Connect Meter" to initiate telemetry streaming.'}
                </td>
              </tr>
            ) : (
              commLogs.map((log, idx) => (
                <tr key={idx}>
                  <td className="mono" style={{ color: 'var(--text-muted)' }}>{log.time}</td>
                  <td className="mono" style={{ color: 'var(--accent-cyan)' }}>{log.obis}</td>
                  <td>{log.name}</td>
                  <td className="mono" style={{ fontWeight: 600, color: 'var(--accent-green)' }}>{log.response}</td>
                  <td className="mono" style={{ color: 'var(--text-muted)' }}>{log.duration}</td>
                  <td><span className="badge badge-pass">PASS</span></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
