import React, { useEffect, useState } from 'react';
import { Cpu, AlertTriangle } from 'lucide-react';
import { apiService } from '../services/api';
import { MeterProfile as MeterProfileData } from '../types';

const METER_ID = 1;

function formatTimestamp(iso: string | null): string {
  if (!iso) return 'Never';
  return new Date(iso).toLocaleString();
}

export const MeterProfile: React.FC = () => {
  const [profile, setProfile] = useState<MeterProfileData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiService
      .getMeterProfile(METER_ID)
      .then((data) => {
        setProfile(data);
        setError(null);
      })
      .catch((err: any) => {
        setError(err?.message || 'Failed to load meter profile.');
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '28px' }}>
        <p style={{ color: 'var(--text-muted)' }}>Loading meter profile…</p>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div style={{ padding: '28px' }}>
        <div className="glass-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '10px', border: '1px solid #ff1744', background: 'rgba(255,23,68,0.08)' }}>
          <AlertTriangle size={18} color="#ff1744" />
          <span style={{ color: '#ff1744', fontWeight: 600 }}>Could not load meter profile — {error}</span>
        </div>
      </div>
    );
  }

  // Honest status: never claim CERTIFIED unless is_certified is actually
  // true. Three real states, not two glossed-over ones.
  let statusLabel: string;
  let statusDotClass: string;
  if (profile.is_certified) {
    statusLabel = 'ONLINE & CERTIFIED';
    statusDotClass = 'dot-green pulse-green';
  } else if (profile.is_online) {
    statusLabel = 'ONLINE — NOT CERTIFIED';
    statusDotClass = 'dot-amber';
  } else {
    statusLabel = 'OFFLINE / STALE';
    statusDotClass = 'dot-red';
  }
  const badgeClass = profile.is_certified ? 'badge-pass' : profile.is_online ? 'badge-warning' : 'badge-fail';

  const lastRun = profile.last_test_run;

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
      <div>
        <h2 className="section-title">Digital Meter Profile</h2>
        <p className="section-sub">Real hardware identity, testing history, and connectivity status from the backend.</p>
      </div>

      {/* Identity Card */}
      <div className="glass-card" style={{ padding: '24px', display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px', alignItems: 'center' }}>
        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(17,23,38,0.8)', border: '1px solid var(--border-cyan)', textAlign: 'center' }}>
          <Cpu size={48} color="var(--accent-cyan)" style={{ marginBottom: '12px' }} />
          <h3 className="mono" style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>{profile.meter_number}</h3>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            {profile.manufacturer} {profile.meter_model}
          </div>
          <div className={`badge ${badgeClass}`} style={{ marginTop: '12px' }}>
            <div className={`dot ${statusDotClass}`} /> {statusLabel}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '10px' }}>
            Last contact: {formatTimestamp(profile.last_seen)}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>MANUFACTURER</span>
            <div style={{ fontSize: '1.1rem', fontWeight: 600, marginTop: '2px' }}>{profile.manufacturer || '—'}</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>INSTALLED FIRMWARE</span>
            <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--accent-cyan)', marginTop: '2px' }}>{profile.firmware_version || 'Unknown'}</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>HARDWARE REVISION</span>
            <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 600, marginTop: '2px' }}>{profile.hardware_revision || '—'}</div>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>MEDIA INTERFACE</span>
            <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--accent-green)', marginTop: '2px' }}>{profile.communication_interface || '—'}</div>
          </div>
        </div>
      </div>

      {/* Profile Metrics Grid — no fabricated "Quality Score" / metrology
          compliance card: neither has any real backing data, so it's
          dropped entirely rather than replaced with another fake claim. */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>TOTAL TEST RUNS</div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#f1f5f9', marginTop: '4px' }}>{profile.total_test_runs}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>{profile.total_readings_count} OBIS Reads Performed</div>
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>HISTORICAL PASS RATE</div>
          {profile.total_test_runs > 0 ? (
            <>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-green)', marginTop: '4px' }}>{profile.pass_rate}%</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>{profile.failures_resolved_count} failure(s) resolved</div>
            </>
          ) : (
            <div style={{ fontSize: '1rem', color: 'var(--text-muted)', marginTop: '12px' }}>No test runs yet</div>
          )}
        </div>

        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>LAST TEST RUN</div>
          {lastRun ? (
            <>
              <div style={{ fontSize: '1.2rem', fontWeight: 700, color: lastRun.status === 'COMPLETED' ? 'var(--accent-green)' : 'var(--accent-red)', marginTop: '8px' }}>
                {lastRun.status === 'COMPLETED' ? 'Passed' : lastRun.status} ({(lastRun.duration_seconds ?? 0).toFixed(2)}s)
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                {formatTimestamp(lastRun.finished_at || lastRun.started_at)}
              </div>
            </>
          ) : (
            <div style={{ fontSize: '1rem', color: 'var(--text-muted)', marginTop: '12px' }}>This meter has never been tested</div>
          )}
        </div>
      </div>
    </div>
  );
};
