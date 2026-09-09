import React, { useEffect, useState } from 'react';
import { AlertOctagon, Sparkles, CheckCircle2, RefreshCw, List } from 'lucide-react';
import { apiService } from '../services/api';
import { FailureRecord } from '../types';

export const FailureIntelligence: React.FC = () => {
  const [failures, setFailures]   = useState<FailureRecord[]>([]);
  const [analysis, setAnalysis]   = useState<any>(null);
  const [selected, setSelected]   = useState<number>(1);
  const [loading, setLoading]     = useState(false);

  useEffect(() => {
    apiService.getFailures().then(f => {
      setFailures(f);
      if (f.length) {
        setSelected(f[0].id);
        loadAnalysis(f[0].id);
      }
    }).catch(console.error);
  }, []);

  const loadAnalysis = (id: number) => {
    setLoading(true);
    setSelected(id);
    apiService.getSimilarFailures(id)
      .then(setAnalysis)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const severityStyle = (s: string) => {
    if (s === 'CRITICAL') return 'badge-fail';
    if (s === 'HIGH')     return 'badge-warning';
    return 'badge-info';
  };

  const selectedFailure = failures.find(f => f.id === selected);

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '22px' }}>

      <div>
        <h2 className="section-title">Failure Intelligence &amp; Similarity Engine</h2>
        <p className="section-sub">
          Automated failure capture, historical similarity matching, root cause analysis, and AI recommendations.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px', alignItems: 'start' }}>

        {/* Failure List */}
        <div className="glass-card" style={{ padding: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
            <List size={16} color="var(--text-muted)" />
            <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '0.9rem', fontWeight: 600, margin: 0 }}>
              Recorded Failures
            </h3>
            <span className="badge badge-fail" style={{ marginLeft: 'auto' }}>{failures.length}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '480px', overflowY: 'auto' }}>
            {failures.length === 0 ? (
              <div style={{ padding: '24px 12px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.82rem' }}>
                No failure records found in database.
              </div>
            ) : (
              failures.map(f => (
                <button
                  key={f.id}
                  onClick={() => loadAnalysis(f.id)}
                  style={{
                    width: '100%', textAlign: 'left', padding: '10px 12px',
                    borderRadius: '8px', border: 'none', cursor: 'pointer',
                    background: selected === f.id ? 'rgba(255,23,68,0.12)' : 'rgba(10,15,26,0.6)',
                    borderLeft: selected === f.id ? '3px solid var(--accent-red)' : '3px solid transparent',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ fontSize: '0.82rem', fontWeight: 600, color: selected === f.id ? '#fff' : 'var(--text-muted)' }}>
                    {f.test_case || f.test_case_name || `Failure #${f.id}`}
                  </div>
                  <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--accent-red)', marginTop: '3px' }}>
                    {f.error_type || f.error_code || 'ERROR'} · {f.firmware_version || 'v—'}
                  </div>
                  <div style={{ display: 'flex', gap: '6px', marginTop: '5px' }}>
                    <span className={`badge ${severityStyle(f.severity || f.case_severity || 'HIGH')}`}>
                      {f.severity || f.case_severity || 'HIGH'}
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Detail + Analysis */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* Active Incident Card */}
          <div className="glass-card" style={{ padding: '22px', borderLeft: '4px solid var(--accent-red)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px', color: 'var(--accent-red)' }}>
              <AlertOctagon size={20} />
              <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                Active Incident — Failure #{selected}
              </h3>
              <span className="badge badge-fail" style={{ marginLeft: 'auto' }}>OPEN</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '0.84rem' }}>
              <div>
                <div className="label">Failed Test Case</div>
                <div style={{ fontWeight: 600, color: '#fff', marginTop: '3px' }}>
                  {analysis?.target_failure?.test_case || selectedFailure?.test_case || selectedFailure?.test_case_name || 'N/A'}
                </div>
              </div>
              <div>
                <div className="label">Error Classification</div>
                <div className="mono" style={{ color: 'var(--accent-red)', fontWeight: 600, marginTop: '3px' }}>
                  {analysis?.target_failure?.error_type || selectedFailure?.error_type || selectedFailure?.error_code || 'N/A'}
                </div>
              </div>
              <div>
                <div className="label">Meter</div>
                <div className="mono" style={{ color: 'var(--accent-cyan)', marginTop: '3px' }}>
                  {analysis?.target_failure?.meter_number || (analysis?.target_failure?.meter_id ? `Meter #${analysis.target_failure.meter_id}` : (selectedFailure?.meter_id ? `Meter #${selectedFailure.meter_id}` : 'N/A'))}
                </div>
              </div>
              <div>
                <div className="label">Firmware</div>
                <div className="mono" style={{ color: 'var(--accent-cyan)', marginTop: '3px' }}>
                  {analysis?.target_failure?.firmware_version || selectedFailure?.firmware_version || 'N/A'}
                </div>
              </div>
            </div>

            <div style={{ marginTop: '14px' }}>
              <div className="label">Raw Error Output</div>
              <div className="terminal" style={{ marginTop: '6px', padding: '10px 14px', height: 'auto', whiteSpace: 'pre-wrap' }}>
                {analysis?.target_failure?.error_message || selectedFailure?.error_message || selectedFailure?.case_details || 'No raw error details recorded.'}
              </div>
            </div>
          </div>

          {/* AI Analysis */}
          <div className="glass-card" style={{ padding: '22px', borderLeft: '4px solid var(--accent-cyan)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', color: 'var(--accent-cyan)' }}>
              <Sparkles size={20} />
              <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                AI-Grounded Root Cause Analysis
              </h3>
              {loading && <RefreshCw size={15} color="var(--text-dim)" style={{ marginLeft: 'auto', animation: 'spin 1s linear infinite' }} />}
            </div>

            {analysis?.best_match ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  <span className="badge badge-fail">
                    Similarity: {analysis.best_match.similarity_score}%
                  </span>
                  <span className="badge badge-pass">
                    Confidence: {analysis.best_match.confidence || 'HIGH'}
                  </span>
                  <span className="badge badge-info">
                    Matched Incident #{analysis.best_match.failure_id}
                  </span>
                </div>

                <div>
                  <div className="label" style={{ marginBottom: '6px' }}>Identified Root Cause</div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
                    {analysis.best_match.root_cause || 'Identified root cause details recorded from historical match.'}
                  </p>
                </div>

                {analysis.best_match.solution && (
                  <div className="alert-banner success">
                    <CheckCircle2 size={18} style={{ flexShrink: 0 }} />
                    <div>
                      <strong>Recommended Action:</strong>
                      <p style={{ marginTop: '4px', fontSize: '0.83rem', lineHeight: '1.6' }}>
                        {analysis.best_match.solution}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>
                <p style={{ margin: 0, fontSize: '0.88rem' }}>No prior matching failure found in database.</p>
                <p style={{ margin: '6px 0 0', fontSize: '0.76rem', color: 'var(--text-dim)' }}>
                  This defect pattern has not been previously observed or indexed in historical records.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
