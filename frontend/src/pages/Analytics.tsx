import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, CartesianGrid,
} from 'recharts';
import { TrendingDown, TrendingUp, AlertTriangle } from 'lucide-react';

const firmwareData = [
  { firmware: 'v3.12.1', failures: 18, passRate: 91.2 },
  { firmware: 'v3.13.0', failures: 12, passRate: 94.5 },
  { firmware: 'v3.14.2', failures: 4,  passRate: 98.1 },
  { firmware: 'v3.15.0-RC1', failures: 1, passRate: 99.2 },
];

const modelData = [
  { model: 'AM550-TD1', failures: 14, tests: 580 },
  { model: 'MT880-D2',  failures: 8,  tests: 420 },
  { model: 'MT382-T1',  failures: 22, tests: 310 },
];

const errorDist = [
  { name: 'TIMEOUT',       value: 45, color: '#ff1744' },
  { name: 'READ_FAILED',   value: 30, color: '#ffab00' },
  { name: 'SNRM_FAILED',   value: 15, color: '#00f2fe' },
  { name: 'DECODING_ERROR',value: 10, color: '#9333ea' },
];

const trendData = [
  { week: 'Wk 1', passRate: 91.2 },
  { week: 'Wk 2', passRate: 93.1 },
  { week: 'Wk 3', passRate: 92.5 },
  { week: 'Wk 4', passRate: 95.8 },
  { week: 'Wk 5', passRate: 94.0 },
  { week: 'Wk 6', passRate: 97.2 },
  { week: 'Wk 7', passRate: 98.1 },
  { week: 'Wk 8', passRate: 99.2 },
];

const ttStyle = { background: '#0d1424', borderColor: 'var(--border-cyan)', color: '#fff', borderRadius: '8px', fontSize: '0.8rem' };

export const Analytics: React.FC = () => {
  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '24px' }}>

      {/* Header */}
      <div>
        <h2 className="section-title">Smart Meter Analytics &amp; QA Dashboard</h2>
        <p className="section-sub">
          Failure rate breakdown by firmware build, meter model, error classification, and long-term pass rate trends.
        </p>
      </div>

      {/* KPI Strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px' }}>
        {[
          { label: 'Avg Pass Rate',      value: '95.8%', color: 'var(--accent-green)', icon: '✓', trend: '+1.4% this month' },
          { label: 'Total Failures',     value: '35',    color: 'var(--accent-red)',   icon: '✕', trend: 'across all firmware' },
          { label: 'Most Stable FW',     value: 'v3.15.0-RC1', color: 'var(--accent-cyan)', icon: '🛡', trend: '99.2% pass rate' },
          { label: 'Highest Risk Model', value: 'MT382-T1', color: 'var(--accent-amber)', icon: '⚠', trend: '22 recorded failures' },
        ].map(k => (
          <div key={k.label} className="stat-card">
            <div className="label">{k.label}</div>
            <div style={{ fontFamily: 'var(--font-head)', fontSize: '1.8rem', fontWeight: 800, color: k.color, margin: '6px 0 4px' }}>
              {k.value}
            </div>
            <div style={{ fontSize: '0.73rem', color: 'var(--text-dim)' }}>{k.trend}</div>
          </div>
        ))}
      </div>

      {/* Row 1: Bar + Pie */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>

        <div className="glass-card" style={{ padding: '22px' }}>
          <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '0.95rem', fontWeight: 600, marginBottom: '16px' }}>
            Failure Count by Firmware Version
          </h3>
          <div style={{ width: '100%', height: 230 }}>
            <ResponsiveContainer>
              <BarChart data={firmwareData} margin={{ left: -10, right: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="firmware" stroke="#55657e" tick={{ fontSize: 11 }} />
                <YAxis stroke="#55657e" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={ttStyle} />
                <Bar dataKey="failures" fill="#00f2fe" radius={[6, 6, 0, 0]} name="Failures" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '22px' }}>
          <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '0.95rem', fontWeight: 600, marginBottom: '16px' }}>
            Error Type Distribution
          </h3>
          <div style={{ width: '100%', height: 230 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={errorDist} dataKey="value" nameKey="name"
                  cx="50%" cy="45%" outerRadius={80} innerRadius={40}
                  paddingAngle={3}
                >
                  {errorDist.map((e, i) => <Cell key={i} fill={e.color} />)}
                </Pie>
                <Tooltip contentStyle={ttStyle} />
                <Legend
                  wrapperStyle={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}
                  iconType="circle" iconSize={8}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Row 2: Pass Rate Trend + Model Table */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '20px' }}>

        <div className="glass-card" style={{ padding: '22px' }}>
          <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '0.95rem', fontWeight: 600, marginBottom: '16px' }}>
            Pass Rate Trend (8 Weeks)
          </h3>
          <div style={{ width: '100%', height: 210 }}>
            <ResponsiveContainer>
              <LineChart data={trendData} margin={{ left: -10, right: 4 }}>
                <defs>
                  <linearGradient id="gLine" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%"   stopColor="#00f2fe" />
                    <stop offset="100%" stopColor="#00e676" />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="week" stroke="#55657e" tick={{ fontSize: 11 }} />
                <YAxis stroke="#55657e" tick={{ fontSize: 11 }} domain={[88, 100]} unit="%" />
                <Tooltip contentStyle={ttStyle} formatter={(v: number) => [`${v}%`, 'Pass Rate']} />
                <Line
                  type="monotone" dataKey="passRate"
                  stroke="url(#gLine)" strokeWidth={2.5}
                  dot={{ fill: '#00f2fe', strokeWidth: 0, r: 4 }}
                  activeDot={{ r: 6, fill: '#00e676' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '22px' }}>
          <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '0.95rem', fontWeight: 600, marginBottom: '16px' }}>
            Failure Rate by Meter Model
          </h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Tests</th>
                <th>Failures</th>
                <th>Fail %</th>
              </tr>
            </thead>
            <tbody>
              {modelData.map(m => {
                const pct = ((m.failures / m.tests) * 100).toFixed(1);
                const color = parseFloat(pct) > 5 ? 'var(--accent-red)' : parseFloat(pct) > 2 ? 'var(--accent-amber)' : 'var(--accent-green)';
                return (
                  <tr key={m.model}>
                    <td style={{ fontWeight: 600 }}>{m.model}</td>
                    <td className="mono" style={{ color: 'var(--text-muted)' }}>{m.tests}</td>
                    <td className="mono" style={{ color: 'var(--accent-red)' }}>{m.failures}</td>
                    <td>
                      <span className="badge" style={{ background: `${color}18`, color, border: `1px solid ${color}44` }}>
                        {pct}%
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <hr className="divider" />

          {/* Firmware pass rate table */}
          <h4 style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '10px' }}>
            Pass Rate by Firmware
          </h4>
          {firmwareData.map(f => (
            <div key={f.firmware} style={{ marginBottom: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: '4px' }}>
                <span className="mono" style={{ color: 'var(--text-muted)' }}>{f.firmware}</span>
                <span style={{ fontWeight: 700, color: f.passRate >= 97 ? 'var(--accent-green)' : f.passRate >= 93 ? 'var(--accent-cyan)' : 'var(--accent-amber)' }}>
                  {f.passRate}%
                </span>
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{
                    width: `${f.passRate}%`,
                    background: f.passRate >= 97 ? 'linear-gradient(90deg, #00e676, #00b894)' : 'linear-gradient(90deg, #00f2fe, #4facfe)',
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
