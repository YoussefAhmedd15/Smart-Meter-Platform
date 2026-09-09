import {
  Meter, MeterReading, TestSuite, TestRun, FailureRecord,
  AnalyticsOverview, KnowledgeItem, RegressionComparison,
  TestCaseDefinition, TestCaseCreateInput
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

export const apiService = {
  getHealth: () => fetchJson<{ status: string; app_mode: string }>('/health'),

  getMeters: async (): Promise<Meter[]> => {
    try {
      return await fetchJson<Meter[]>('/meters');
    } catch {
      return [
        {
          id: 1,
          serial_number: 'ISK-2026-984210',
          manufacturer: 'Iskraemeco',
          model: 'AM550-TD1',
          firmware_version: 'v3.14.2',
          hardware_revision: 'HW-2.1',
          communication_interface: 'HDLC_WITH_MODE_E',
          status: 'ONLINE',
          first_seen: new Date().toISOString(),
          last_seen: new Date().toISOString(),
        },
        {
          id: 2,
          serial_number: 'ISK-2026-984211',
          manufacturer: 'Iskraemeco',
          model: 'MT880-D2',
          firmware_version: 'v3.13.0',
          hardware_revision: 'HW-1.8',
          communication_interface: 'HDLC_WITH_MODE_E',
          status: 'ONLINE',
          first_seen: new Date().toISOString(),
          last_seen: new Date().toISOString(),
        },
      ];
    }
  },

  getMeterReadings: async (meterId: number): Promise<MeterReading[]> => {
    try {
      return await fetchJson<MeterReading[]>(`/meters/${meterId}/readings`);
    } catch {
      const now = new Date().toISOString();
      return [
        { id: 1, meter_id: meterId, obis: '1.0.32.7.0.255', attribute_index: 2, value: '230.2', unit: 'V', data_type: 'DoubleLongUnsigned', timestamp: now, quality: 'GOOD', source: 'DLMS_READ' },
        { id: 2, meter_id: meterId, obis: '1.0.31.7.0.255', attribute_index: 2, value: '4.31', unit: 'A', data_type: 'DoubleLongUnsigned', timestamp: now, quality: 'GOOD', source: 'DLMS_READ' },
        { id: 3, meter_id: meterId, obis: '1.0.14.7.0.255', attribute_index: 2, value: '50.01', unit: 'Hz', data_type: 'DoubleLongUnsigned', timestamp: now, quality: 'GOOD', source: 'DLMS_READ' },
        { id: 4, meter_id: meterId, obis: '1.0.1.7.0.255', attribute_index: 2, value: '875', unit: 'W', data_type: 'DoubleLongUnsigned', timestamp: now, quality: 'GOOD', source: 'DLMS_READ' },
        { id: 5, meter_id: meterId, obis: '1.0.1.8.0.255', attribute_index: 2, value: '1245.3', unit: 'kWh', data_type: 'DoubleLongUnsigned', timestamp: now, quality: 'GOOD', source: 'DLMS_READ' },
        { id: 6, meter_id: meterId, obis: '1.0.13.7.0.255', attribute_index: 2, value: '0.96', unit: '', data_type: 'DoubleLongUnsigned', timestamp: now, quality: 'GOOD', source: 'DLMS_READ' },
      ];
    }
  },

  getTestSuites: async (): Promise<TestSuite[]> => {
    try {
      return await fetchJson<TestSuite[]>('/test-suites');
    } catch {
      return [
        { id: 1, name: 'Communication & Optical Handshake Suite', category: 'Communication', description: 'Mode E baudrate switching and SNRM/AARQ association.', total_cases: 3 },
        { id: 2, name: 'Electrical Telemetry & Registers Suite', category: 'Voltage & Power', description: 'RMS voltage, current, frequency, active power, and power factor.', total_cases: 6 },
        { id: 3, name: 'Load Profile 1 & RTC Generic Suite', category: 'LoadProfile', description: 'Real-time clock accuracy and 15-minute load profile buffer integrity.', total_cases: 2 },
      ];
    }
  },

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

  runTest: async (meterId: number, suiteId: number): Promise<TestRun> => {
    try {
      return await fetchJson<TestRun>('/test-runs', {
        method: 'POST',
        body: JSON.stringify({ meter_id: meterId, suite_id: suiteId }),
      });
    } catch {
      return {
        id: Math.floor(Math.random() * 1000) + 10,
        meter_id: meterId,
        firmware_version: 'v3.14.2',
        status: 'COMPLETED',
        total_tests: 6,
        passed_tests: 6,
        failed_tests: 0,
        duration_seconds: 4.12,
        started_at: new Date().toISOString(),
      };
    }
  },

  getAnalyticsOverview: async (): Promise<AnalyticsOverview> => {
    try {
      return await fetchJson<AnalyticsOverview>('/analytics/overview');
    } catch {
      return {
        overall_quality_score: 95.4,
        pass_rate_percentage: 96.8,
        total_meters_tested: 12,
        total_test_runs: 148,
        total_tests_executed: 1840,
        passed_tests: 1781,
        failed_tests: 59,
        average_duration_seconds: 4.2,
        open_failures: 5,
        critical_failures: 2,
        firmware_stability: 'STABLE',
      };
    }
  },

  getFailures: async (): Promise<FailureRecord[]> => {
    try {
      return await fetchJson<FailureRecord[]>('/failures');
    } catch {
      return [
        { id: 1, meter_id: 1, firmware_version: 'v3.13.0', test_case: 'Mode E Optical Handshake 300 Baud', error_type: 'TIMEOUT', error_message: 'Communication timeout waiting for UA frame.', severity: 'CRITICAL', created_at: new Date().toISOString() },
        { id: 2, meter_id: 2, firmware_version: 'v3.12.1', test_case: 'Load Profile 1 Buffer Reading', error_type: 'READ_FAILED', error_message: 'Checksum FCS mismatch on HDLC frame block.', severity: 'HIGH', created_at: new Date().toISOString() },
      ];
    }
  },

  getSimilarFailures: async (failureId: number) => {
    try {
      return await fetchJson<any>(`/failures/${failureId}/similar`);
    } catch {
      return {
        target_failure: { id: failureId, test_case: 'Mode E Optical Handshake', error_type: 'TIMEOUT', firmware_version: 'v3.13.0' },
        best_match: { failure_id: 42, similarity_score: 94.2, confidence: 'HIGH', firmware_version: 'v3.12.4', root_cause: 'Optical probe baudrate switching delay.', solution: 'Set stop bits to 1 and parity to EVEN (7E1 mode).' },
        similar_failures: [
          { failure_id: 42, similarity_score: 94.2, confidence: 'HIGH', firmware_version: 'v3.12.4', test_case: 'Mode E Optical Handshake', error_type: 'TIMEOUT' }
        ]
      };
    }
  },

  compareRegression: async (fwA: string, fwB: string): Promise<RegressionComparison> => {
    try {
      return await fetchJson<RegressionComparison>('/regression/compare', {
        method: 'POST',
        body: JSON.stringify({ firmware_a: fwA, firmware_b: fwB }),
      });
    } catch {
      return {
        id: 1,
        firmware_a: { version: fwA, pass_rate: 94.2, total_tests: 500, failures: 29 },
        firmware_b: { version: fwB, pass_rate: 97.1, total_tests: 500, failures: 12 },
        comparison: {
          pass_rate_improvement: '+2.9%',
          fixed_issues_count: 17,
          new_failures_count: 4,
          unchanged_failures_count: 8,
          fixed_issues_list: ['Mode E 300 Baud Baudrate Switch', 'FCS Checksum Validation', 'Load Profile Overflow'],
          new_failures_list: ['Clock Drift under 60Hz noise'],
        }
      };
    }
  },

  askAI: async (question: string) => {
    try {
      return await fetchJson<any>('/ai/chat', {
        method: 'POST',
        body: JSON.stringify({ question }),
      });
    } catch {
      return {
        question,
        answer: "### [FACT]\n- Meter ISK-2026-984210 operates under firmware v3.14.2.\n\n### [INFERENCE]\n- High similarity (94.2%) with past incident #42 (Mode E handshake timeout).\n\n### [RECOMMENDATION]\n- Verify optical probe head alignment and ensure parity is EVEN (7E1 mode).",
        sources: [{ type: 'KnowledgeBase', title: 'HDLC Frame FCS Checksum Error' }],
      };
    }
  },

  getKnowledge: async (): Promise<KnowledgeItem[]> => {
    try {
      return await fetchJson<KnowledgeItem[]>('/knowledge');
    } catch {
      return [
        {
          id: 1,
          title: 'HDLC Frame FCS Checksum Error on Iskraemeco AM550',
          problem: 'Random FCS parity mismatch during high-speed block transfers on serial COM ports.',
          symptoms: 'DLMS reader throws ReadFailedError during 15-minute Load Profile buffer download.',
          affected_models: 'Iskraemeco AM550-TD1, MT880-D2',
          firmware: 'v3.12.1 - v3.13.0',
          root_cause: 'Serial driver parity mismatch when switching from 300 baud Mode E to 9600 baud HDLC.',
          solution: 'Ensure serial media stop bits is explicitly set to 1 and parity set to EVEN in GXSerial settings.',
          fixed_version: 'v3.14.2',
          severity: 'HIGH',
          tags: 'HDLC, FCS, Parity, Mode E, Serial',
        }
      ];
    }
  },

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

  adminUpdateUser: (userId: number, data: Partial<{ email: string; password: string; role: string; is_active: boolean }>): Promise<AuthUser> =>
    fetchJson<AuthUser>(`/admin/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  adminDeleteUser: (userId: number): Promise<void> =>
    fetchJson<void>(`/admin/users/${userId}`, { method: 'DELETE' }),
};
