import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { apiService, AuthUser } from '../services/api';
import { setAuthToken } from '../services/authToken';

interface AuthContextValue {
  token: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  /** True once we know whether there's a session or not. Always true here —
   * the token lives in memory only (see authToken.ts), so there's no
   * persisted session to rehydrate on load and nothing async to wait on.
   * Kept as a real flag (not hardcoded true at every call site) so
   * ProtectedRoute has a stable thing to check rather than an implicit
   * assumption, and so this doesn't need to change shape if persistence
   * is ever added later. */
  initialized: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [initialized] = useState<boolean>(true);

  const login = useCallback(async (email: string, password: string) => {
    // The JWT itself only carries `sub`/`role` (see backend/app/core/security.py)
    // — not email — so /auth/me is the real source for "the decoded user".
    const { access_token } = await apiService.login(email, password);
    const me = await apiService.getMe(access_token);
    setAuthToken(access_token);
    setToken(access_token);
    setUser(me);
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
