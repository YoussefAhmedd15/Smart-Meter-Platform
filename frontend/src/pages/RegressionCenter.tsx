import React, { useState, useEffect } from 'react';
import { GitCompare, ArrowRight, CheckCircle2, XCircle, TrendingUp, RefreshCw } from 'lucide-react';
import { apiService } from '../services/api';
import { RegressionComparison } from '../types';

export const RegressionCenter: React.FC = () => {
  const [firmwares, setFirmwares] = useState<string[]>([]);
  const [fwLoading, setFwLoading] = useState(true);
  const [fwError, setFwError] = useState<string | null>(null);
  const [fwA, setFwA] = useState('');
  const [fwB, setFwB] = useState('');
  const [comparison, setComparison] = useState<RegressionComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [compareError, setCompareError] = useState<string | null>(null);

  useEffect(() => {
    setFwLoading(true);
    setFwError(null);
    apiService.getAnalyticsFirmware()
      .then(res => {
        const versions = Array.from(
          new Set(
            res
              .map(f => f.firmware_version)
              .filter((v): v is string => Boolean(v && v.trim()))
          )
        );
        setFirmwares(versions);
        if (versions.length > 0) {
          setFwA(versions[0]);
          setFwB(versions.length > 1 ? versions[1] : versions[0]);
        }
      })
      .catch(err => {
        console.error('Failed to load firmwares', err);
        setFwError('Could not load firmware versions from backend.');
      })
      .finally(() => setFwLoading(false));
  }, []);

  const handleCompare = async () => {
    if (!fwA || !fwB) return;
    try {
      setLoading(true);
      setCompareError(null);
      const res = await apiService.compareRegression(fwA, fwB);
      setComparison(res);
    } catch (err: any) {
      console.error('Failed to compare regression', err);
      setCompareError(err?.message || 'Failed to compare regression between selected firmware versions.');
      setComparison(null);
    } finally {
      setLoading(false);
    }
  };

  const passRateA = comparison
    ? (typeof comparison.firmware_a === 'object' ? comparison.firmware_a.pass_rate : (comparison.pass_rate_a ?? 0))
    : 0;

  const passRateB = comparison
    ? (typeof comparison.firmware_b === 'object' ? comparison.firmware_b.pass_rate : (comparison.pass_rate_b ?? 0))
    : 0;

  const delta = comparison?.pass_rate_delta ?? +(passRateB - passRateA).toFixed(1);
  const deltaStr = `${delta >= 0 ? '+' : ''}${delta}%`;

  const fixedList: string[] = comparison?.comparison?.fixed_issues_list ?? [];

  const newFailuresList: string[] = comparison?.regressed_tests && comparison.regressed_tests.length > 0
    ? comparison.regressed_tests.map(t => t.test_name)
    : (comparison?.comparison?.new_failures_list ?? []);

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 className="section-title">Firmware Regression Comparison Center</h2>
        <p className="section-sub">Compare testing pass rates, fixed defects, and new regressions between firmware releases.</p>
      </div>

      {/* Selectors */}
      <div className="glass-card" style={{ padding: '22px' }}>
        {fwLoading ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)', padding: '8px 0' }}>
            <RefreshCw size={16} className="spin" />
            <span>Loading firmware releases from database…</span>
          </div>
        ) : fwError ? (
          <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem' }}>
            {fwError}
          </div>
        ) : firmwares.length === 0 ? (
          <div style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>
            No firmware records registered in database yet.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr auto', gap: '16px', alignItems: 'end' }}>
            <div>
              <label className="form-label">Baseline Firmware (A)</label>
              <select className="form-select" value={fwA} onChange={e => setFwA(e.target.value)}>
                {firmwares.map(v => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>

            <ArrowRight size={24} color="var(--accent-cyan)" />

            <div>
              <label className="form-label">Target Firmware (B)</label>
              <select className="form-select" value={fwB} onChange={e => setFwB(e.target.value)}>
                {firmwares.map(v => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>

            <button className="btn-cyan" onClick={handleCompare} disabled={loading || !fwA || !fwB}>
              {loading ? <RefreshCw size={16} className="spin" /> : <GitCompare size={16} />}
              {loading ? 'Comparing...' : 'Run Regression Comparison'}
            </button>
          </div>
        )}
      </div>

      {compareError && (
        <div className="alert-banner danger">
          <XCircle size={18} style={{ flexShrink: 0 }} />
          <span>{compareError}</span>
        </div>
      )}

      {/* Comparison Outcome */}
      {!comparison ? (
        <div className="glass-card" style={{ padding: '40px 24px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <GitCompare size={36} color="var(--accent-cyan)" style={{ margin: '0 auto 12px', opacity: 0.5 }} />
          <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#fff', margin: '0 0 6px' }}>
            Ready for Comparison
          </h3>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-dim)', maxWidth: '420px', margin: '0 auto' }}>
            Select baseline and target firmware versions above and click &quot;Run Regression Comparison&quot; to analyze pass rates and defect regressions.
          </p>
        </div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr 1fr', gap: '20px' }}>
            {/* Firmware A */}
            <div className="glass-card" style={{ padding: '20px' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>BASELINE FIRMWARE A</div>
              <h3 className="mono" style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-muted)', marginTop: '4px' }}>{fwA}</h3>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#f1f5f9', marginTop: '12px' }}>{passRateA}%</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Baseline Pass Rate</div>
            </div>

            {/* Delta Highlight */}
            <div className="glass-card" style={{ padding: '20px', border: '1px solid var(--border-cyan)', textAlign: 'center' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>REGRESSION SUMMARY OUTCOME</div>
              <div style={{
                fontSize: '2.4rem', fontWeight: 800,
                color: delta >= 0 ? 'var(--accent-green)' : 'var(--accent-red)',
                marginTop: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
              }}>
                <TrendingUp size={28} /> {deltaStr}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginTop: '8px' }}>
                <strong>{fixedList.length} Issues Fixed</strong> • <span style={{ color: 'var(--accent-red)' }}>{newFailuresList.length} New Failures</span>
              </div>
            </div>

            {/* Firmware B */}
            <div className="glass-card" style={{ padding: '20px', borderLeft: '4px solid var(--accent-green)' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--accent-green)' }}>TARGET FIRMWARE B</div>
              <h3 className="mono" style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-green)', marginTop: '4px' }}>{fwB}</h3>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-green)', marginTop: '12px' }}>{passRateB}%</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Target Pass Rate</div>
            </div>
          </div>

          {/* Fixed vs New Failures Details */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div className="glass-card" style={{ padding: '20px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--accent-green)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={18} /> Fixed Defect Test Cases ({fixedList.length})
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {fixedList.length === 0 ? (
                  <div style={{ fontSize: '0.83rem', color: 'var(--text-dim)', fontStyle: 'italic', padding: '6px 0' }}>
                    No fixed defects detected between these two releases.
                  </div>
                ) : (
                  fixedList.map((c, i) => (
                    <div key={i} style={{ padding: '10px 12px', borderRadius: '6px', background: 'rgba(0,230,118,0.08)', border: '1px solid rgba(0,230,118,0.2)', fontSize: '0.85rem', color: '#a7f3d0' }}>
                      ✓ {c}
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="glass-card" style={{ padding: '20px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--accent-red)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <XCircle size={18} /> New Regression Failures ({newFailuresList.length})
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {newFailuresList.length === 0 ? (
                  <div style={{ fontSize: '0.83rem', color: 'var(--text-dim)', fontStyle: 'italic', padding: '6px 0' }}>
                    No new regression failures detected between these two releases.
                  </div>
                ) : (
                  newFailuresList.map((c, i) => (
                    <div key={i} style={{ padding: '10px 12px', borderRadius: '6px', background: 'rgba(255,23,68,0.08)', border: '1px solid rgba(255,23,68,0.2)', fontSize: '0.85rem', color: '#fca5a5' }}>
                      ✗ {c}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
