export interface Meter {
  id?: number;
  meter_id: number;
  serial_number?: string;
  meter_number: string;
  manufacturer?: string;
  model?: string;
  meter_model?: string;
  meter_type?: string | null;
  firmware_version?: string | null;
  hardware_revision?: string | null;
  communication_interface?: string;
  communication_protocol?: string;
  port_name?: string;
  baud_rate?: number;
  status?: 'ONLINE' | 'OFFLINE' | 'TESTING' | 'ERROR' | string;
  first_seen?: string | null;
  last_seen?: string | null;
}

export interface LastTestRunSummary {
  test_run_id: number;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  duration_seconds: number | null;
}

// Matches GET /api/meters/{meter_id}/profile exactly (real field names —
// meter_number/meter_model, not the serial_number/model naming the older
// `Meter` interface above uses for a different, pre-existing endpoint).
export interface MeterProfile {
  meter_id: number;
  meter_number: string;
  meter_type: string | null;
  meter_model: string | null;
  manufacturer: string | null;
  firmware_version: string | null;
  hardware_revision: string | null;
  communication_interface: string | null;
  status: string | null;
  first_seen: string | null;
  last_seen: string | null;
  is_online: boolean;
  last_test_run: LastTestRunSummary | null;
  is_certified: boolean;
  total_test_runs: number;
  pass_rate: number;
  avg_duration_seconds: number;
  failures_resolved_count: number;
  total_readings_count: number;
}

export interface MeterReading {
  id: number;
  meter_reading_id?: number;
  meter_id: number;
  obis: string;
  obis_code?: string;
  attribute_index: number;
  value: string;
  raw_value?: string;
  unit: string;
  data_type: string;
  timestamp: string;
  quality: string;
  source: string;
  // Real per-request value from the backend ("mock" | "hardware" | "unknown")
  // — optional since older mock fallback literals in api.ts don't set it.
  data_source?: string;
}

export interface TestSuite {
  id: number;
  suite_id?: number;
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

export type AzureSyncStatus = 'NOT_SYNCED' | 'SYNCED' | 'FAILED' | 'NOT_CONFIGURED' | 'PENDING';

export interface TestStep {
  action: string;
  expected: string;
}

export interface TestCaseDefinition {
  id: number;
  test_case_id?: number;   // backend primary key (alias for id)
  suite_id: number;
  name: string;
  description?: string;
  priority?: string;        // backend field name
  severity?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'; // legacy alias
  obis_target: string;
  action: string;
  expected_result?: string | null;
  expected_value?: string | null;  // legacy alias
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
  priority?: string;        // backend field name
  severity?: string;        // legacy alias
  obis_target?: string;
  action?: string;
  expected_result?: string; // backend field name
  expected_value?: string;  // legacy alias
  timeout_ms?: number;
  test_steps?: TestStep[];
  is_active?: boolean;
}

export interface TestRun {
  id: number;
  test_run_id?: number;
  meter_id: number;
  firmware_version: string;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED' | 'ABORTED' | 'PASSED';
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  duration_seconds: number;
  started_at: string;
  start_time?: string;
  end_time?: string;
  results?: TestResult[];
}

export interface TestResult {
  id: number;
  test_result_id?: number;
  test_name: string;
  status: 'PASS' | 'FAIL' | 'SKIPPED' | 'ERROR';
  duration_ms: number;
  actual_value: string;
  error_message?: string;
}

export interface FailureRecord {
  id: number;
  failure_id?: number;
  meter_id: number;
  firmware_version: string;
  test_case: string;
  test_case_name?: string;
  error_type: string;
  error_code?: string;
  error_message: string;
  case_details?: string;
  severity: string;
  case_severity?: string;
  created_at: string;
}

export interface AnalyticsOverview {
  quality_score: number;
  overall_pass_rate: number;
  total_test_executions: number;
  total_meters_tested: number;
  passed_tests: number;
  failed_tests: number;
  pending_tests?: number;
  avg_duration_seconds: number;
  open_failures?: number;
  critical_failures?: number;
  firmware_stability?: string;
  // Compatibility read-throughs
  overall_quality_score?: number;
  pass_rate_percentage?: number;
  total_test_runs?: number;
  total_tests_executed?: number;
  average_duration_seconds?: number;
}

export interface KnowledgeItem {
  id: number;
  knowledge_item_id?: number;
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

export interface RegressionDetail {
  test_case_id: number;
  test_name: string;
  status_firmware_a: string;
  status_firmware_b: string;
}

export interface RegressionComparison {
  id?: number;
  pass_rate_a?: number;
  pass_rate_b?: number;
  pass_rate_delta?: number;
  regressions_detected?: number;
  regressed_tests?: RegressionDetail[];
  handoff_payload?: any;
  firmware_a: string | {
    version: string;
    pass_rate: number;
    total_tests: number;
    failures: number;
  };
  firmware_b: string | {
    version: string;
    pass_rate: number;
    total_tests: number;
    failures: number;
  };
  comparison?: {
    pass_rate_improvement: string;
    fixed_issues_count: number;
    new_failures_count: number;
    unchanged_failures_count: number;
    fixed_issues_list: string[];
    new_failures_list: string[];
  };
}


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

export interface AnalyticsFirmware {
  firmware_version: string;
  failure_count: number;
  pass_rate?: number;
}

export interface AnalyticsModel {
  model: string;
  failures: number;
  pass_rate?: number;
  tests?: number;
}

export interface AnalyticsTrend {
  date: string;
  passed: number;
  failed: number;
  duration: number;
  passRate?: number;
}

export interface MeterConnectionResult {
  meter_id: number;
  meter_number: string;
  connected: boolean;
  handshake?: any;
}

export interface MeterObjectInfo {
  meter_id?: number;
  obis: string;
  class_id: number;
  name?: string;
  description?: string;
  attributes?: any[];
  methods?: any[];
}

export interface ReportGenerationResult {
  test_run_id: number;
  format: string;
  filename: string;
  filepath: string;
  report_summary: any;
  download_url: string;
}

export interface TestRecommendationResult {
  change_summary: string;
  recommended_suite_name: string;
  total_candidates: number;
  selected_count: number;
  reasoning: string;
}

export interface KnowledgeItemCreateInput {
  title: string;
  problem: string;
  symptoms: string;
  affected_models?: string;
  firmware?: string;
  root_cause: string;
  solution: string;
  fixed_version?: string;
  severity?: string;
  tags?: string;
}

