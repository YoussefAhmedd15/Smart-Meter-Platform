import React, { useEffect, useState, useCallback } from 'react';
import {
  Users, UserPlus, Edit3, Trash2, ShieldCheck, ShieldAlert,
  CheckCircle2, XCircle, RefreshCw, X, Save, Eye, EyeOff,
  Crown, UserCheck,
} from 'lucide-react';
import { apiService, AuthUser } from '../services/api';
import { useAuth } from '../context/AuthContext';

// ─── Helpers ───────────────────────────────────────────────────────────────

const ROLES = ['tester', 'admin'] as const;
type Role = typeof ROLES[number];

const RoleBadge: React.FC<{ role: string }> = ({ role }) => {
  const isAdmin = role === 'admin';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '4px',
      padding: '3px 10px', borderRadius: '99px', fontSize: '0.72rem', fontWeight: 700,
      background: isAdmin ? 'rgba(168,85,247,0.15)' : 'rgba(0,242,254,0.12)',
      color: isAdmin ? '#c084fc' : 'var(--accent-cyan)',
      border: `1px solid ${isAdmin ? 'rgba(168,85,247,0.35)' : 'rgba(0,242,254,0.3)'}`,
      textTransform: 'uppercase', letterSpacing: '0.06em',
    }}>
      {isAdmin ? <Crown size={10} /> : <UserCheck size={10} />}
      {role}
    </span>
  );
};

const StatusBadge: React.FC<{ active: boolean }> = ({ active }) => (
  <span style={{
    display: 'inline-flex', alignItems: 'center', gap: '4px',
    padding: '3px 10px', borderRadius: '99px', fontSize: '0.72rem', fontWeight: 700,
    background: active ? 'rgba(0,255,136,0.1)' : 'rgba(255,23,68,0.1)',
    color: active ? 'var(--accent-green)' : 'var(--accent-red)',
    border: `1px solid ${active ? 'rgba(0,255,136,0.25)' : 'rgba(255,23,68,0.25)'}`,
  }}>
    {active ? <CheckCircle2 size={10} /> : <XCircle size={10} />}
    {active ? 'Active' : 'Inactive'}
  </span>
);

// ─── Modal ──────────────────────────────────────────────────────────────────

interface UserModalProps {
  mode: 'create' | 'edit';
  initial?: AuthUser;
  onClose: () => void;
  onSave: (data: any) => Promise<void>;
}

const UserModal: React.FC<UserModalProps> = ({ mode, initial, onClose, onSave }) => {
  const [email, setEmail] = useState(initial?.email ?? '');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<Role>((initial?.role as Role) ?? 'tester');
  const [isActive, setIsActive] = useState(initial?.is_active ?? true);
  const [showPw, setShowPw] = useState(false);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setSaving(true);
    try {
      const payload: any = { role, is_active: isActive };
      if (email) payload.email = email;
      if (password) payload.password = password;
      if (mode === 'create') {
        if (!email || !password) { setErr('Email and password are required.'); setSaving(false); return; }
        await onSave({ email, password, role });
      } else {
        await onSave(payload);
      }
      onClose();
    } catch (ex: any) {
      setErr(ex?.message ?? 'Save failed.');
    } finally {
      setSaving(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '9px 12px', borderRadius: 'var(--radius-sm)',
    border: '1px solid var(--border-color)', background: 'var(--bg-input)',
    color: 'var(--text-main)', fontSize: '0.88rem', boxSizing: 'border-box',
    outline: 'none',
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(6px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{
        width: '440px', background: 'var(--bg-card)',
        border: '1px solid var(--border-color)', borderRadius: 'var(--radius-lg)',
        boxShadow: '0 24px 64px rgba(0,0,0,0.6)', padding: '28px',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px', height: '36px', borderRadius: '8px',
              background: 'linear-gradient(135deg, rgba(0,242,254,0.2) 0%, rgba(79,172,254,0.15) 100%)',
              border: '1px solid rgba(0,242,254,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              {mode === 'create' ? <UserPlus size={16} color="var(--accent-cyan)" /> : <Edit3 size={16} color="var(--accent-cyan)" />}
            </div>
            <div>
              <div style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '1rem' }}>
                {mode === 'create' ? 'Create User' : 'Edit User'}
              </div>
              <div style={{ fontSize: '0.73rem', color: 'var(--text-dim)' }}>
                {mode === 'create' ? 'Add a new platform user' : `Editing ${initial?.email}`}
              </div>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-dim)', padding: '4px' }}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Email */}
          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600 }}>
              Email {mode === 'edit' && <span style={{ fontWeight: 400, color: 'var(--text-dim)' }}>(leave blank to keep current)</span>}
            </label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder={mode === 'edit' ? initial?.email : 'user@example.com'}
              required={mode === 'create'}
              style={inputStyle}
            />
          </div>

          {/* Password */}
          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600 }}>
              Password {mode === 'edit' && <span style={{ fontWeight: 400, color: 'var(--text-dim)' }}>(leave blank to keep current)</span>}
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPw ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder={mode === 'create' ? 'Min. 6 characters' : '••••••••'}
                required={mode === 'create'}
                style={{ ...inputStyle, paddingRight: '40px' }}
              />
              <button
                type="button"
                onClick={() => setShowPw(v => !v)}
                style={{
                  position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-dim)', padding: '2px',
                }}
              >
                {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
          </div>

          {/* Role */}
          <div>
            <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600 }}>
              Role
            </label>
            <div style={{ display: 'flex', gap: '8px' }}>
              {ROLES.map(r => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setRole(r)}
                  style={{
                    flex: 1, padding: '8px 0', borderRadius: 'var(--radius-sm)',
                    border: `1px solid ${role === r ? (r === 'admin' ? 'rgba(168,85,247,0.5)' : 'rgba(0,242,254,0.5)') : 'var(--border-color)'}`,
                    background: role === r
                      ? (r === 'admin' ? 'rgba(168,85,247,0.15)' : 'rgba(0,242,254,0.12)')
                      : 'var(--bg-input)',
                    color: role === r
                      ? (r === 'admin' ? '#c084fc' : 'var(--accent-cyan)')
                      : 'var(--text-muted)',
                    fontWeight: 600, fontSize: '0.82rem', cursor: 'pointer',
                    textTransform: 'capitalize', transition: 'all 0.15s ease',
                  }}
                >
                  {r === 'admin' ? '👑 Admin' : '🔬 Tester'}
                </button>
              ))}
            </div>
          </div>

          {/* Status (edit only) */}
          {mode === 'edit' && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>Account Status</label>
              <button
                type="button"
                onClick={() => setIsActive(v => !v)}
                style={{
                  padding: '6px 16px', borderRadius: '99px', border: 'none', cursor: 'pointer',
                  fontWeight: 700, fontSize: '0.78rem',
                  background: isActive ? 'rgba(0,255,136,0.15)' : 'rgba(255,23,68,0.12)',
                  color: isActive ? 'var(--accent-green)' : 'var(--accent-red)',
                  transition: 'all 0.15s ease',
                }}
              >
                {isActive ? '✓ Active' : '✗ Inactive'}
              </button>
            </div>
          )}

          {/* Error */}
          {err && (
            <div style={{
              padding: '10px 12px', borderRadius: 'var(--radius-sm)',
              background: 'rgba(255,23,68,0.08)', border: '1px solid var(--border-red)',
              color: 'var(--accent-red)', fontSize: '0.82rem',
            }}>
              {err}
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', gap: '10px', marginTop: '4px' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                flex: 1, padding: '10px', borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-color)', background: 'transparent',
                color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.88rem', cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              style={{
                flex: 2, padding: '10px', borderRadius: 'var(--radius-sm)', border: 'none',
                background: 'linear-gradient(135deg, #00f2fe 0%, #4facfe 100%)',
                color: '#070b14', fontWeight: 700, fontSize: '0.88rem',
                cursor: saving ? 'default' : 'pointer', opacity: saving ? 0.7 : 1,
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
              }}
            >
              <Save size={14} />
              {saving ? 'Saving…' : 'Save User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ─── Main Page ───────────────────────────────────────────────────────────────

export const AdminPage: React.FC = () => {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modal, setModal] = useState<{ mode: 'create' | 'edit'; user?: AuthUser } | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<AuthUser | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null);

  const showToast = useCallback((msg: string, type: 'success' | 'error' = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  }, []);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.adminListUsers();
      setUsers(data);
    } catch (ex: any) {
      setError(ex?.message ?? 'Failed to load users.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  const handleCreate = async (data: any) => {
    await apiService.adminCreateUser(data.email, data.password, data.role);
    showToast(`User ${data.email} created successfully.`);
    await loadUsers();
  };

  const handleUpdate = async (data: any) => {
    if (!modal?.user) return;
    await apiService.adminUpdateUser(modal.user.user_id, data);
    showToast(`User updated successfully.`);
    await loadUsers();
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleteLoading(true);
    try {
      await apiService.adminDeleteUser(deleteTarget.user_id);
      showToast(`User ${deleteTarget.email} deleted.`);
      setDeleteTarget(null);
      await loadUsers();
    } catch (ex: any) {
      showToast(ex?.message ?? 'Delete failed.', 'error');
    } finally {
      setDeleteLoading(false);
    }
  };

  // ── Stat cards ─────────────────────────────────────────────────────────────
  const totalUsers  = users.length;
  const adminCount  = users.filter(u => u.role === 'admin').length;
  const activeCount = users.filter(u => u.is_active).length;
  const testerCount = users.filter(u => u.role === 'tester').length;

  const stats = [
    { label: 'Total Users',  value: totalUsers,  icon: Users,       color: 'var(--accent-cyan)' },
    { label: 'Admins',       value: adminCount,   icon: Crown,       color: '#c084fc' },
    { label: 'Testers',      value: testerCount,  icon: ShieldCheck, color: 'var(--accent-blue)' },
    { label: 'Active',       value: activeCount,  icon: CheckCircle2,color: 'var(--accent-green)' },
  ];

  return (
    <div style={{ padding: '28px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Toast */}
      {toast && (
        <div style={{
          position: 'fixed', top: '24px', right: '24px', zIndex: 2000,
          padding: '12px 20px', borderRadius: 'var(--radius-md)',
          background: toast.type === 'success' ? 'rgba(0,255,136,0.15)' : 'rgba(255,23,68,0.15)',
          border: `1px solid ${toast.type === 'success' ? 'rgba(0,255,136,0.4)' : 'rgba(255,23,68,0.4)'}`,
          color: toast.type === 'success' ? 'var(--accent-green)' : 'var(--accent-red)',
          fontWeight: 600, fontSize: '0.88rem', boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
          display: 'flex', alignItems: 'center', gap: '8px',
          animation: 'fadeIn 0.2s ease',
        }}>
          {toast.type === 'success' ? <CheckCircle2 size={15} /> : <XCircle size={15} />}
          {toast.msg}
        </div>
      )}

      {/* Modals */}
      {modal && (
        <UserModal
          mode={modal.mode}
          initial={modal.user}
          onClose={() => setModal(null)}
          onSave={modal.mode === 'create' ? handleCreate : handleUpdate}
        />
      )}

      {/* Delete confirmation */}
      {deleteTarget && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 1000,
          background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <div style={{
            width: '380px', background: 'var(--bg-card)',
            border: '1px solid var(--border-red)', borderRadius: 'var(--radius-lg)',
            boxShadow: '0 24px 64px rgba(0,0,0,0.6)', padding: '28px', textAlign: 'center',
          }}>
            <div style={{
              width: '52px', height: '52px', borderRadius: '50%',
              background: 'rgba(255,23,68,0.12)', border: '1px solid rgba(255,23,68,0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 16px',
            }}>
              <Trash2 size={22} color="var(--accent-red)" />
            </div>
            <div style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '1rem', marginBottom: '8px' }}>
              Delete User?
            </div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.84rem', marginBottom: '24px', lineHeight: 1.5 }}>
              Are you sure you want to delete <strong style={{ color: 'var(--text-main)' }}>{deleteTarget.email}</strong>?
              This action cannot be undone.
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={() => setDeleteTarget(null)}
                style={{
                  flex: 1, padding: '10px', borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-color)', background: 'transparent',
                  color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.88rem', cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleteLoading}
                style={{
                  flex: 1, padding: '10px', borderRadius: 'var(--radius-sm)', border: 'none',
                  background: 'rgba(255,23,68,0.85)', color: '#fff',
                  fontWeight: 700, fontSize: '0.88rem', cursor: deleteLoading ? 'default' : 'pointer',
                  opacity: deleteLoading ? 0.7 : 1,
                }}
              >
                {deleteLoading ? 'Deleting…' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Page header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '28px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px' }}>
            <div style={{
              width: '40px', height: '40px', borderRadius: '10px',
              background: 'linear-gradient(135deg, rgba(168,85,247,0.25) 0%, rgba(79,172,254,0.15) 100%)',
              border: '1px solid rgba(168,85,247,0.4)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <ShieldAlert size={20} color="#c084fc" />
            </div>
            <h1 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-main)', fontFamily: 'var(--font-head)' }}>
              Admin Dashboard
            </h1>
          </div>
          <p style={{ margin: 0, fontSize: '0.84rem', color: 'var(--text-dim)' }}>
            Platform administration · Logged in as <strong style={{ color: '#c084fc' }}>{me?.email}</strong>
          </p>
        </div>
        <button
          onClick={loadUsers}
          title="Refresh"
          style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '8px 16px', borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border-color)', background: 'var(--bg-card)',
            color: 'var(--text-muted)', fontWeight: 600, fontSize: '0.82rem', cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginBottom: '28px' }}>
        {stats.map(s => {
          const Icon = s.icon;
          return (
            <div key={s.label} style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-lg)', padding: '20px',
              display: 'flex', alignItems: 'center', gap: '14px',
            }}>
              <div style={{
                width: '40px', height: '40px', borderRadius: '8px', flexShrink: 0,
                background: `${s.color}1a`, border: `1px solid ${s.color}40`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Icon size={18} color={s.color} />
              </div>
              <div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)', lineHeight: 1 }}>{s.value}</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '3px' }}>{s.label}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Manage Users section */}
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-lg)', overflow: 'hidden',
      }}>
        {/* Table header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '18px 22px', borderBottom: '1px solid var(--border-subtle)',
          flexWrap: 'wrap', gap: '12px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Users size={18} color="var(--accent-cyan)" />
            <span style={{ fontWeight: 700, color: 'var(--text-main)', fontSize: '0.96rem' }}>Manage Users</span>
            <span style={{
              padding: '2px 10px', borderRadius: '99px', fontSize: '0.7rem', fontWeight: 700,
              background: 'rgba(0,242,254,0.12)', color: 'var(--accent-cyan)',
              border: '1px solid rgba(0,242,254,0.25)',
            }}>{totalUsers}</span>
          </div>
          <button
            id="admin-create-user-btn"
            onClick={() => setModal({ mode: 'create' })}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              padding: '8px 16px', borderRadius: 'var(--radius-sm)', border: 'none',
              background: 'linear-gradient(135deg, #00f2fe 0%, #4facfe 100%)',
              color: '#070b14', fontWeight: 700, fontSize: '0.84rem', cursor: 'pointer',
            }}
          >
            <UserPlus size={14} />
            Create User
          </button>
        </div>

        {/* Loading / Error */}
        {loading && (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.88rem' }}>
            <RefreshCw size={20} style={{ animation: 'spin 1s linear infinite', marginBottom: '8px' }} />
            <div>Loading users…</div>
          </div>
        )}

        {error && !loading && (
          <div style={{ padding: '32px', textAlign: 'center' }}>
            <XCircle size={28} color="var(--accent-red)" style={{ marginBottom: '10px' }} />
            <div style={{ color: 'var(--accent-red)', fontWeight: 600, marginBottom: '6px' }}>Failed to load users</div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.82rem', marginBottom: '16px' }}>{error}</div>
            <button onClick={loadUsers} style={{
              padding: '8px 18px', borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)', background: 'transparent',
              color: 'var(--text-muted)', fontWeight: 600, cursor: 'pointer',
            }}>
              Retry
            </button>
          </div>
        )}

        {/* Table */}
        {!loading && !error && (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'rgba(255,255,255,0.02)' }}>
                  {['#', 'Email', 'Role', 'Status', 'Joined', 'Actions'].map(h => (
                    <th key={h} style={{
                      padding: '12px 18px', textAlign: h === 'Actions' ? 'center' : 'left',
                      fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)',
                      textTransform: 'uppercase', letterSpacing: '0.08em',
                      borderBottom: '1px solid var(--border-subtle)',
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {users.map((u, idx) => (
                  <tr
                    key={u.user_id}
                    style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      transition: 'background 0.12s ease',
                    }}
                    onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.025)'}
                    onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = 'transparent'}
                  >
                    <td style={{ padding: '14px 18px', color: 'var(--text-dim)', fontSize: '0.8rem' }}>
                      {idx + 1}
                    </td>
                    <td style={{ padding: '14px 18px' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-main)', fontSize: '0.88rem' }}>{u.email}</div>
                      {u.user_id === me?.user_id && (
                        <div style={{ fontSize: '0.68rem', color: 'var(--accent-cyan)', marginTop: '2px' }}>← You</div>
                      )}
                    </td>
                    <td style={{ padding: '14px 18px' }}>
                      <RoleBadge role={u.role} />
                    </td>
                    <td style={{ padding: '14px 18px' }}>
                      <StatusBadge active={u.is_active} />
                    </td>
                    <td style={{ padding: '14px 18px', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      {new Date(u.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}
                    </td>
                    <td style={{ padding: '14px 18px' }}>
                      <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                        <button
                          id={`admin-edit-user-${u.user_id}`}
                          onClick={() => setModal({ mode: 'edit', user: u })}
                          title="Edit user"
                          style={{
                            padding: '6px 12px', borderRadius: '6px', border: '1px solid var(--border-color)',
                            background: 'rgba(0,242,254,0.08)', color: 'var(--accent-cyan)',
                            cursor: 'pointer', fontSize: '0.78rem', fontWeight: 600,
                            display: 'flex', alignItems: 'center', gap: '4px', transition: 'all 0.12s ease',
                          }}
                        >
                          <Edit3 size={12} /> Edit
                        </button>
                        <button
                          id={`admin-delete-user-${u.user_id}`}
                          onClick={() => setDeleteTarget(u)}
                          disabled={u.user_id === me?.user_id}
                          title={u.user_id === me?.user_id ? 'Cannot delete yourself' : 'Delete user'}
                          style={{
                            padding: '6px 12px', borderRadius: '6px', border: '1px solid rgba(255,23,68,0.25)',
                            background: 'rgba(255,23,68,0.08)', color: 'var(--accent-red)',
                            cursor: u.user_id === me?.user_id ? 'not-allowed' : 'pointer',
                            fontSize: '0.78rem', fontWeight: 600, opacity: u.user_id === me?.user_id ? 0.4 : 1,
                            display: 'flex', alignItems: 'center', gap: '4px', transition: 'all 0.12s ease',
                          }}
                        >
                          <Trash2 size={12} /> Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.88rem' }}>
                      No users found. Create one to get started.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
};
