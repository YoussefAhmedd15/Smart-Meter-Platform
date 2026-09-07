import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * UX gate, not the security boundary. The real protection is the backend's
 * Depends(get_current_user) guards (backend/app/main.py) — those are what
 * actually stop an unauthenticated request. This wrapper exists only so a
 * logged-out visitor sees a login form instead of a broken app shell full of
 * 401s; it does not and cannot substitute for the backend checks.
 */
export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, initialized } = useAuth();
  const location = useLocation();

  if (!initialized) {
    return null;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <>{children}</>;
};
