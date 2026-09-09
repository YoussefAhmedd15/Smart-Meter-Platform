// Token store — reads/writes localStorage so the session survives page refreshes.
// Still a thin module (not a React hook) so api.ts can import it without issue.
// AuthContext is the only writer.

const TOKEN_KEY = 'smp_auth_token';

export function setAuthToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function getAuthToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
