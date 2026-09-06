export interface Meter {
  id: number;
  serial_number: string;
  manufacturer: string;
  model: string;
  firmware_version: string;
  hardware_revision: string;
  communication_interface: string;
  status: 'ONLINE' | 'OFFLINE' | 'TESTING' | 'ERROR';
  first_seen: string;
  last_seen: string;
}

export interface MeterReading {
  id: number;
  meter_id: number;
  obis: string;
  attribute_index: number;
  value: string;
  raw_value?: string;
  unit: string;
  data_type: string;
  timestamp: string;
  quality: string;
  source: string;
}

export interface TestSuite {
  id: number;
  name: string;
  category: string;
  description: string;
  total_cases: number;
  azure_plan_id?: number | null;
  azure_suite_id?: number | null;
  azure_sync_status?: AzureSyncStatus;
  azure_sync_error?: string | null;
  azure_last_synced_at?: string | null;
}

export type AzureSyncStatus = 'NOT_SYNCED' | 'SYNCED' | 'FAILED' | 'NOT_CONFIGURED';

export interface TestStep {
  action: string;
  expected: string;
}

export interface TestCaseDefinition {
  id: number;
  suite_id: number;
  name: string;
  description?: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  obis_target: string;
  action: string;
  expected_value?: string | null;
  timeout_ms: number;
  test_steps: TestStep[];
  is_active: boolean;
  azure_test_case_id?: number | null;
  azure_sync_status: AzureSyncStatus;
  azure_sync_error?: string | null;
  azure_last_synced_at?: string | null;
}

export interface TestCaseCreateInput {
  suite_id: number;
  name: string;
  description?: string;
  severity?: string;
  obis_target?: string;
  action?: string;
  expected_value?: string;
  timeout_ms?: number;
  test_steps?: TestStep[];
  is_active?: boolean;
}

export interface TestRun {
  id: number;
  meter_id: number;
  firmware_version: string;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED' | 'ABORTED';
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  duration_seconds: number;
  started_at: string;
  results?: TestResult[];
}

export interface TestResult {
  id: number;
  test_name: string;
  status: 'PASS' | 'FAIL' | 'SKIPPED' | 'ERROR';
  duration_ms: number;
  actual_value: string;
  error_message?: string;
}

export interface FailureRecord {
  id: number;
  meter_id: number;
  firmware_version: string;
  test_case: string;
  error_type: string;
  error_message: string;
  severity: string;
  created_at: string;
}

export interface AnalyticsOverview {
  overall_quality_score: number;
  pass_rate_percentage: number;
  total_meters_tested: number;
  total_test_runs: number;
  total_tests_executed: number;
  passed_tests: number;
  failed_tests: number;
  average_duration_seconds: number;
  open_failures: number;
  critical_failures: number;
  firmware_stability: string;
}

export interface KnowledgeItem {
  id: number;
  title: string;
  problem: string;
  symptoms: string;
  affected_models: string;
  firmware: string;
  root_cause: string;
  solution: string;
  fixed_version: string;
  severity: string;
  tags: string;
}

export interface RegressionComparison {
  id: number;
  firmware_a: {
    version: string;
    pass_rate: number;
    total_tests: number;
    failures: number;
  };
  firmware_b: {
    version: string;
    pass_rate: number;
    total_tests: number;
    failures: number;
  };
  comparison: {
    pass_rate_improvement: string;
    fixed_issues_count: number;
    new_failures_count: number;
    unchanged_failures_count: number;
    fixed_issues_list: string[];
    new_failures_list: string[];
  };
}

export type AzureSyncStatus = 'NOT_SYNCED' | 'SYNCED' | 'FAILED';

export interface TestCase {
  id: number;
  suite_id: number;
  name: string;
  description?: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  obis_target: string;
  expected_value?: string;
  timeout_ms: number;
  azure_sync_status: AzureSyncStatus;
  azure_test_case_id?: number;
  azure_suite_id?: number;
  azure_plan_id?: number;
  azure_synced_at?: string;
  azure_url?: string;
}
