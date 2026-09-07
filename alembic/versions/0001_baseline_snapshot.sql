CREATE TABLE raw_scdc_cases (
    raw_id SERIAL PRIMARY KEY,
    source_file VARCHAR(100),
    source_year INTEGER,
    account_or_scdc TEXT,
    district TEXT,
    pos TEXT,
    case_type TEXT,
    case_date TEXT,
    meter_number TEXT,
    meter_type TEXT,
    case_details TEXT,
    action_taken TEXT,
    error_code TEXT,
    categories TEXT,
    case_category TEXT,
    case_severity TEXT,
    status TEXT,
    action_owner TEXT,
    comment TEXT,
    fm_team_member TEXT,
    loaded_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE normalized_scdc_cases (
    normalized_id SERIAL PRIMARY KEY,
    raw_id INTEGER UNIQUE REFERENCES raw_scdc_cases(raw_id),
    source_file VARCHAR(100),
    source_year INTEGER,
    account_or_scdc TEXT,
    district TEXT,
    pos TEXT,
    case_type TEXT,
    case_date DATE,
    meter_number TEXT,
    meter_type TEXT,
    case_details TEXT,
    action_taken TEXT,
    error_code TEXT,
    categories TEXT,
    case_category TEXT,
    case_severity TEXT,
    status TEXT,
    action_owner TEXT,
    comment TEXT,
    fm_team_member TEXT,
    normalized_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE firmwares (
    firmware_id SERIAL PRIMARY KEY,
    version VARCHAR(100) UNIQUE NOT NULL,
    release_date DATE,
    notes TEXT,
    status VARCHAR(30) DEFAULT 'RELEASED', -- DRAFT, RELEASED, DEPRECATED
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE meters (
    meter_id SERIAL PRIMARY KEY,
    meter_number VARCHAR(100) UNIQUE NOT NULL,
    meter_type VARCHAR(100),
    meter_model VARCHAR(100), -- specific hardware model, e.g. AM550-TD1 (distinct from meter_type, which is the SCDC field-ops category)
    manufacturer VARCHAR(100) DEFAULT 'Iskraemeco',
    firmware_id INTEGER REFERENCES firmwares(firmware_id),
    hardware_revision VARCHAR(100),
    communication_interface VARCHAR(50) DEFAULT 'HDLC_WITH_MODE_E',
    district VARCHAR(100),
    pos VARCHAR(100),
    status VARCHAR(30) DEFAULT 'ONLINE', -- ONLINE, OFFLINE, TESTING, ERROR
    first_seen TIMESTAMPTZ DEFAULT now(),
    last_seen TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE meter_readings (
    meter_reading_id SERIAL PRIMARY KEY,
    meter_id INTEGER NOT NULL REFERENCES meters(meter_id) ON DELETE CASCADE,
    obis VARCHAR(32) NOT NULL,
    attribute_index INTEGER DEFAULT 2,
    value VARCHAR(256),
    raw_value VARCHAR(256),
    unit VARCHAR(32),
    data_type VARCHAR(32),
    quality VARCHAR(32) DEFAULT 'GOOD',
    source VARCHAR(32) DEFAULT 'METER_READ',
    "timestamp" TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE meter_objects (
    meter_object_id SERIAL PRIMARY KEY,
    meter_id INTEGER NOT NULL REFERENCES meters(meter_id) ON DELETE CASCADE,
    obis VARCHAR(32) NOT NULL,
    class_id INTEGER DEFAULT 1,
    name VARCHAR(128),
    description TEXT,
    attributes JSONB,
    methods JSONB
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) NOT NULL,
    api_token_hash TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE test_suites (
    suite_id SERIAL PRIMARY KEY,
    name VARCHAR(128) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(64) DEFAULT 'Functional', -- Communication, OBIS, LoadProfile, Voltage, Current, Power
    azure_plan_id INTEGER,
    azure_suite_id INTEGER,
    azure_sync_status VARCHAR(16) DEFAULT 'NOT_SYNCED', -- NOT_SYNCED, SYNCED, FAILED, NOT_CONFIGURED
    azure_sync_error TEXT,
    azure_last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE test_cases (
    test_case_id SERIAL PRIMARY KEY,
    suite_id INTEGER REFERENCES test_suites(suite_id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    test_type VARCHAR(50),
    status VARCHAR(30) DEFAULT 'Draft',
    priority VARCHAR(20),
    version INTEGER DEFAULT 1,
    expected_result TEXT,
    obis_target VARCHAR(32), -- OBIS logical name this case reads/writes, e.g. 1.0.1.8.0.255
    action VARCHAR(32) DEFAULT 'READ_OBIS', -- READ_OBIS, WRITE_OBIS, EXECUTE_METHOD
    timeout_ms INTEGER DEFAULT 5000,
    created_by INTEGER REFERENCES users(user_id),
    is_active BOOLEAN DEFAULT TRUE,
    azure_test_case_id INTEGER,
    azure_sync_status VARCHAR(30) DEFAULT 'PENDING',
    azure_last_synced_at TIMESTAMPTZ,
    azure_sync_error TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE test_case_steps (
    step_id SERIAL PRIMARY KEY,
    test_case_id INTEGER NOT NULL REFERENCES test_cases(test_case_id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    name VARCHAR(255),
    action VARCHAR(50),
    description TEXT,
    expected_result TEXT,
    parameters JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (test_case_id, step_number)
);

CREATE TABLE test_case_azure_mapping (
    mapping_id SERIAL PRIMARY KEY,
    test_case_id INTEGER NOT NULL REFERENCES test_cases(test_case_id) ON DELETE CASCADE,
    azure_organization VARCHAR(255),
    azure_project_id VARCHAR(100),
    azure_plan_id INTEGER,
    azure_suite_id INTEGER,
    azure_test_case_id INTEGER,
    sync_status VARCHAR(30) DEFAULT 'PENDING',
    last_synced_at TIMESTAMPTZ,
    last_sync_error TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- A test_run groups the execution of an entire suite against one meter (used by the
-- live Testing Engine). test_executions below remains the flat, ungrouped, one-case-at-
-- a-time execution record used by the data-engineering pipeline; the two coexist because
-- they serve different callers rather than one being a legacy form of the other.
CREATE TABLE test_runs (
    test_run_id SERIAL PRIMARY KEY,
    meter_id INTEGER NOT NULL REFERENCES meters(meter_id),
    firmware_id INTEGER REFERENCES firmwares(firmware_id),
    suite_id INTEGER REFERENCES test_suites(suite_id),
    status VARCHAR(30) DEFAULT 'RUNNING', -- RUNNING, COMPLETED, FAILED, ABORTED
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ,
    duration_seconds DOUBLE PRECISION DEFAULT 0,
    total_tests INTEGER DEFAULT 0,
    passed_tests INTEGER DEFAULT 0,
    failed_tests INTEGER DEFAULT 0,
    skipped_tests INTEGER DEFAULT 0,
    executed_by INTEGER REFERENCES users(user_id)
);

CREATE TABLE test_results (
    test_result_id SERIAL PRIMARY KEY,
    test_run_id INTEGER NOT NULL REFERENCES test_runs(test_run_id) ON DELETE CASCADE,
    test_case_id INTEGER REFERENCES test_cases(test_case_id),
    test_name VARCHAR(255) DEFAULT 'Test Case',
    status VARCHAR(30) DEFAULT 'PASS', -- PASS, FAIL, SKIPPED, ERROR
    duration_ms INTEGER DEFAULT 0,
    expected_value VARCHAR(256),
    actual_value VARCHAR(256),
    error_code VARCHAR(64),
    error_message TEXT,
    raw_response TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE test_logs (
    test_log_id SERIAL PRIMARY KEY,
    test_run_id INTEGER NOT NULL REFERENCES test_runs(test_run_id) ON DELETE CASCADE,
    level VARCHAR(16) DEFAULT 'INFO', -- INFO, WARNING, ERROR, DEBUG
    message TEXT NOT NULL,
    details JSONB,
    "timestamp" TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE test_executions (
    execution_id SERIAL PRIMARY KEY,
    test_case_id INTEGER NOT NULL REFERENCES test_cases(test_case_id),
    meter_id INTEGER NOT NULL REFERENCES meters(meter_id),
    firmware_id INTEGER REFERENCES firmwares(firmware_id),
    status VARCHAR(20),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    executed_by INTEGER REFERENCES users(user_id),
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE test_step_results (
    step_result_id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL REFERENCES test_executions(execution_id) ON DELETE CASCADE,
    step_id INTEGER NOT NULL REFERENCES test_case_steps(step_id),
    status VARCHAR(20),
    actual_result TEXT,
    expected_result TEXT,
    response_data JSONB,
    error_message TEXT,
    duration_ms INTEGER,
    executed_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE test_execution_logs (
    log_id SERIAL PRIMARY KEY,
    execution_id INTEGER NOT NULL REFERENCES test_executions(execution_id) ON DELETE CASCADE,
    step_id INTEGER REFERENCES test_case_steps(step_id),
    log_level VARCHAR(20),
    message TEXT,
    request_data JSONB,
    response_data JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE failures (
    failure_id SERIAL PRIMARY KEY,
    meter_id INTEGER REFERENCES meters(meter_id),
    firmware_id INTEGER REFERENCES firmwares(firmware_id),
    test_case_id INTEGER REFERENCES test_cases(test_case_id),
    test_result_id INTEGER REFERENCES test_results(test_result_id) ON DELETE SET NULL,
    case_type VARCHAR(100),
    case_category VARCHAR(100),
    case_severity VARCHAR(50),
    error_code VARCHAR(100),
    case_details TEXT,
    stack_trace TEXT,
    root_cause TEXT,
    solution TEXT,
    action_taken TEXT,
    status VARCHAR(50),
    action_owner VARCHAR(255),
    district VARCHAR(100),
    pos VARCHAR(100),
    source VARCHAR(20) CHECK (source IN ('scdc_tracker','ado_bug','test_engine')),
    reported_date DATE,
    resolved_date DATE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE failure_fingerprints (
    fingerprint_id SERIAL PRIMARY KEY,
    failure_id INTEGER NOT NULL REFERENCES failures(failure_id) ON DELETE CASCADE,
    meter_model VARCHAR(100),
    firmware VARCHAR(100),
    hardware_revision VARCHAR(100),
    error_code VARCHAR(100),
    normalized_signature TEXT,
    embedding_ref TEXT, -- reserved for a future vector/embedding lookup; not populated or read by any code yet
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE regression_runs (
    regression_run_id SERIAL PRIMARY KEY,
    firmware_a VARCHAR(64) NOT NULL,
    firmware_b VARCHAR(64) NOT NULL,
    total_tests INTEGER DEFAULT 0,
    fixed_issues INTEGER DEFAULT 0,
    new_failures INTEGER DEFAULT 0,
    unchanged_failures INTEGER DEFAULT 0,
    pass_rate_change DOUBLE PRECISION DEFAULT 0,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE knowledge_items (
    knowledge_item_id SERIAL PRIMARY KEY,
    title VARCHAR(256) NOT NULL,
    problem TEXT NOT NULL,
    symptoms TEXT NOT NULL,
    affected_models VARCHAR(128) DEFAULT 'Iskraemeco AM550',
    firmware VARCHAR(128) DEFAULT 'v3.12 - v3.14',
    root_cause TEXT NOT NULL,
    solution TEXT NOT NULL,
    fixed_version VARCHAR(64) DEFAULT 'v3.15.0',
    severity VARCHAR(32) DEFAULT 'HIGH',
    tags VARCHAR(256) DEFAULT 'HDLC, Mode E, Optical',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    change_summary VARCHAR(256) NOT NULL,
    recommended_suite_name VARCHAR(128) DEFAULT 'Load Profile & HDLC Regression',
    total_candidates INTEGER DEFAULT 500,
    selected_count INTEGER DEFAULT 31,
    reasoning TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE dev_bugs (
    bug_id SERIAL PRIMARY KEY,
    ado_id INTEGER UNIQUE NOT NULL,
    work_item_type VARCHAR(50),
    title TEXT,
    assigned_to VARCHAR(255),
    created_by VARCHAR(255),
    state VARCHAR(50),
    tags TEXT,
    resolved_by VARCHAR(255),
    closed_by VARCHAR(255),
    resolved_date TIMESTAMPTZ,
    closed_date TIMESTAMPTZ,
    created_date TIMESTAMPTZ,
    level VARCHAR(10) CHECK (level IN ('L1','L2')),
    loaded_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_meters_firmware_id ON meters(firmware_id);
CREATE INDEX idx_meter_readings_meter_id ON meter_readings(meter_id);
CREATE INDEX idx_meter_readings_timestamp ON meter_readings("timestamp");
CREATE INDEX idx_meter_objects_meter_id ON meter_objects(meter_id);
CREATE INDEX idx_test_cases_suite_id ON test_cases(suite_id);
CREATE INDEX idx_test_runs_meter_id ON test_runs(meter_id);
CREATE INDEX idx_test_results_test_run_id ON test_results(test_run_id);
CREATE INDEX idx_test_logs_test_run_id ON test_logs(test_run_id);
CREATE INDEX idx_failures_meter_id ON failures(meter_id);
CREATE INDEX idx_failures_firmware_id ON failures(firmware_id);
CREATE INDEX idx_failures_reported_date ON failures(reported_date);
CREATE INDEX idx_test_executions_meter_id ON test_executions(meter_id);
CREATE INDEX idx_test_executions_test_case_id ON test_executions(test_case_id);
CREATE INDEX idx_raw_scdc_cases_source_year ON raw_scdc_cases(source_year);
