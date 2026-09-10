import React, { useState, useEffect, useCallback } from 'react';
import {
  Plus, RefreshCw, ExternalLink, CheckCircle2, XCircle,
  Clock, AlertTriangle, Search, Filter, ChevronDown, ChevronUp,
  Trash2, Edit3, X, Save, Layers, CloudOff,
} from 'lucide-react';
import { apiService } from '../services/api';
import { TestCaseDefinition, TestSuite, AzureSyncStatus } from '../types';

// ─────────────────────────────────────────────
// Azure sync status badge
// ─────────────────────────────────────────────
const SyncBadge: React.FC<{ status: AzureSyncStatus; error?: string | null }> = ({ status, error }) => {
  const map: Record<AzureSyncStatus, { label: string; icon: React.ReactNode; cls: string }> = {
    SYNCED:         { label: 'Synced',         icon: <CheckCircle2 size={11} />, cls: 'badge-pass' },
    FAILED:         { label: 'Sync Failed',    icon: <XCircle size={11} />,     cls: 'badge-fail' },
    PENDING:        { label: 'Pending',        icon: <Clock size={11} />,       cls: 'badge-pending' },
    NOT_CONFIGURED: { label: 'Not Configured', icon: <AlertTriangle size={11} />, cls: 'badge-warn' },
    NOT_SYNCED:     { label: 'Not Synced',     icon: <CloudOff size={11} />,    cls: 'badge-dim' },
  };
  const cfg = map[status] ?? map['NOT_SYNCED'];
  return (
    <span className={`badge ${cfg.cls}`} title={error ?? undefined} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', cursor: error ? 'help' : 'default' }}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
};

// ─────────────────────────────────────────────
// Azure DevOps deep link helper
// ─────────────────────────────────────────────
const buildAzureUrl = (azureId: number | null | undefined, org: string | null, project: string | null) => {
  // org/project come from GET /api/settings/azure-connection-status (the
  // server's own configured values) — not secret, but no longer read from
  // localStorage since SettingsPage.tsx no longer writes them there.
  if (!azureId || !org || !project) return null;
  return `https://dev.azure.com/${org}/${project}/_testManagement/testcases/edit/${azureId}`;
};

// ─────────────────────────────────────────────
// Empty/loading state
// ─────────────────────────────────────────────
const EmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div style={{ textAlign: 'center', padding: '48px 24px', color: 'var(--text-dim)' }}>
    <Layers size={40} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
    <p style={{ fontSize: '0.9rem' }}>{message}</p>
  </div>
);

// ─────────────────────────────────────────────
// Test Case row
// ─────────────────────────────────────────────
interface RowProps {
  tc: TestCaseDefinition;
  onRetry: (id: number) => void;
  retrying: boolean;
  onEdit: (tc: TestCaseDefinition) => void;
  azureOrg: string | null;
  azureProject: string | null;
}

const TestCaseRow: React.FC<RowProps> = ({ tc, onRetry, retrying, onEdit, azureOrg, azureProject }) => {
  const [expanded, setExpanded] = useState(false);
  const azureUrl = buildAzureUrl(tc.azure_test_case_id, azureOrg, azureProject);

  return (
    <>
      <tr
        style={{ cursor: 'pointer' }}
        onClick={() => setExpanded(x => !x)}
      >
        <td>
          <div style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--text-main)' }}>{tc.name}</div>
          {tc.description && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              {tc.description.substring(0, 80)}{tc.description.length > 80 ? '…' : ''}
            </div>
          )}
        </td>
        <td>
          <span className="mono" style={{ color: 'var(--accent-cyan)', fontSize: '0.8rem' }}>{tc.obis_target}</span>
        </td>
        <td>
          <span className={`badge badge-${(tc.priority ?? tc.severity ?? 'HIGH').toLowerCase()}`}>
            {tc.priority ?? tc.severity ?? 'HIGH'}
          </span>
        </td>
        <td>
          <SyncBadge status={tc.azure_sync_status} error={tc.azure_sync_error} />
        </td>
        <td>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {/* Retry sync */}
            {(tc.azure_sync_status === 'FAILED' || tc.azure_sync_status === 'PENDING' || tc.azure_sync_status === 'NOT_SYNCED') && (
              <button
                className="btn-ghost"
                title="Retry Azure sync"
                onClick={e => { e.stopPropagation(); onRetry(tc.test_case_id ?? tc.id); }}
                disabled={retrying}
                style={{ padding: '4px 8px', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
              >
                <RefreshCw size={12} className={retrying ? 'spin' : ''} />
                {retrying ? 'Syncing…' : 'Retry'}
              </button>
            )}
            {/* Azure deep link */}
            {azureUrl && (
              <a
                href={azureUrl}
                target="_blank"
                rel="noopener noreferrer"
                onClick={e => e.stopPropagation()}
                title={`Open in Azure DevOps (Work Item #${tc.azure_test_case_id})`}
                style={{ color: 'var(--accent-cyan)', display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '0.78rem' }}
              >
                <ExternalLink size={13} /> #{tc.azure_test_case_id}
              </a>
            )}
            {/* Edit */}
            <button
              className="btn-ghost"
              onClick={e => { e.stopPropagation(); onEdit(tc); }}
              style={{ padding: '4px 8px', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
            >
              <Edit3 size={12} /> Edit
            </button>
            {/* Expand toggle */}
            {expanded ? <ChevronUp size={14} color="var(--text-dim)" /> : <ChevronDown size={14} color="var(--text-dim)" />}
          </div>
        </td>
      </tr>

      {/* Expanded detail row */}
      {expanded && (
        <tr style={{ background: 'rgba(0,242,254,0.02)' }}>
          <td colSpan={5} style={{ padding: '12px 20px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', fontSize: '0.8rem' }}>
              <div>
                <div className="label" style={{ marginBottom: '4px' }}>Action</div>
                <span className="mono" style={{ color: 'var(--text-main)' }}>{tc.action}</span>
              </div>
              <div>
                <div className="label" style={{ marginBottom: '4px' }}>Timeout</div>
                <span>{tc.timeout_ms}ms</span>
              </div>
              <div>
                <div className="label" style={{ marginBottom: '4px' }}>Last Synced</div>
                <span>{tc.azure_last_synced_at ? new Date(tc.azure_last_synced_at).toLocaleString() : '—'}</span>
              </div>
              {tc.expected_result && (
                <div style={{ gridColumn: '1 / -1' }}>
                  <div className="label" style={{ marginBottom: '4px' }}>Expected Result</div>
                  <span>{tc.expected_result}</span>
                </div>
              )}
              {tc.test_steps && tc.test_steps.length > 0 && (
                <div style={{ gridColumn: '1 / -1' }}>
                  <div className="label" style={{ marginBottom: '6px' }}>Test Steps</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {tc.test_steps.map((s: any, i: number) => (
                      <div key={i} style={{ display: 'flex', gap: '12px', background: 'rgba(0,0,0,0.25)', borderRadius: '6px', padding: '6px 10px' }}>
                        <span style={{ color: 'var(--accent-cyan)', fontWeight: 700, minWidth: '20px' }}>{i + 1}.</span>
                        <span style={{ flex: 1 }}>{s.action}</span>
                        {s.expected && <span style={{ color: 'var(--accent-green)', fontSize: '0.75rem' }}>→ {s.expected}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {tc.azure_sync_error && (
                <div style={{ gridColumn: '1 / -1' }}>
                  <div className="label" style={{ color: 'var(--accent-red)', marginBottom: '4px' }}>Sync Error</div>
                  <span className="mono" style={{ color: 'var(--accent-red)', fontSize: '0.75rem' }}>{tc.azure_sync_error}</span>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
};

// ─────────────────────────────────────────────
// Create / Edit Modal
// ─────────────────────────────────────────────
interface ModalProps {
  suites: TestSuite[];
  editing: TestCaseDefinition | null;
  onClose: () => void;
  onSaved: () => void;
}

interface StepDraft { action: string; expected: string; }

const TestCaseModal: React.FC<ModalProps> = ({ suites, editing, onClose, onSaved }) => {
  const isEdit = Boolean(editing);

  const [name,           setName]           = useState(editing?.name ?? '');
  const [description,    setDescription]    = useState(editing?.description ?? '');
  const [suiteId,        setSuiteId]        = useState<number | ''>(editing?.suite_id ?? (suites[0]?.id ?? ''));
  const [priority,       setPriority]       = useState<string>(editing?.priority ?? editing?.severity ?? 'HIGH');
  const [obisTarget,     setObisTarget]     = useState(editing?.obis_target ?? '1.0.1.8.0.255');
  const [action,         setAction]         = useState(editing?.action ?? 'READ_OBIS');
  const [expectedResult, setExpectedResult] = useState(editing?.expected_result ?? '');
  const [timeoutMs,      setTimeoutMs]      = useState(editing?.timeout_ms ?? 5000);
  const [steps,          setSteps]          = useState<StepDraft[]>(
    (editing?.test_steps ?? []).map((s: any) => ({ action: s.action ?? '', expected: s.expected ?? '' }))
  );
  const [saving, setSaving]   = useState(false);
  const [error,  setError]    = useState<string | null>(null);

  const addStep = () => setSteps(ss => [...ss, { action: '', expected: '' }]);
  const removeStep = (i: number) => setSteps(ss => ss.filter((_, idx) => idx !== i));
  const updateStep = (i: number, field: 'action' | 'expected', val: string) =>
    setSteps(ss => ss.map((s, idx) => idx === i ? { ...s, [field]: val } : s));

  const handleSave = async () => {
    if (!name.trim()) { setError('Name is required.'); return; }
    if (!suiteId)     { setError('Select a test suite.'); return; }
    setSaving(true);
    setError(null);
    try {
      const payload: any = {
        suite_id: Number(suiteId),
        name: name.trim(),
        description: description.trim(),
        priority,
        obis_target: obisTarget,
        action,
        expected_result: expectedResult.trim() || undefined,
        timeout_ms: Number(timeoutMs),
        test_steps: steps.filter(s => s.action.trim()),
      };
      if (isEdit && editing) {
        await apiService.updateTestCase(editing.test_case_id ?? editing.id, payload);
      } else {
        await apiService.createTestCase(payload);
      }
      onSaved();
      onClose();
    } catch (err: any) {
      setError(err.message ?? 'Save failed. Check that the backend is running.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0,0,0,0.72)', backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px',
    }}>
      <div className="glass-card" style={{
        width: '100%', maxWidth: '680px', maxHeight: '90vh', overflow: 'hidden',
        display: 'flex', flexDirection: 'column', borderRadius: '16px',
        border: '1px solid var(--border-cyan)',
      }}>
        {/* Header */}
        <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ fontFamily: 'var(--font-head)', fontSize: '1.1rem', fontWeight: 700, margin: 0, color: 'var(--accent-cyan)' }}>
              {isEdit ? 'Edit Test Case' : 'Create Test Case'}
            </h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '3px' }}>
              {isEdit ? 'Changes sync to Azure DevOps automatically.' : 'Saved locally and synced to Azure DevOps Test Plans.'}
            </p>
          </div>
          <button className="btn-ghost" onClick={onClose} style={{ padding: '6px' }}><X size={18} /></button>
        </div>

        {/* Body */}
        <div style={{ padding: '20px 24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {error && (
            <div className="alert-banner danger">
              <XCircle size={16} /> {error}
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div style={{ gridColumn: '1 / -1' }}>
              <label className="form-label">Test Case Name *</label>
              <input id="tc-name" className="form-input" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Mode E Optical Handshake 300 Baud" />
            </div>

            <div>
              <label className="form-label">Test Suite *</label>
              <select id="tc-suite" className="form-select" value={suiteId} onChange={e => setSuiteId(Number(e.target.value))}>
                <option value="">— Select suite —</option>
                {suites.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>

            <div>
              <label className="form-label">Priority</label>
              <select id="tc-priority" className="form-select" value={priority} onChange={e => setPriority(e.target.value)}>
                {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>

            <div>
              <label className="form-label">OBIS Target Code</label>
              <input id="tc-obis" className="form-input mono" value={obisTarget} onChange={e => setObisTarget(e.target.value)} placeholder="1.0.1.8.0.255" />
            </div>

            <div>
              <label className="form-label">Action</label>
              <select id="tc-action" className="form-select" value={action} onChange={e => setAction(e.target.value)}>
                <option value="READ_OBIS">READ_OBIS</option>
                <option value="WRITE_OBIS">WRITE_OBIS</option>
                <option value="EXECUTE_METHOD">EXECUTE_METHOD</option>
              </select>
            </div>

            <div>
              <label className="form-label">Timeout (ms)</label>
              <input id="tc-timeout" className="form-input mono" type="number" value={timeoutMs} onChange={e => setTimeoutMs(Number(e.target.value))} />
            </div>

            <div>
              <label className="form-label">Expected Result</label>
              <input id="tc-expected" className="form-input" value={expectedResult} onChange={e => setExpectedResult(e.target.value)} placeholder="e.g. 230.5 ±2%" />
            </div>

            <div style={{ gridColumn: '1 / -1' }}>
              <label className="form-label">Description</label>
              <textarea
                id="tc-description"
                className="form-input"
                value={description}
                onChange={e => setDescription(e.target.value)}
                rows={2}
                style={{ resize: 'vertical', fontFamily: 'inherit' }}
                placeholder="Brief description of what this test case validates."
              />
            </div>
          </div>

          {/* Steps */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <label className="form-label" style={{ marginBottom: 0 }}>Test Steps</label>
              <button id="add-step-btn" className="btn-ghost" onClick={addStep} style={{ padding: '4px 10px', fontSize: '0.78rem', display: 'inline-flex', gap: '4px', alignItems: 'center' }}>
                <Plus size={13} /> Add Step
              </button>
            </div>
            {steps.length === 0 && (
              <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontStyle: 'italic' }}>No steps added yet — the test case will use a default single-step action.</p>
            )}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {steps.map((step, i) => (
                <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '8px', alignItems: 'center', background: 'rgba(0,0,0,0.25)', borderRadius: '8px', padding: '10px 12px' }}>
                  <div>
                    <label className="form-label" style={{ marginBottom: '4px', fontSize: '0.65rem' }}>Step {i + 1} — Action</label>
                    <input className="form-input" style={{ padding: '6px 10px' }} value={step.action} onChange={e => updateStep(i, 'action', e.target.value)} placeholder="Read OBIS 1.0.1.8.0.255" />
                  </div>
                  <div>
                    <label className="form-label" style={{ marginBottom: '4px', fontSize: '0.65rem' }}>Expected Result</label>
                    <input className="form-input" style={{ padding: '6px 10px' }} value={step.expected} onChange={e => updateStep(i, 'expected', e.target.value)} placeholder="Value > 0 kWh" />
                  </div>
                  <button className="btn-ghost" onClick={() => removeStep(i)} style={{ padding: '6px', marginTop: '18px', color: 'var(--accent-red)' }}>
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div style={{ padding: '14px 24px', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button id="save-tc-btn" className="btn-cyan" onClick={handleSave} disabled={saving}>
            {saving ? <><RefreshCw size={15} className="spin" /> Saving…</> : <><Save size={15} /> {isEdit ? 'Save Changes' : 'Create & Sync'}</>}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────
export const TestCaseManager: React.FC = () => {
  const [suites,       setSuites]       = useState<TestSuite[]>([]);
  const [testCases,    setTestCases]    = useState<TestCaseDefinition[]>([]);
  const [loading,      setLoading]      = useState(true);
  const [filterSuite,  setFilterSuite]  = useState<number | ''>('');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [search,       setSearch]       = useState('');
  const [showModal,    setShowModal]    = useState(false);
  const [editing,      setEditing]      = useState<TestCaseDefinition | null>(null);
  const [retrying,     setRetrying]     = useState<number | null>(null);
  const [toast,        setToast]        = useState<{ msg: string; type: 'success' | 'error' } | null>(null);
  // Sourced from the backend's own configured Azure DevOps org/project
  // (GET /api/settings/azure-connection-status) — fetched once, used only
  // to build deep-link URLs. Not secret; never includes the PAT.
  const [azureOrg,     setAzureOrg]     = useState<string | null>(null);
  const [azureProject, setAzureProject] = useState<string | null>(null);

  const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [s, tc] = await Promise.all([
        apiService.getTestSuites(),
        apiService.getTestCases(),
      ]);
      // normalize: API returns suite_id, but our type uses id on suites
      const normalizedSuites = s.map((x: any) => ({ ...x, id: x.suite_id ?? x.id }));
      setSuites(normalizedSuites);
      // normalize test cases: API uses test_case_id, type uses id
      const normalizedCases = tc.map((x: any) => ({ ...x, id: x.test_case_id ?? x.id }));
      setTestCases(normalizedCases);
    } catch {
      showToast('Backend unreachable — showing cached data.', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    apiService.getAzureConnectionStatus()
      .then(status => {
        setAzureOrg(status.org);
        setAzureProject(status.project);
      })
      .catch(() => { /* deep links simply won't render without org/project */ });
  }, []);

  const handleRetry = async (id: number) => {
    setRetrying(id);
    try {
      const updated = await apiService.retrySyncTestCase(id);
      setTestCases(prev => prev.map(tc => (tc.test_case_id ?? tc.id) === id ? { ...updated, id: updated.test_case_id ?? (updated as any).id } : tc));
      const status = (updated as any).azure_sync_status;
      showToast(status === 'SYNCED' ? '✓ Test case synced to Azure DevOps!' : `Sync status: ${status}`, status === 'SYNCED' ? 'success' : 'error');
    } catch (err: any) {
      showToast(err.message ?? 'Retry failed. Check backend.', 'error');
    } finally {
      setRetrying(null);
    }
  };

  const openCreate = () => { setEditing(null); setShowModal(true); };
  const openEdit   = (tc: TestCaseDefinition) => { setEditing(tc); setShowModal(true); };

  const filtered = testCases.filter(tc => {
    if (filterSuite && (tc.suite_id !== filterSuite)) return false;
    if (filterStatus !== 'ALL' && tc.azure_sync_status !== filterStatus) return false;
    if (search && !tc.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  // Stats
  const total   = testCases.length;
  const synced  = testCases.filter(t => t.azure_sync_status === 'SYNCED').length;
  const failed  = testCases.filter(t => t.azure_sync_status === 'FAILED').length;
  const pending = testCases.filter(t => ['PENDING', 'NOT_SYNCED'].includes(t.azure_sync_status)).length;

  return (
    <div style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '22px' }}>

      {/* Toast */}
      {toast && (
        <div
          className={`alert-banner ${toast.type === 'success' ? 'success' : 'danger'}`}
          style={{ position: 'fixed', top: '80px', right: '24px', zIndex: 999, minWidth: '320px', maxWidth: '480px', boxShadow: '0 8px 32px rgba(0,0,0,0.4)' }}
        >
          {toast.type === 'success' ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 className="section-title">Test Case Manager</h2>
          <p className="section-sub">Create, manage, and synchronize test cases with Azure DevOps Test Plans.</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn-ghost" onClick={load} title="Refresh">
            <RefreshCw size={15} className={loading ? 'spin' : ''} />
          </button>
          <button id="create-test-case-btn" className="btn-cyan" onClick={openCreate}>
            <Plus size={16} /> New Test Case
          </button>
        </div>
      </div>

      {/* KPI Strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px' }}>
        {[
          { label: 'Total Cases',   value: total,   color: 'var(--text-main)' },
          { label: 'Synced ✓',      value: synced,  color: 'var(--accent-green)' },
          { label: 'Sync Failed',   value: failed,  color: 'var(--accent-red)' },
          { label: 'Pending',       value: pending, color: 'var(--accent-amber)' },
        ].map(k => (
          <div key={k.label} className="stat-card" style={{ padding: '16px 20px' }}>
            <div className="label">{k.label}</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: k.color, fontFamily: 'var(--font-head)', lineHeight: 1.2, marginTop: '6px' }}>
              {loading ? '—' : k.value}
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="glass-card" style={{ padding: '16px 20px', display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: '180px' }}>
          <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
          <input
            id="tc-search"
            className="form-input"
            style={{ paddingLeft: '34px' }}
            placeholder="Search test cases…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Filter size={14} color="var(--text-dim)" />
          <select id="filter-suite" className="form-select" style={{ width: 'auto' }} value={filterSuite} onChange={e => setFilterSuite(e.target.value ? Number(e.target.value) : '')}>
            <option value="">All Suites</option>
            {suites.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </div>

        <select id="filter-status" className="form-select" style={{ width: 'auto' }} value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="ALL">All Statuses</option>
          <option value="SYNCED">Synced</option>
          <option value="PENDING">Pending</option>
          <option value="FAILED">Failed</option>
          <option value="NOT_CONFIGURED">Not Configured</option>
          <option value="NOT_SYNCED">Not Synced</option>
        </select>
      </div>

      {/* Table */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {[1, 2, 3].map(i => <div key={i} className="skeleton" style={{ height: '48px', borderRadius: '8px' }} />)}
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState message={testCases.length === 0 ? 'No test cases yet. Create your first one!' : 'No test cases match the current filters.'} />
        ) : (
          <table className="data-table" style={{ margin: 0 }}>
            <thead>
              <tr>
                <th>Test Case</th>
                <th>OBIS Target</th>
                <th>Priority</th>
                <th>Azure Sync</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(tc => (
                <TestCaseRow
                  key={tc.test_case_id ?? tc.id}
                  tc={tc}
                  onRetry={handleRetry}
                  retrying={retrying === (tc.test_case_id ?? tc.id)}
                  onEdit={openEdit}
                  azureOrg={azureOrg}
                  azureProject={azureProject}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <TestCaseModal
          suites={suites}
          editing={editing}
          onClose={() => setShowModal(false)}
          onSaved={load}
        />
      )}
    </div>
  );
};
