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
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE meters (
    meter_id SERIAL PRIMARY KEY,
    meter_number VARCHAR(100) UNIQUE NOT NULL,
    meter_type VARCHAR(100),
    firmware_id INTEGER REFERENCES firmwares(firmware_id),
    hardware_revision VARCHAR(100),
    district VARCHAR(100),
    pos VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now()
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

CREATE TABLE test_cases (
    test_case_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    test_type VARCHAR(50),
    status VARCHAR(30) DEFAULT 'Draft',
    priority VARCHAR(20),
    version INTEGER DEFAULT 1,
    expected_result TEXT,
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
    case_type VARCHAR(100),
    case_category VARCHAR(100),
    case_severity VARCHAR(50),
    error_code VARCHAR(100),
    case_details TEXT,
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
    embedding_ref TEXT,
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

CREATE INDEX idx_failures_meter_id ON failures(meter_id);
CREATE INDEX idx_failures_firmware_id ON failures(firmware_id);
CREATE INDEX idx_failures_reported_date ON failures(reported_date);
CREATE INDEX idx_test_executions_meter_id ON test_executions(meter_id);
CREATE INDEX idx_test_executions_test_case_id ON test_executions(test_case_id);
CREATE INDEX idx_raw_scdc_cases_source_year ON raw_scdc_cases(source_year);

