import {
  Meter, MeterReading, MeterProfile, TestSuite, TestRun, FailureRecord,
  AnalyticsOverview, KnowledgeItem, RegressionComparison,
  TestCaseDefinition, TestCaseCreateInput,
  AnalyticsFirmware, AnalyticsModel, AnalyticsTrend,
} from '../types';
import { getAuthToken } from './authToken';

const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const token = getAuthToken();
    const res = await fetch(`${API_BASE}${url}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...options,
    });
    if (!res.ok) {
      // Try to parse error detail from body, fall back to status text.
      const errBody = await res.text();
      let message = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const parsed = JSON.parse(errBody);
        if (parsed?.detail) message = typeof parsed.detail === 'string' ? parsed.detail : message;
      } catch { /* ignore */ }
      throw new Error(message);
    }
    // 204 No Content (e.g. DELETE) — body is empty, nothing to parse.
    if (res.status === 204) return undefined as T;
    const text = await res.text();
    return text ? JSON.parse(text) as T : undefined as T;
  } catch (err) {
    console.warn(`API call to ${url} failed:`, err);
    throw err;
  }
}

/**
 * For auth calls specifically (register/login/logout/me) — unlike fetchJson,
 * this never falls back to mock data on failure. A 401 here is real
 * information the UI must show (e.g. "wrong password"), not something to
 * paper over with a fake success. Parses the backend's actual error `detail`
 * so the UI can display it verbatim rather than a generic message.
 */
async function authFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const body = await res.json().catch(() => ({} as any));
  if (!res.ok) {
    const detail = body && typeof body === 'object' ? (body as any).detail : undefined;
    const message = typeof detail === 'string' ? detail : `HTTP ${res.status}: ${res.statusText}`;
    throw new Error(message);
  }
  return body as T;
}

export interface AuthUser {
  user_id: number;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// The PAT is deliberately absent — it never leaves the backend. org/project
// are not secret, safe to display read-only.
export interface AzureConnectionStatus {
  configured: boolean;
  connected: boolean;
  org: string | null;
  project: string | null;
}

export const apiService = {
  getHealth: () => fetchJson<{ status: string; app_mode: string }>('/health'),

  getMeters: (): Promise<Meter[]> =>
    fetchJson<Meter[]>('/meters'),

  getMeterReadings: (meterId: number): Promise<MeterReading[]> =>
    fetchJson<MeterReading[]>(`/meters/${meterId}/readings`),

  // Real call only, no mock fallback — used by LiveMeter.tsx to show the
  // real meter.status on initial load, before any connect/disconnect click.
  getMeter: (meterId: number): Promise<Meter> =>
    fetchJson<Meter>(`/meters/${meterId}`),

  // Real call only, no mock fallback — MeterProfile.tsx's whole point is
  // showing a real online/certified state; silently falling back to fake
  // numbers on a fetch failure would defeat that.
  getMeterProfile: (meterId: number): Promise<MeterProfile> =>
    fetchJson<MeterProfile>(`/meters/${meterId}/profile`),

  // Real calls only, no mock fallback — used by LiveMeter.tsx specifically,
  // where a fetch failure must surface as a real disconnected/error state
  // rather than silently rendering fake numbers that look live. This does
  // not replace getMeterReadings above, which other callers may still rely
  // on for its mock fallback.
  getMeterReadingsOrThrow: (meterId: number): Promise<MeterReading[]> =>
    fetchJson<MeterReading[]>(`/meters/${meterId}/readings`),

  connectMeter: (meterId: number): Promise<{
    meter_id: number; meter_number: string; connected: boolean; handshake: any; data_source: string;
  }> =>
    fetchJson(`/meters/${meterId}/connect`, { method: 'POST' }),

  disconnectMeter: (meterId: number): Promise<{
    meter_id: number; meter_number: string; disconnected: boolean; status: string;
  }> =>
    fetchJson(`/meters/${meterId}/disconnect`, { method: 'POST' }),

  getTestSuites: (): Promise<TestSuite[]> =>
    fetchJson<TestSuite[]>('/test-suites'),

  getTestCases: (suiteId?: number): Promise<TestCaseDefinition[]> =>
    fetchJson<TestCaseDefinition[]>(suiteId ? `/test-cases?suite_id=${suiteId}` : '/test-cases'),

  createTestCase: (data: TestCaseCreateInput): Promise<TestCaseDefinition> =>
    fetchJson<TestCaseDefinition>('/test-cases', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateTestCase: (caseId: number, data: Partial<TestCaseCreateInput>): Promise<TestCaseDefinition> =>
    fetchJson<TestCaseDefinition>(`/test-cases/${caseId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteTestCase: (caseId: number): Promise<void> =>
    fetchJson<void>(`/test-cases/${caseId}`, { method: 'DELETE' }),

  retrySyncTestCase: (caseId: number): Promise<TestCaseDefinition> =>
    fetchJson<TestCaseDefinition>(`/test-cases/${caseId}/sync-azure`, {
      method: 'POST',
    }),

  getTestRun: (runId: number): Promise<any> =>
    fetchJson<any>(`/test-runs/${runId}`),

  getTestRuns: (): Promise<TestRun[]> =>
    fetchJson<TestRun[]>('/test-runs'),

  runTest: (meterId: number, suiteId: number): Promise<TestRun> =>
    fetchJson<TestRun>('/test-runs', {
      method: 'POST',
      body: JSON.stringify({ meter_id: meterId, suite_id: suiteId }),
    }),

  getAnalyticsOverview: (): Promise<AnalyticsOverview> =>
    fetchJson<AnalyticsOverview>('/analytics/overview'),

  getAnalyticsFirmware: (): Promise<AnalyticsFirmware[]> =>
    fetchJson<AnalyticsFirmware[]>('/analytics/firmware'),

  getAnalyticsModels: (): Promise<AnalyticsModel[]> =>
    fetchJson<AnalyticsModel[]>('/analytics/models'),

  getAnalyticsTrends: (): Promise<AnalyticsTrend[]> =>
    fetchJson<AnalyticsTrend[]>('/analytics/trends'),

  getFailures: (): Promise<FailureRecord[]> =>
    fetchJson<FailureRecord[]>('/failures'),

  getSimilarFailures: (failureId: number) =>
    fetchJson<any>(`/failures/${failureId}/similar`),

  compareRegression: (fwA: string, fwB: string): Promise<RegressionComparison> =>
    fetchJson<RegressionComparison>('/regression/compare', {
      method: 'POST',
      body: JSON.stringify({ firmware_a: fwA, firmware_b: fwB }),
    }),

  askAI: (question: string) =>
    fetchJson<any>('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ question }),
    }),

  getKnowledge: (): Promise<KnowledgeItem[]> =>
    fetchJson<KnowledgeItem[]>('/knowledge'),

  // --- Auth: real calls only, no mock fallback (see authFetch above) ---

  register: (email: string, password: string): Promise<AuthUser> =>
    authFetch<AuthUser>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string): Promise<TokenResponse> =>
    authFetch<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  logout: (): Promise<{ detail: string }> =>
    authFetch<{ detail: string }>('/auth/logout', { method: 'POST' }),

  getMe: (token: string): Promise<AuthUser> =>
    authFetch<AuthUser>('/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    }),

  // --- Admin: user management (admin role required) ---

  adminListUsers: (): Promise<AuthUser[]> =>
    fetchJson<AuthUser[]>('/admin/users'),

  adminCreateUser: (email: string, password: string, role: string): Promise<AuthUser> =>
    fetchJson<AuthUser>('/admin/users', {
      method: 'POST',
      body: JSON.stringify({ email, password, role }),
    }),

  adminUpdateUser: (
    userId: number,
    data: Partial<{ email: string; password: string; role: string; is_active: boolean }>
  ): Promise<AuthUser> =>
    fetchJson<AuthUser>(`/admin/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  adminDeleteUser: (userId: number): Promise<void> =>
    fetchJson<void>(`/admin/users/${userId}`, { method: 'DELETE' }),

  // --- Settings: read-only status, server-side-configured values only ---

  getAzureConnectionStatus: (): Promise<AzureConnectionStatus> =>
    fetchJson<AzureConnectionStatus>('/settings/azure-connection-status'),

  // --- Reports: real calls only, no mock fallback ---

  generateReport: (
    runId: number,
    formatType: string = 'pdf'
  ): Promise<{ filename: string; download_url: string }> =>
    authFetch<{ filename: string; download_url: string }>(
      `/reports/test-run/${runId}?format_type=${encodeURIComponent(formatType)}`,
      { method: 'POST' },
    ),

  downloadReportFile: async (downloadUrl: string): Promise<Blob> => {
    const res = await fetch(downloadUrl);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return res.blob();
  },
};
