import React, { useEffect, useState } from 'react';
import {
  ShieldCheck, CheckCircle2, AlertTriangle, Cpu,
  TrendingUp, Activity,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import { apiService } from '../services/api';
import { AnalyticsOverview, AnalyticsTrend, Meter } from '../types';

const customTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: '#0d1424', border: '1px solid var(--border-cyan)',
      borderRadius: '8px', padding: '10px 14px', fontSize: '0.82rem',
    }}>
      <div style={{ color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600 }}>{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} style={{ color: p.color, display: 'flex', gap: '8px', justifyContent: 'space-between' }}>
          <span>{p.name}</span>
          <span style={{ fontWeight: 700 }}>{p.value}</span>
        </div>
      ))}
    </div>
  );
};

export const ExecutiveDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [meters, setMeters]       = useState<Meter[]>([]);
  const [trends, setTrends]       = useState<AnalyticsTrend[]>([]);
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    Promise.allSettled([
      apiService.getAnalyticsOverview(),
      apiService.getMeters(),
      apiService.getAnalyticsTrends(),
    ]).then(([a, m, t]) => {
      if (a.status === 'fulfilled') setAnalytics(a.value);
      if (m.status === 'fulfilled') setMeters(m.value);
      if (t.status === 'fulfilled') setTrends(t.value);
      setLoading(false);
    });
  }, []);

  const totalExecutions = analytics?.total_test_executions ?? analytics?.total_tests_executed ?? 0;
  const passRate = analytics?.overall_pass_rate ?? analytics?.pass_rate_percentage ?? 0;
  const qualityScore = analytics?.quality_score ?? analytics?.overall_quality_score ?? 0;
  const passedTests = analytics?.passed_tests ?? 0;
  const criticalDefects = analytics?.critical_failures ?? 0;
  const openDefects = analytics?.open_failures ?? 0;
  const metersTested = analytics?.total_meters_tested ?? meters.length;

  const kpis = [
    {
      label: 'Overall Quality Score',
      value: analytics ? `${qualityScore}` : '—',
      unit: analytics ? '/ 100' : '',
      color: 'var(--accent-cyan)',
      icon: ShieldCheck,
      trend: analytics ? `${analytics.firmware_stability ?? 'STABLE'} quality status` : 'Calculating…',
      trendUp: qualityScore >= 80,
    },
    {
      label: 'Automated Pass Rate',
      value: analytics ? `${passRate}%` : '—',
      unit: '',
      color: 'var(--accent-green)',
      icon: CheckCircle2,
      trend: analytics ? `${passedTests} / ${totalExecutions} tests passed` : 'Calculating…',
      trendUp: passRate >= 90,
    },
    {
      label: 'Critical Defects',
      value: analytics ? `${criticalDefects}` : '0',
      unit: '',
      color: criticalDefects > 0 ? 'var(--accent-red)' : 'var(--accent-green)',
      icon: AlertTriangle,
      trend: `${openDefects} open issues logged`,
      trendUp: criticalDefects === 0,
    },
    {
      label: 'Meters Tested',
      value: analytics ? `${metersTested}` : `${meters.length}`,
      unit: '',
      color: 'var(--accent-blue)',
      icon: Cpu,
      trend: meters.length > 0 ? `${meters.length} meter(s) registered` : 'No meters registered',
      trendUp: meters.length > 0,
    },
  ];

  const chartData = trends.map(t => ({
    day: t.date,
    passed: t.passed,
    failed: t.failed,
  }));

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '24px' }}>

      {/* ── Page Header ── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <h2 className="section-title">Executive Intelligence Dashboard</h2>
          <p className="section-sub">Real-time smart meter quality, firmware stability, and failure analytics from database.</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div className="dot dot-green pulse-green" />
          <span style={{ fontSize: '0.78rem', color: 'var(--accent-green)', fontWeight: 600 }}>
            LIVE DATABASE METRICS
          </span>
        </div>
      </div>

      {/* ── KPI Grid ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        {kpis.map((kpi) => {
          const Icon = kpi.icon;
          return (
            <div key={kpi.label} className="stat-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <span className="label">{kpi.label}</span>
                <div style={{
                  width: '36px', height: '36px', borderRadius: '9px',
                  background: `${kpi.color}18`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Icon size={18} color={kpi.color} />
                </div>
              </div>
              <div style={{ fontFamily: 'var(--font-head)', fontSize: '2.2rem', fontWeight: 800, color: kpi.color, lineHeight: 1 }}>
                {loading ? <span className="skeleton" style={{ display: 'block', width: '80px', height: '36px' }} /> : kpi.value}
                {kpi.unit && <span style={{ fontSize: '1rem', color: 'var(--text-dim)', marginLeft: '4px' }}>{kpi.unit}</span>}
              </div>
              <div style={{
                fontSize: '0.75rem',
                color: kpi.trendUp ? 'var(--accent-green)' : 'var(--text-muted)',
                marginTop: '10px',
                display: 'flex', alignItems: 'center', gap: '4px',
              }}>
                {kpi.trendUp ? <TrendingUp size={13} /> : <Activity size={13} />}
                {kpi.trend}
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Charts ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>

        {/* Area Chart */}
        <div className="glass-card" style={{ padding: '22px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
            <div>
              <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1rem', fontWeight: 600, margin: 0 }}>
                Weekly Test Pass / Fail Trend
              </h3>
              <p style={{ fontSize: '0.76rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                Historical test executions recorded in database
              </p>
            </div>
            <span className="badge badge-pass">
              <TrendingUp size={12} /> {analytics?.firmware_stability ?? 'STABLE'}
            </span>
          </div>
          {chartData.length > 0 ? (
            <div style={{ width: '100%', height: 240 }}>
              <ResponsiveContainer>
                <AreaChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: -10 }}>
                  <defs>
                    <linearGradient id="gPassed" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#00e676" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#00e676" stopOpacity={0}    />
                    </linearGradient>
                    <linearGradient id="gFailed" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#ff1744" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#ff1744" stopOpacity={0}    />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="day" stroke="#55657e" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#55657e" tick={{ fontSize: 11 }} />
                  <Tooltip content={customTooltip} />
                  <Area type="monotone" dataKey="passed" name="Passed" stroke="#00e676" strokeWidth={2} fill="url(#gPassed)" />
                  <Area type="monotone" dataKey="failed"  name="Failed"  stroke="#ff1744" strokeWidth={2} fill="url(#gFailed)"  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)', fontSize: '0.86rem' }}>
              No test execution trends logged in database yet.
            </div>
          )}
        </div>

        {/* Active Meter Fleet */}
        <div className="glass-card" style={{ padding: '22px', display: 'flex', flexDirection: 'column', gap: '0' }}>
          <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1rem', fontWeight: 600, margin: 0 }}>
              Active Meter Fleet
            </h3>
            <span className="badge badge-info">{meters.length} Registered</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, overflowY: 'auto' }}>
            {meters.length === 0 && loading && [1, 2, 3].map(i => (
              <div key={i} className="skeleton" style={{ height: '54px', borderRadius: '8px' }} />
            ))}
            {meters.length === 0 && !loading && (
              <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.84rem' }}>
                No meters found in database.
              </div>
            )}
            {meters.map(m => (
              <div key={m.meter_id ?? m.id} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '10px 14px', borderRadius: '9px',
                background: 'rgba(13,20,36,0.7)', border: '1px solid var(--border-color)',
                transition: 'var(--transition-fast)',
              }}>
                <div>
                  <div className="mono" style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                    {m.meter_number || m.serial_number}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                    {m.meter_model || m.model} · {m.firmware_version || 'FW: N/A'}
                  </div>
                </div>
                <div className={`badge ${m.status === 'ONLINE' ? 'badge-pass' : 'badge-dim'}`}>
                  <div className={`dot ${m.status === 'ONLINE' ? 'dot-green pulse-green' : 'dot-red'}`} /> {m.status || 'UNKNOWN'}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Summary Row ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        {[
          { label: 'Total Test Executions', value: totalExecutions, color: 'var(--accent-cyan)', icon: '🔬' },
          { label: 'Avg Execution Time',    value: `${analytics?.avg_duration_seconds ?? analytics?.average_duration_seconds ?? 0}s`, color: 'var(--accent-blue)', icon: '⚡' },
          { label: 'Firmware Stability',    value: analytics?.firmware_stability ?? 'STABLE', color: 'var(--accent-green)', icon: '🛡️' },
        ].map(s => (
          <div key={s.label} className="glass-card" style={{ padding: '18px 20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontSize: '1.6rem' }}>{s.icon}</span>
            <div>
              <div className="label">{s.label}</div>
              <div style={{ fontFamily: 'var(--font-head)', fontSize: '1.4rem', fontWeight: 700, color: s.color, marginTop: '2px' }}>
                {s.value}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
