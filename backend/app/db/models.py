from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date, Text, ForeignKey, JSON,
    CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from .database import Base


# ---------------------------------------------------------------------------
# Mirrors Database/shema.sql, the canonical schema. Table names and primary
# keys follow shema.sql's <entity>_id convention throughout. Where shema.sql
# has no equivalent of an existing app feature (test suites, live telemetry,
# regression history, knowledge base, recommendations), that table has been
# added to shema.sql rather than the feature being dropped.
# ---------------------------------------------------------------------------


class Firmware(Base):
    __tablename__ = "firmwares"

    firmware_id = Column(Integer, primary_key=True, index=True)
    version = Column(String(100), unique=True, nullable=False)
    release_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(30), default="RELEASED")  # DRAFT, RELEASED, DEPRECATED
    created_at = Column(DateTime, default=datetime.utcnow)

    meters = relationship("Meter", back_populates="firmware")


class Meter(Base):
    __tablename__ = "meters"

    meter_id = Column(Integer, primary_key=True, index=True)
    meter_number = Column(String(100), unique=True, index=True, nullable=False)
    meter_type = Column(String(100), nullable=True)
    meter_model = Column(String(100), default="AM550-TD1")
    manufacturer = Column(String(100), default="Iskraemeco")
    firmware_id = Column(Integer, ForeignKey("firmwares.firmware_id"), nullable=True)
    hardware_revision = Column(String(100), default="HW-2.1")
    communication_interface = Column(String(50), default="HDLC_WITH_MODE_E")
    district = Column(String(100), nullable=True)
    pos = Column(String(100), nullable=True)
    status = Column(String(30), default="ONLINE")  # ONLINE, OFFLINE, TESTING, ERROR
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    firmware = relationship("Firmware", back_populates="meters")
    readings = relationship("MeterReading", back_populates="meter", cascade="all, delete-orphan")
    objects = relationship("MeterObject", back_populates="meter", cascade="all, delete-orphan")
    test_runs = relationship("TestRun", back_populates="meter", cascade="all, delete-orphan")

    @property
    def firmware_version(self) -> Optional[str]:
        """Convenience read-through to the linked firmware's version string."""
        return self.firmware.version if self.firmware else None


class MeterReading(Base):
    __tablename__ = "meter_readings"

    meter_reading_id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(Integer, ForeignKey("meters.meter_id"), nullable=False)
    obis = Column(String(32), index=True, nullable=False)
    attribute_index = Column(Integer, default=2)
    value = Column(String(256))
    raw_value = Column(String(256))
    unit = Column(String(32), default="")
    data_type = Column(String(32), default="DoubleLongUnsigned")
    quality = Column(String(32), default="GOOD")
    source = Column(String(32), default="METER_READ")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    meter = relationship("Meter", back_populates="readings")


class MeterObject(Base):
    __tablename__ = "meter_objects"

    meter_object_id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(Integer, ForeignKey("meters.meter_id"), nullable=False)
    obis = Column(String(32), index=True, nullable=False)
    class_id = Column(Integer, default=1)
    name = Column(String(128))
    description = Column(Text)
    attributes = Column(JSON, default=list)
    methods = Column(JSON, default=list)

    meter = relationship("Meter", back_populates="objects")


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    role = Column(String(50), nullable=False)
    api_token_hash = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestSuite(Base):
    __tablename__ = "test_suites"

    suite_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)
    description = Column(Text)
    category = Column(String(64), default="Functional")  # Communication, OBIS, LoadProfile, Voltage, Current, Power
    created_at = Column(DateTime, default=datetime.utcnow)

    # Azure DevOps Test Plans sync state
    azure_plan_id = Column(Integer, nullable=True)
    azure_suite_id = Column(Integer, nullable=True)
    azure_sync_status = Column(String(16), default="NOT_SYNCED")  # NOT_SYNCED, SYNCED, FAILED, NOT_CONFIGURED
    azure_sync_error = Column(Text, nullable=True)
    azure_last_synced_at = Column(DateTime, nullable=True)

    test_cases = relationship("TestCase", back_populates="suite", cascade="all, delete-orphan")


class TestCase(Base):
    __tablename__ = "test_cases"

    test_case_id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("test_suites.suite_id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    test_type = Column(String(50), nullable=True)
    status = Column(String(30), default="Draft")
    priority = Column(String(20), default="HIGH")  # CRITICAL, HIGH, MEDIUM, LOW
    version = Column(Integer, default=1)
    expected_result = Column(Text, nullable=True)
    obis_target = Column(String(32), default="1.0.1.8.0.255")
    action = Column(String(32), default="READ_OBIS")  # READ_OBIS, WRITE_OBIS, EXECUTE_METHOD
    timeout_ms = Column(Integer, default=5000)
    created_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Azure DevOps Test Plans sync state
    azure_test_case_id = Column(Integer, nullable=True)
    azure_sync_status = Column(String(30), default="PENDING")  # PENDING, SYNCED, FAILED, NOT_CONFIGURED
    azure_sync_error = Column(Text, nullable=True)
    azure_last_synced_at = Column(DateTime, nullable=True)

    suite = relationship("TestSuite", back_populates="test_cases")
    steps = relationship(
        "TestCaseStep", back_populates="test_case",
        cascade="all, delete-orphan", order_by="TestCaseStep.step_number"
    )
    azure_mappings = relationship("TestCaseAzureMapping", back_populates="test_case", cascade="all, delete-orphan")

    @property
    def test_steps(self) -> List[dict]:
        """Convenience read-through: normalized `steps` rows as the [{action, expected}, ...]
        shape the API and the Azure sync XML builder already expect."""
        return [{"action": s.action or "", "expected": s.expected_result or ""} for s in self.steps]


class TestCaseStep(Base):
    __tablename__ = "test_case_steps"
    __table_args__ = (UniqueConstraint("test_case_id", "step_number"),)

    step_id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.test_case_id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    name = Column(String(255), nullable=True)
    action = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    expected_result = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    test_case = relationship("TestCase", back_populates="steps")


class TestCaseAzureMapping(Base):
    __tablename__ = "test_case_azure_mapping"

    mapping_id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.test_case_id"), nullable=False)
    azure_organization = Column(String(255), nullable=True)
    azure_project_id = Column(String(100), nullable=True)
    azure_plan_id = Column(Integer, nullable=True)
    azure_suite_id = Column(Integer, nullable=True)
    azure_test_case_id = Column(Integer, nullable=True)
    sync_status = Column(String(30), default="PENDING")
    last_synced_at = Column(DateTime, nullable=True)
    last_sync_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    test_case = relationship("TestCase", back_populates="azure_mappings")


class TestRun(Base):
    """Groups the execution of a whole suite against one meter. See `TestExecution`
    below for the flat, one-case-at-a-time record the data pipeline scripts use —
    the two model different callers, not one legacy form of the other."""
    __tablename__ = "test_runs"

    test_run_id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(Integer, ForeignKey("meters.meter_id"), nullable=False)
    firmware_id = Column(Integer, ForeignKey("firmwares.firmware_id"), nullable=True)
    suite_id = Column(Integer, ForeignKey("test_suites.suite_id"), nullable=True)
    status = Column(String(30), default="RUNNING")  # RUNNING, COMPLETED, FAILED, ABORTED
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    executed_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)

    meter = relationship("Meter", back_populates="test_runs")
    firmware = relationship("Firmware")
    suite = relationship("TestSuite")
    results = relationship("TestResult", back_populates="test_run", cascade="all, delete-orphan")
    logs = relationship("TestLog", back_populates="test_run", cascade="all, delete-orphan")

    @property
    def firmware_version(self) -> Optional[str]:
        return self.firmware.version if self.firmware else None


class TestResult(Base):
    __tablename__ = "test_results"

    test_result_id = Column(Integer, primary_key=True, index=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.test_run_id"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("test_cases.test_case_id"), nullable=True)
    test_name = Column(String(255), default="Test Case")
    status = Column(String(30), default="PASS")  # PASS, FAIL, SKIPPED, ERROR
    duration_ms = Column(Float, default=0.0)
    expected_value = Column(String(256), nullable=True)
    actual_value = Column(String(256), nullable=True)
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    test_run = relationship("TestRun", back_populates="results")
    test_case = relationship("TestCase")
    failures = relationship("FailureRecord", back_populates="test_result", cascade="all, delete-orphan")


class TestLog(Base):
    __tablename__ = "test_logs"

    test_log_id = Column(Integer, primary_key=True, index=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.test_run_id"), nullable=False)
    level = Column(String(16), default="INFO")  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    test_run = relationship("TestRun", back_populates="logs")


class TestExecution(Base):
    """Flat, ungrouped record of one test case executed against one meter —
    the shape the data-engineering pipeline scripts (load_*.py, create_*_analytics.py)
    read and write directly via psycopg2. Not currently used by the FastAPI app."""
    __tablename__ = "test_executions"

    execution_id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.test_case_id"), nullable=False)
    meter_id = Column(Integer, ForeignKey("meters.meter_id"), nullable=False)
    firmware_id = Column(Integer, ForeignKey("firmwares.firmware_id"), nullable=True)
    status = Column(String(20), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    executed_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    step_results = relationship("TestStepResult", back_populates="execution", cascade="all, delete-orphan")
    execution_logs = relationship("TestExecutionLog", back_populates="execution", cascade="all, delete-orphan")


class TestStepResult(Base):
    __tablename__ = "test_step_results"

    step_result_id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("test_executions.execution_id"), nullable=False)
    step_id = Column(Integer, ForeignKey("test_case_steps.step_id"), nullable=False)
    status = Column(String(20), nullable=True)
    actual_result = Column(Text, nullable=True)
    expected_result = Column(Text, nullable=True)
    response_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)

    execution = relationship("TestExecution", back_populates="step_results")


class TestExecutionLog(Base):
    __tablename__ = "test_execution_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("test_executions.execution_id"), nullable=False)
    step_id = Column(Integer, ForeignKey("test_case_steps.step_id"), nullable=True)
    log_level = Column(String(20), nullable=True)
    message = Column(Text, nullable=True)
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    execution = relationship("TestExecution", back_populates="execution_logs")


class FailureRecord(Base):
    __tablename__ = "failures"
    __table_args__ = (
        CheckConstraint("source IN ('scdc_tracker','ado_bug','test_engine')", name="failures_source_check"),
    )

    failure_id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(Integer, ForeignKey("meters.meter_id"), nullable=True)
    firmware_id = Column(Integer, ForeignKey("firmwares.firmware_id"), nullable=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.test_case_id"), nullable=True)
    test_result_id = Column(Integer, ForeignKey("test_results.test_result_id"), nullable=True)
    case_type = Column(String(100), nullable=True)
    case_category = Column(String(100), nullable=True)
    case_severity = Column(String(50), default="HIGH")  # CRITICAL, HIGH, MEDIUM, LOW
    error_code = Column(String(100), nullable=True)
    case_details = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    solution = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)
    action_owner = Column(String(255), nullable=True)
    district = Column(String(100), nullable=True)
    pos = Column(String(100), nullable=True)
    source = Column(String(20), nullable=True)  # scdc_tracker, ado_bug, test_engine
    reported_date = Column(Date, nullable=True)
    resolved_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    meter = relationship("Meter")
    firmware = relationship("Firmware")
    test_case = relationship("TestCase")
    test_result = relationship("TestResult", back_populates="failures")

    @property
    def firmware_version(self) -> Optional[str]:
        return self.firmware.version if self.firmware else None

    @property
    def test_case_name(self) -> Optional[str]:
        return self.test_case.name if self.test_case else None


class FailureFingerprint(Base):
    __tablename__ = "failure_fingerprints"

    fingerprint_id = Column(Integer, primary_key=True, index=True)
    failure_id = Column(Integer, ForeignKey("failures.failure_id"), nullable=False)
    meter_model = Column(String(100), nullable=True)
    firmware = Column(String(100), nullable=True)
    hardware_revision = Column(String(100), nullable=True)
    error_code = Column(String(100), nullable=True)
    normalized_signature = Column(Text, nullable=True)
    # Reserved for a future vector/embedding lookup. Nullable and intentionally
    # unused for now — the AI/RAG direction this would support is a separate,
    # still-open decision. Nothing reads or writes this column yet.
    embedding_ref = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    failure = relationship("FailureRecord")


class RegressionRun(Base):
    __tablename__ = "regression_runs"

    regression_run_id = Column(Integer, primary_key=True, index=True)
    firmware_a = Column(String(64), nullable=False)
    firmware_b = Column(String(64), nullable=False)
    total_tests = Column(Integer, default=0)
    fixed_issues = Column(Integer, default=0)
    new_failures = Column(Integer, default=0)
    unchanged_failures = Column(Integer, default=0)
    pass_rate_change = Column(Float, default=0.0)  # e.g. +2.9%
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    knowledge_item_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    problem = Column(Text, nullable=False)
    symptoms = Column(Text, nullable=False)
    affected_models = Column(String(128), default="Iskraemeco AM550")
    firmware = Column(String(128), default="v3.12 - v3.14")
    root_cause = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    fixed_version = Column(String(64), default="v3.15.0")
    severity = Column(String(32), default="HIGH")
    tags = Column(String(256), default="HDLC, Mode E, Optical")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class TestRecommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(Integer, primary_key=True, index=True)
    change_summary = Column(String(256), nullable=False)
    recommended_suite_name = Column(String(128), default="Load Profile & HDLC Regression")
    total_candidates = Column(Integer, default=500)
    selected_count = Column(Integer, default=31)
    reasoning = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DevBug(Base):
    """Mirrors shema.sql's dev_bugs table (Azure DevOps bug import). Not currently
    read or written by the FastAPI app — included for full schema parity."""
    __tablename__ = "dev_bugs"

    bug_id = Column(Integer, primary_key=True, index=True)
    ado_id = Column(Integer, unique=True, nullable=False)
    work_item_type = Column(String(50), nullable=True)
    title = Column(Text, nullable=True)
    assigned_to = Column(String(255), nullable=True)
    created_by = Column(String(255), nullable=True)
    state = Column(String(50), nullable=True)
    tags = Column(Text, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    closed_by = Column(String(255), nullable=True)
    resolved_date = Column(DateTime, nullable=True)
    closed_date = Column(DateTime, nullable=True)
    created_date = Column(DateTime, nullable=True)
    level = Column(String(10), nullable=True)  # L1, L2
    loaded_at = Column(DateTime, default=datetime.utcnow)


class RawScdcCase(Base):
    """Mirrors shema.sql's raw_scdc_cases table. Not currently read or written
    by the FastAPI app — included for full schema parity."""
    __tablename__ = "raw_scdc_cases"

    raw_id = Column(Integer, primary_key=True, index=True)
    source_file = Column(String(100), nullable=True)
    source_year = Column(Integer, nullable=True)
    account_or_scdc = Column(Text, nullable=True)
    district = Column(Text, nullable=True)
    pos = Column(Text, nullable=True)
    case_type = Column(Text, nullable=True)
    case_date = Column(Text, nullable=True)
    meter_number = Column(Text, nullable=True)
    meter_type = Column(Text, nullable=True)
    case_details = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=True)
    error_code = Column(Text, nullable=True)
    categories = Column(Text, nullable=True)
    case_category = Column(Text, nullable=True)
    case_severity = Column(Text, nullable=True)
    status = Column(Text, nullable=True)
    action_owner = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    fm_team_member = Column(Text, nullable=True)
    loaded_at = Column(DateTime, default=datetime.utcnow)


class NormalizedScdcCase(Base):
    """Mirrors shema.sql's normalized_scdc_cases table. Not currently read or
    written by the FastAPI app — included for full schema parity."""
    __tablename__ = "normalized_scdc_cases"

    normalized_id = Column(Integer, primary_key=True, index=True)
    raw_id = Column(Integer, ForeignKey("raw_scdc_cases.raw_id"), unique=True, nullable=True)
    source_file = Column(String(100), nullable=True)
    source_year = Column(Integer, nullable=True)
    account_or_scdc = Column(Text, nullable=True)
    district = Column(Text, nullable=True)
    pos = Column(Text, nullable=True)
    case_type = Column(Text, nullable=True)
    case_date = Column(Date, nullable=True)
    meter_number = Column(Text, nullable=True)
    meter_type = Column(Text, nullable=True)
    case_details = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=True)
    error_code = Column(Text, nullable=True)
    categories = Column(Text, nullable=True)
    case_category = Column(Text, nullable=True)
    case_severity = Column(Text, nullable=True)
    status = Column(Text, nullable=True)
    action_owner = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    fm_team_member = Column(Text, nullable=True)
    normalized_at = Column(DateTime, default=datetime.utcnow)
