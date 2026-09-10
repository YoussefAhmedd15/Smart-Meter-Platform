// In-memory access-token store. Deliberately not localStorage/sessionStorage —
// a page refresh losing the session is an accepted tradeoff for not
// persisting a bearer token somewhere readable by any injected script (XSS).
// This is a considered, explicit choice (re-confirmed after a later commit
// incidentally reintroduced localStorage storage without discussion) — do
// not change this without a deliberate decision and a real reason recorded
// here, not as a side effect of an unrelated feature.
let currentToken: string | null = null;

export function setAuthToken(token: string | null): void {
  currentToken = token;
}

export function getAuthToken(): string | null {
  return currentToken;
}
