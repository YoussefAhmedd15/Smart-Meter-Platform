import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { apiService, AuthUser } from '../services/api';
import { getAuthToken, setAuthToken } from '../services/authToken';

interface AuthContextValue {
  token: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  /** False while we're rehydrating a stored token on first load.
   * ProtectedRoute waits for this before deciding to redirect. */
  initialized: boolean;
  /** Returns the signed-in AuthUser so callers can redirect based on role. */
  login: (email: string, password: string) => Promise<AuthUser>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken]           = useState<string | null>(null);
  const [user, setUser]             = useState<AuthUser | null>(null);
  const [initialized, setInit]      = useState<boolean>(false);

  // ── Rehydrate from localStorage on first render ──────────────────────────
  useEffect(() => {
    const stored = getAuthToken();
    if (!stored) {
      setInit(true);
      return;
    }
    // Validate the stored token with the backend (/auth/me).
    // If it's expired or revoked the call will 401 and we clear the token.
    apiService.getMe(stored)
      .then(me => {
        setToken(stored);
        setUser(me);
      })
      .catch(() => {
        // Token is invalid/expired — clear it so the user lands on /login.
        setAuthToken(null);
      })
      .finally(() => setInit(true));
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<AuthUser> => {
    const { access_token } = await apiService.login(email, password);
    const me = await apiService.getMe(access_token);
    setAuthToken(access_token);
    setToken(access_token);
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiService.logout();
    } finally {
      setAuthToken(null);
      setToken(null);
      setUser(null);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token && user),
      initialized,
      login,
      logout,
    }),
    [token, user, initialized, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth() must be used inside an <AuthProvider>.');
  }
  return ctx;
}
