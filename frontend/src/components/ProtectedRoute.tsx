import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * UX gate, not the security boundary. The real protection is the backend's
 * Depends(get_current_user) guards (backend/app/main.py) — those are what
 * actually stop an unauthenticated request. This wrapper exists only so a
 * logged-out visitor sees a login form instead of a broken app shell full of
 * 401s; it does not and cannot substitute for the backend checks.
 *
 * While `initialized` is false the provider is still validating a stored token
 * against /auth/me — show a full-screen spinner rather than flashing /login.
 */
export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, initialized } = useAuth();
  const location = useLocation();

  if (!initialized) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-primary)',
        gap: '16px',
      }}>
        {/* Spinning ring */}
        <div style={{
          width: '44px', height: '44px', borderRadius: '50%',
          border: '3px solid rgba(0,242,254,0.15)',
          borderTop: '3px solid var(--accent-cyan)',
          animation: 'spin 0.8s linear infinite',
        }} />
        <div style={{ color: 'var(--text-dim)', fontSize: '0.84rem' }}>
          Restoring session…
        </div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <>{children}</>;
};
