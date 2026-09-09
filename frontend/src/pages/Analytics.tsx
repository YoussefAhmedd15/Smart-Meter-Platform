import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, CartesianGrid,
} from 'recharts';
import { apiService } from '../services/api';
import { AnalyticsOverview, AnalyticsFirmware, AnalyticsModel, AnalyticsTrend } from '../types';

const ttStyle = { background: '#0d1424', borderColor: 'var(--border-cyan)', color: '#fff', borderRadius: '8px', fontSize: '0.8rem' };

export const Analytics: React.FC = () => {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [firmwares, setFirmwares] = useState<AnalyticsFirmware[]>([]);
  const [models, setModels] = useState<AnalyticsModel[]>([]);
  const [trends, setTrends] = useState<AnalyticsTrend[]>([]);
  const [errorDist, setErrorDist] = useState<{ name: string; value: number; color: string }[]>([]);

  useEffect(() => {
    Promise.allSettled([
      apiService.getAnalyticsOverview(),
      apiService.getAnalyticsFirmware(),
      apiService.getAnalyticsModels(),
      apiService.getAnalyticsTrends(),
      apiService.getFailures(),
    ]).then(([resOverview, resFw, resModels, resTrends, resFailures]) => {
      if (resOverview.status === 'fulfilled') setOverview(resOverview.value);
      if (resFw.status === 'fulfilled') setFirmwares(resFw.value);
      if (resModels.status === 'fulfilled') setModels(resModels.value);
      if (resTrends.status === 'fulfilled') setTrends(resTrends.value);
      if (resFailures.status === 'fulfilled' && resFailures.value.length) {
        const counts: Record<string, number> = {};
        resFailures.value.forEach(f => {
          const type = f.error_type || f.error_code || 'UNKNOWN';
          counts[type] = (counts[type] || 0) + 1;
        });
        const colors = ['#ff1744', '#ffab00', '#00f2fe', '#9333ea', '#3b82f6'];
        const mapped = Object.entries(counts).map(([name, val], idx) => ({
          name,
          value: val,
          color: colors[idx % colors.length],
        }));
        if (mapped.length) setErrorDist(mapped);
      }
    });
  }, []);

  const barData = firmwares.map(f => ({
    firmware: f.firmware_version,
    failures: f.failure_count,
    passRate: f.pass_rate ?? 0,
  }));

  const lineData = trends.map(t => ({
    week: t.date,
    passRate: t.passRate ?? (t.passed + t.failed > 0 ? +(t.passed / (t.passed + t.failed) * 100).toFixed(1) : 0),
  }));

  const displayModels = models;

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
          {
            label: 'Avg Pass Rate',
            value: overview ? `${overview.overall_pass_rate ?? overview.pass_rate_percentage ?? 0}%` : '—',
            color: 'var(--accent-green)',
            trend: overview ? `${overview.total_test_executions ?? 0} total test runs` : 'Loading...',
          },
          {
            label: 'Total Failures',
            value: overview ? `${overview.failed_tests ?? 0}` : '—',
            color: 'var(--accent-red)',
            trend: 'across recorded test runs',
          },
          {
            label: 'Most Stable FW',
            value: overview?.firmware_stability || (firmwares[0]?.firmware_version ?? '—'),
            color: 'var(--accent-cyan)',
            trend: overview?.firmware_stability ? 'evaluated from test history' : 'no firmware data',
          },
          {
            label: 'Critical Failures',
            value: overview ? `${overview.critical_failures ?? 0}` : '—',
            color: 'var(--accent-amber)',
            trend: `${overview?.open_failures ?? 0} open defects`,
          },
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
            {barData.length > 0 ? (
              <ResponsiveContainer>
                <BarChart data={barData} margin={{ left: -10, right: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="firmware" stroke="#55657e" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#55657e" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={ttStyle} />
                  <Bar dataKey="failures" fill="#00f2fe" radius={[6, 6, 0, 0]} name="Failures" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No firmware failure records found.
              </div>
            )}
          </div>
        </div>

        <div className="glass-card" style={{ padding: '22px' }}>
          <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '0.95rem', fontWeight: 600, marginBottom: '16px' }}>
            Error Type Distribution
          </h3>
          <div style={{ width: '100%', height: 230 }}>
            {errorDist.length > 0 ? (
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
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No failure distribution data recorded in database.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Row 2: Pass Rate Trend + Model Table */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '20px' }}>

        <div className="glass-card" style={{ padding: '22px' }}>
          <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '0.95rem', fontWeight: 600, marginBottom: '16px' }}>
            Pass Rate Trend {lineData.length > 0 ? `(${lineData.length} Intervals)` : ''}
          </h3>
          <div style={{ width: '100%', height: 210 }}>
            {lineData.length > 0 ? (
              <ResponsiveContainer>
                <LineChart data={lineData} margin={{ left: -10, right: 4 }}>
                  <defs>
                    <linearGradient id="gLine" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#00f2fe" />
                      <stop offset="100%" stopColor="#00e676" />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="week" stroke="#55657e" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#55657e" tick={{ fontSize: 11 }} domain={[0, 100]} unit="%" />
                  <Tooltip contentStyle={ttStyle} formatter={(v: number) => [`${v}%`, 'Pass Rate']} />
                  <Line
                    type="monotone" dataKey="passRate"
                    stroke="url(#gLine)" strokeWidth={2.5}
                    dot={{ fill: '#00f2fe', strokeWidth: 0, r: 4 }}
                    activeDot={{ r: 6, fill: '#00e676' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No pass rate trend intervals available.
              </div>
            )}
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
              {displayModels.length > 0 ? (
                displayModels.map(m => {
                  const total = m.tests ?? 0;
                  const pct = total > 0 ? ((m.failures / total) * 100).toFixed(1) : (m.failures > 0 ? '100.0' : '0.0');
                  const color = parseFloat(pct) > 5 ? 'var(--accent-red)' : parseFloat(pct) > 2 ? 'var(--accent-amber)' : 'var(--accent-green)';
                  return (
                    <tr key={m.model}>
                      <td style={{ fontWeight: 600 }}>{m.model}</td>
                      <td className="mono" style={{ color: 'var(--text-muted)' }}>{total}</td>
                      <td className="mono" style={{ color: 'var(--accent-red)' }}>{m.failures}</td>
                      <td>
                        <span className="badge" style={{ background: `${color}18`, color, border: `1px solid ${color}44` }}>
                          {pct}%
                        </span>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '24px', fontSize: '0.85rem' }}>
                    No model failure data found in database.
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          <hr className="divider" />

          {/* Firmware pass rate table */}
          <h4 style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '10px' }}>
            Pass Rate by Firmware
          </h4>
          {barData.length > 0 ? (
            barData.map(f => (
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
            ))
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              No firmware pass rate data recorded.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

