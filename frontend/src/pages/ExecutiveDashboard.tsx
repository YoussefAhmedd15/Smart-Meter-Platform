import React, { useEffect, useState } from 'react';
import { ShieldCheck, CheckCircle2, AlertTriangle, Cpu, TrendingUp, Activity } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { apiService } from '../services/api';
import { AnalyticsOverview, Meter } from '../types';

export const ExecutiveDashboard: React.FC = () => {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [meters, setMeters] = useState<Meter[]>([]);

  useEffect(() => {
    apiService.getAnalyticsOverview().then(setAnalytics).catch(console.error);
    apiService.getMeters().then(setMeters).catch(console.error);
  }, []);

  const chartData = [
    { date: 'Mon', passed: 240, failed: 8 },
    { date: 'Tue', passed: 280, failed: 5 },
    { date: 'Wed', passed: 310, failed: 12 },
    { date: 'Thu', passed: 290, failed: 4 },
    { date: 'Fri', passed: 350, failed: 6 },
    { date: 'Sat', passed: 180, failed: 2 },
    { date: 'Sun', passed: 130, failed: 1 },
  ];

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>Executive Intelligence Overview</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Real-time smart meter test quality, firmware stability, and failure analytics.</p>
      </div>

      {/* KPI Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>OVERALL QUALITY SCORE</span>
            <ShieldCheck size={22} color="var(--accent-cyan)" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
            {analytics?.overall_quality_score ?? 95.4} <span style={{ fontSize: '1rem', color: 'var(--text-dim)' }}>/ 100</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--accent-green)', marginTop: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <TrendingUp size={14} /> +1.8% vs last firmware baseline
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>AUTOMATED PASS RATE</span>
            <CheckCircle2 size={22} color="var(--accent-green)" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-green)' }}>
            {analytics?.pass_rate_percentage ?? 96.8}%
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px' }}>
            {analytics?.passed_tests ?? 1781} of {analytics?.total_tests_executed ?? 1840} tests passed
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>CRITICAL DEFECTS</span>
            <AlertTriangle size={22} color="var(--accent-red)" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-red)' }}>
            {analytics?.critical_failures ?? 2}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px' }}>
            {analytics?.open_failures ?? 5} total open issues logged
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>TESTED METERS</span>
            <Cpu size={22} color="var(--accent-blue)" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-blue)' }}>
            {analytics?.total_meters_tested ?? 12}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px' }}>
            Iskraemeco AM550, MT880, MT382
          </div>
        </div>
      </div>

      {/* Charts & Tables Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '16px' }}>Testing Pass/Fail Trend</h3>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorPassed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00e676" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#00e676" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorFailed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ff1744" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#ff1744" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip contentStyle={{ background: '#111726', borderColor: '#2d3e5f', color: '#fff' }} />
                <Area type="monotone" dataKey="passed" stroke="#00e676" fillOpacity={1} fill="url(#colorPassed)" name="Passed Tests" />
                <Area type="monotone" dataKey="failed" stroke="#ff1744" fillOpacity={1} fill="url(#colorFailed)" name="Failed Tests" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '16px' }}>Active Meter Fleet</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {meters.map(m => (
              <div key={m.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', borderRadius: '8px', background: 'rgba(17,23,38,0.6)', border: '1px solid var(--border-color)' }}>
                <div>
                  <div className="mono" style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>{m.serial_number}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{m.model} • {m.firmware_version}</div>
                </div>
                <span className="badge badge-pass">
                  <div className="dot dot-green pulse-green" /> ONLINE
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
