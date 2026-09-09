import React, { useEffect, useRef, useState } from 'react';
import { Radio, AlertTriangle, Plug, PlugZap } from 'lucide-react';
import { apiService } from '../services/api';
import { MeterReading } from '../types';

const METER_ID = 1;
const POLL_INTERVAL_MS = 2000;

// Real OBIS logical names, from meter/obis.py's COMMON_OBIS_CODES —
// not guessed.
const OBIS = {
  voltage: '1.0.32.7.0.255',
  current: '1.0.31.7.0.255',
  frequency: '1.0.14.7.0.255',
  power: '1.0.1.7.0.255',
  energy: '1.0.1.8.0.255',
  powerFactor: '1.0.13.7.0.255',
} as const;

interface CommLogEntry {
  time: string;
  status: 'PASS' | 'FAIL';
  durationMs: number;
  detail: string;
}

// Client-side-only log. Built entirely from this browser tab's own poll
// outcomes (fetch success/failure, client-measured round-trip time) — it is
// NOT a durable server record. Nothing here is persisted to the backend;
// refreshing the page or opening the page in another tab starts an empty
// log. If a real, durable, cross-session communication log is ever needed,
// that requires new backend work (a table + a write path at the reader
// layer) — this is deliberately not that.
const MAX_COMM_LOG_ROWS = 10;

function findValue(readings: MeterReading[], obis: string): string | null {
  const r = readings.find((row) => row.obis === obis);
  return r ? r.value : null;
}

function findUnit(readings: MeterReading[], obis: string, fallback: string): string {
  const r = readings.find((row) => row.obis === obis);
  return r?.unit || fallback;
}

export const LiveMeter: React.FC = () => {
  const [readings, setReadings] = useState<MeterReading[]>([]);
  const [dataSource, setDataSource] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);
  const [meterStatus, setMeterStatus] = useState<string | null>(null);
  const [commLogs, setCommLogs] = useState<CommLogEntry[]>([]);
  const [connecting, setConnecting] = useState(false);
  const hasEverSucceeded = useRef(false);

  const poll = async () => {
    const start = performance.now();
    const time = new Date().toLocaleTimeString();
    try {
      const data = await apiService.getMeterReadingsOrThrow(METER_ID);
      const durationMs = Math.round(performance.now() - start);
      hasEverSucceeded.current = true;
      setReadings(data);
      setDataSource(data[0]?.data_source ?? null);
      setLastUpdated(new Date());
      setPollError(null);
      setCommLogs((prev) => [
        { time, status: 'PASS', durationMs, detail: `${data.length} reading(s) received` },
        ...prev.slice(0, MAX_COMM_LOG_ROWS - 1),
      ]);
    } catch (err: any) {
      const durationMs = Math.round(performance.now() - start);
      setPollError(err?.message || 'Failed to reach meter.');
      setCommLogs((prev) => [
        { time, status: 'FAIL', durationMs, detail: err?.message || 'Request failed' },
        ...prev.slice(0, MAX_COMM_LOG_ROWS - 1),
      ]);
    }
  };

  useEffect(() => {
    apiService.getMeter(METER_ID).then((m) => setMeterStatus(m.status ?? null)).catch(() => {});
    poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleConnect = async () => {
    setConnecting(true);
    try {
      const res = await apiService.connectMeter(METER_ID);
      setMeterStatus(res.connected ? 'ONLINE' : 'ERROR');
    } catch (err: any) {
      setPollError(err?.message || 'Connect request failed.');
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    setConnecting(true);
    try {
      const res = await apiService.disconnectMeter(METER_ID);
      setMeterStatus(res.status);
    } catch (err: any) {
      setPollError(err?.message || 'Disconnect request failed.');
    } finally {
      setConnecting(false);
    }
  };

  const isDisconnected = pollError !== null;
  const showStale = isDisconnected && hasEverSucceeded.current;

  const voltage = findValue(readings, OBIS.voltage);
  const current = findValue(readings, OBIS.current);
  const frequency = findValue(readings, OBIS.frequency);
  const power = findValue(readings, OBIS.power);
  const energy = findValue(readings, OBIS.energy);
  const powerFactor = findValue(readings, OBIS.powerFactor);

  const dataSourceLabel =
    dataSource === 'mock' ? 'MOCK DATA' : dataSource === 'hardware' ? 'LIVE HARDWARE' : dataSource ? dataSource.toUpperCase() : 'UNKNOWN SOURCE';

  const cardStyle = (borderColor: string): React.CSSProperties => ({
    padding: '20px',
    borderLeft: `4px solid ${borderColor}`,
    opacity: showStale ? 0.5 : 1,
    transition: 'opacity 0.2s ease',
  });

  const renderCardValue = (value: string | null, unit: string) => {
    if (value === null) {
      return <span style={{ color: 'var(--text-muted)' }}>—</span>;
    }
    return (
      <>
        {value} <span style={{ fontSize: '1rem', color: 'var(--text-dim)' }}>{unit}</span>
      </>
    );
  };

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 className="section-title">Live Smart Meter Monitor</h2>
          <p className="section-sub">Real-time electrical telemetry polled via DLMS/COSEM HDLC optical head probe.</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {dataSource && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px', borderRadius: '20px', background: dataSource === 'mock' ? 'rgba(255,171,0,0.1)' : 'rgba(0,230,118,0.1)', border: `1px solid ${dataSource === 'mock' ? '#ffab00' : '#00e676'}` }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: dataSource === 'mock' ? '#ffab00' : '#00e676' }}>{dataSourceLabel}</span>
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 14px', borderRadius: '20px', background: isDisconnected ? 'rgba(255,23,68,0.1)' : 'rgba(0,242,254,0.1)', border: `1px solid ${isDisconnected ? '#ff1744' : 'var(--border-cyan)'}` }}>
            <Radio size={16} color={isDisconnected ? '#ff1744' : 'var(--accent-cyan)'} className={isDisconnected ? undefined : 'pulse-green'} />
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: isDisconnected ? '#ff1744' : 'var(--accent-cyan)' }}>
              {isDisconnected ? 'DISCONNECTED' : `POLLING EVERY ${POLL_INTERVAL_MS}ms`}
            </span>
          </div>

          {meterStatus && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px', borderRadius: '20px', background: 'rgba(148,163,184,0.1)', border: '1px solid var(--text-muted)' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>METER STATUS: {meterStatus}</span>
            </div>
          )}

          <button
            className="btn"
            disabled={connecting}
            onClick={handleConnect}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px', borderRadius: '8px', border: '1px solid #00e676', background: 'transparent', color: '#00e676', cursor: connecting ? 'not-allowed' : 'pointer' }}
          >
            <PlugZap size={14} /> Connect
          </button>
          <button
            className="btn"
            disabled={connecting}
            onClick={handleDisconnect}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px', borderRadius: '8px', border: '1px solid #ff1744', background: 'transparent', color: '#ff1744', cursor: connecting ? 'not-allowed' : 'pointer' }}
          >
            <Plug size={14} /> Disconnect
          </button>
        </div>
      </div>

      {isDisconnected && (
        <div className="glass-card" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: '10px', border: '1px solid #ff1744', background: 'rgba(255,23,68,0.08)' }}>
          <AlertTriangle size={18} color="#ff1744" />
          <div>
            <div style={{ fontWeight: 700, color: '#ff1744' }}>Connection lost — {pollError}</div>
            {showStale && lastUpdated && (
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Values below are STALE — last confirmed reading at {lastUpdated.toLocaleTimeString()}. Still retrying every {POLL_INTERVAL_MS}ms.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Telemetry Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
        <div className="glass-card" style={cardStyle('#00f2fe')}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '8px' }}>VOLTAGE L1</div>
          <div className="mono" style={{ fontSize: '2.2rem', fontWeight: 800, color: '#00f2fe' }}>{renderCardValue(voltage, findUnit(readings, OBIS.voltage, 'V'))}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>OBIS: {OBIS.voltage}</div>
        </div>

        <div className="glass-card" style={cardStyle('#00e676')}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '8px' }}>CURRENT L1</div>
          <div className="mono" style={{ fontSize: '2.2rem', fontWeight: 800, color: '#00e676' }}>{renderCardValue(current, findUnit(readings, OBIS.current, 'A'))}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>OBIS: {OBIS.current}</div>
        </div>

        <div className="glass-card" style={cardStyle('#ffab00')}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '8px' }}>FREQUENCY</div>
          <div className="mono" style={{ fontSize: '2.2rem', fontWeight: 800, color: '#ffab00' }}>{renderCardValue(frequency, findUnit(readings, OBIS.frequency, 'Hz'))}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>OBIS: {OBIS.frequency}</div>
        </div>

        <div className="glass-card" style={cardStyle('#4facfe')}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '8px' }}>ACTIVE POWER</div>
          <div className="mono" style={{ fontSize: '2.2rem', fontWeight: 800, color: '#4facfe' }}>{renderCardValue(power, findUnit(readings, OBIS.power, 'W'))}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>OBIS: {OBIS.power}</div>
        </div>

        <div className="glass-card" style={cardStyle('#7f00ff')}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '8px' }}>ACTIVE ENERGY (+A)</div>
          <div className="mono" style={{ fontSize: '1.8rem', fontWeight: 800, color: '#a7f3d0' }}>{renderCardValue(energy, findUnit(readings, OBIS.energy, 'kWh'))}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>OBIS: {OBIS.energy}</div>
        </div>

        <div className="glass-card" style={cardStyle('#e2e8f0')}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '8px' }}>POWER FACTOR</div>
          <div className="mono" style={{ fontSize: '2.2rem', fontWeight: 800, color: '#f1f5f9' }}>{renderCardValue(powerFactor, '')}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>OBIS: {OBIS.powerFactor}</div>
        </div>
      </div>

      {/* Communication Monitor Table */}
      <div className="glass-card" style={{ padding: '22px' }}>
        <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1rem', fontWeight: 600, marginBottom: '4px' }}>Communication Monitor Log</h3>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
          Client-side log of this browser tab's own poll requests — not a durable server record. Clears on page reload.
        </p>
        <table className="data-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Request</th>
              <th>Result</th>
              <th>Duration</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {commLogs.map((log, idx) => (
              <tr key={idx}>
                <td className="mono" style={{ color: 'var(--text-muted)' }}>{log.time}</td>
                <td className="mono" style={{ color: 'var(--accent-cyan)' }}>GET /meters/{METER_ID}/readings</td>
                <td className="mono" style={{ fontWeight: 600, color: log.status === 'PASS' ? 'var(--accent-green)' : '#ff1744' }}>{log.detail}</td>
                <td className="mono" style={{ color: 'var(--text-muted)' }}>{log.durationMs} ms</td>
                <td><span className={log.status === 'PASS' ? 'badge badge-pass' : 'badge badge-fail'}>{log.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
