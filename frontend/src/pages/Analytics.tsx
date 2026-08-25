import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

export const Analytics: React.FC = () => {
  const firmwareData = [
    { firmware: 'v3.12.1', failures: 18, passRate: 91.2 },
    { firmware: 'v3.13.0', failures: 12, passRate: 94.5 },
    { firmware: 'v3.14.2', failures: 4, passRate: 98.1 },
    { firmware: 'v3.15.0-RC1', failures: 1, passRate: 99.2 },
  ];

  const modelData = [
    { model: 'AM550-TD1', failures: 14 },
    { model: 'MT880-D2', failures: 8 },
    { model: 'MT382-T1', failures: 22 },
  ];

  const errorDist = [
    { name: 'TIMEOUT', value: 45, color: '#ff1744' },
    { name: 'READ_FAILED', value: 30, color: '#ffab00' },
    { name: 'SNRM_FAILED', value: 15, color: '#00f2fe' },
    { name: 'DECODING_ERROR', value: 10, color: '#7f00ff' },
  ];

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0 }}>Smart Meter Analytics & QA Dashboard</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Failure rate breakdown by firmware build, meter model, and error classification distribution.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '16px' }}>Failure Count by Firmware Version</h3>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={firmwareData}>
                <XAxis dataKey="firmware" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip contentStyle={{ background: '#111726', borderColor: '#2d3e5f', color: '#fff' }} />
                <Bar dataKey="failures" fill="#00f2fe" radius={[6, 6, 0, 0]} name="Failures" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '16px' }}>Error Type Distribution</h3>
          <div style={{ width: '100%', height: 260, display: 'flex', alignItems: 'center' }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={errorDist} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={85} label>
                  {errorDist.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#111726', borderColor: '#2d3e5f', color: '#fff' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
