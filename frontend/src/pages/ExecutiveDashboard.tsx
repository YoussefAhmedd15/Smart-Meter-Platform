import React, { useEffect, useState } from 'react';
import {
  ShieldCheck, CheckCircle2, AlertTriangle, Cpu,
  TrendingUp, TrendingDown, Activity, Zap,
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import { apiService } from '../services/api';
import { AnalyticsOverview, Meter } from '../types';

const weekData = [
  { day: 'Mon', passed: 240, failed: 8 },
  { day: 'Tue', passed: 285, failed: 5 },
  { day: 'Wed', passed: 310, failed: 12 },
  { day: 'Thu', passed: 295, failed: 4 },
  { day: 'Fri', passed: 358, failed: 6 },
  { day: 'Sat', passed: 182, failed: 2 },
  { day: 'Sun', passed: 130, failed: 1 },
];

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
  const [loading, setLoading]     = useState(true);

  useEffect(() => {
    Promise.allSettled([
      apiService.getAnalyticsOverview(),
      apiService.getMeters(),
    ]).then(([a, m]) => {
      if (a.status === 'fulfilled') setAnalytics(a.value);
      if (m.status === 'fulfilled') setMeters(m.value);
      setLoading(false);
    });
  }, []);

  const kpis = [
    {
      label: 'Overall Quality Score',
      value: analytics ? `${analytics.overall_quality_score}` : '95.4',
      unit: '/ 100',
      color: 'var(--accent-cyan)',
      icon: ShieldCheck,
      trend: '+1.8% vs last firmware',
      trendUp: true,
    },
    {
      label: 'Automated Pass Rate',
      value: analytics ? `${analytics.pass_rate_percentage}%` : '96.8%',
      unit: '',
      color: 'var(--accent-green)',
      icon: CheckCircle2,
      trend: `${analytics?.passed_tests ?? 1781} / ${analytics?.total_tests_executed ?? 1840} tests`,
      trendUp: true,
    },
    {
      label: 'Critical Defects',
      value: analytics ? `${analytics.critical_failures}` : '2',
      unit: '',
      color: 'var(--accent-red)',
      icon: AlertTriangle,
      trend: `${analytics?.open_failures ?? 5} open issues logged`,
      trendUp: false,
    },
    {
      label: 'Meters Tested',
      value: analytics ? `${analytics.total_meters_tested}` : '12',
      unit: '',
      color: 'var(--accent-blue)',
      icon: Cpu,
      trend: 'AM550, MT880, MT382',
      trendUp: true,
    },
  ];

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '24px' }}>

      {/* ── Page Header ── */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <h2 className="section-title">Executive Intelligence Dashboard</h2>
          <p className="section-sub">Real-time smart meter quality, firmware stability, and failure analytics.</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div className="dot dot-green pulse-green" />
          <span style={{ fontSize: '0.78rem', color: 'var(--accent-green)', fontWeight: 600 }}>
            LIVE DATA
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
                Last 7 days · automated DLMS test executions
              </p>
            </div>
            <span className="badge badge-pass">
              <TrendingUp size={12} /> Stable
            </span>
          </div>
          <div style={{ width: '100%', height: 240 }}>
            <ResponsiveContainer>
              <AreaChart data={weekData} margin={{ top: 4, right: 4, bottom: 0, left: -10 }}>
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
        </div>

        {/* Active Meter Fleet */}
        <div className="glass-card" style={{ padding: '22px', display: 'flex', flexDirection: 'column', gap: '0' }}>
          <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1rem', fontWeight: 600, margin: 0 }}>
              Active Meter Fleet
            </h3>
            <span className="badge badge-info">{meters.length} Online</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, overflowY: 'auto' }}>
            {meters.length === 0 && loading && [1, 2, 3].map(i => (
              <div key={i} className="skeleton" style={{ height: '54px', borderRadius: '8px' }} />
            ))}
            {meters.map(m => (
              <div key={m.id} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '10px 14px', borderRadius: '9px',
                background: 'rgba(13,20,36,0.7)', border: '1px solid var(--border-color)',
                transition: 'var(--transition-fast)',
              }}>
                <div>
                  <div className="mono" style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                    {m.serial_number}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                    {m.model} · {m.firmware_version}
                  </div>
                </div>
                <div className="badge badge-pass">
                  <div className="dot dot-green pulse-green" /> ONLINE
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Summary Row ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        {[
          { label: 'Total Test Runs',      value: analytics?.total_test_runs ?? 148, color: 'var(--accent-cyan)', icon: '🔬' },
          { label: 'Avg Execution Time',   value: `${analytics?.average_duration_seconds ?? 4.2}s`, color: 'var(--accent-blue)', icon: '⚡' },
          { label: 'Firmware Stability',   value: analytics?.firmware_stability ?? 'STABLE', color: 'var(--accent-green)', icon: '🛡️' },
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
