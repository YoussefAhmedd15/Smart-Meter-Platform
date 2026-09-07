// In-memory access-token store. Deliberately not localStorage/sessionStorage —
// a page refresh losing the session is an accepted tradeoff for not
// persisting a bearer token somewhere readable by any injected script (XSS).
//
// api.ts (a plain module, can't use React hooks) reads the current token from
// here on every outgoing request. AuthContext is the only writer — it calls
// setAuthToken() whenever its own React state changes (login, logout), so
// this stays a thin mirror of the context's state, not a second source of
// truth.
let currentToken: string | null = null;

export function setAuthToken(token: string | null): void {
  currentToken = token;
}

export function getAuthToken(): string | null {
  return currentToken;
}
