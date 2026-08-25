from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from .database import Base


class Meter(Base):
    __tablename__ = "meters"

    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(String(64), unique=True, index=True, nullable=False)
    manufacturer = Column(String(64), default="Iskraemeco")
    model = Column(String(64), default="AM550-TD1")
    firmware_version = Column(String(64), default="v3.14.2")
    hardware_revision = Column(String(64), default="HW-2.1")
    communication_interface = Column(String(64), default="HDLC_WITH_MODE_E")
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    status = Column(String(32), default="ONLINE")  # ONLINE, OFFLINE, TESTING, ERROR
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    readings = relationship("MeterReading", back_populates="meter", cascade="all, delete-orphan")
    test_runs = relationship("TestRun", back_populates="meter", cascade="all, delete-orphan")
    objects = relationship("MeterObject", back_populates="meter", cascade="all, delete-orphan")


class MeterObject(Base):
    __tablename__ = "meter_objects"

    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(Integer, ForeignKey("meters.id"), nullable=False)
    obis = Column(String(32), index=True, nullable=False)
    class_id = Column(Integer, default=1)
    name = Column(String(128))
    description = Column(Text)
    attributes = Column(JSON, default=list)
    methods = Column(JSON, default=list)

    meter = relationship("Meter", back_populates="objects")


class MeterReading(Base):
    __tablename__ = "meter_readings"

    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(Integer, ForeignKey("meters.id"), nullable=False)
    obis = Column(String(32), index=True, nullable=False)
    attribute_index = Column(Integer, default=2)
    value = Column(String(256))
    raw_value = Column(String(256))
    unit = Column(String(32), default="")
    data_type = Column(String(32), default="DoubleLongUnsigned")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    quality = Column(String(32), default="GOOD")
    source = Column(String(32), default="METER_READ")

    meter = relationship("Meter", back_populates="readings")


class TestSuite(Base):
    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, nullable=False)
    description = Column(Text)
    category = Column(String(64), default="Functional")  # Communication, OBIS, LoadProfile, Voltage, Current, Power
    created_at = Column(DateTime, default=datetime.utcnow)

    test_cases = relationship("TestCase", back_populates="suite", cascade="all, delete-orphan")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    severity = Column(String(32), default="HIGH")  # CRITICAL, HIGH, MEDIUM, LOW
    obis_target = Column(String(32), default="1.0.1.8.0.255")
    expected_value = Column(String(128), nullable=True)
    timeout_ms = Column(Integer, default=5000)

    suite = relationship("TestSuite", back_populates="test_cases")


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(Integer, ForeignKey("meters.id"), nullable=False)
    firmware_version = Column(String(64), nullable=False)
    suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=True)
    status = Column(String(32), default="RUNNING")  # RUNNING, COMPLETED, FAILED, ABORTED
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)

    meter = relationship("Meter", back_populates="test_runs")
    results = relationship("TestResult", back_populates="test_run", cascade="all, delete-orphan")
    logs = relationship("TestLog", back_populates="test_run", cascade="all, delete-orphan")


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=True)
    test_name = Column(String(128), default="Test Case")
    status = Column(String(32), default="PASS")  # PASS, FAIL, SKIPPED, ERROR
    duration_ms = Column(Float, default=0.0)
    expected_value = Column(String(256), nullable=True)
    actual_value = Column(String(256), nullable=True)
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    raw_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    test_run = relationship("TestRun", back_populates="results")
    failures = relationship("FailureRecord", back_populates="test_result", cascade="all, delete-orphan")


class TestLog(Base):
    __tablename__ = "test_logs"

    id = Column(Integer, primary_key=True, index=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(16), default="INFO")  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)

    test_run = relationship("TestRun", back_populates="logs")


class FailureRecord(Base):
    __tablename__ = "failures"

    id = Column(Integer, primary_key=True, index=True)
    test_result_id = Column(Integer, ForeignKey("test_results.id"), nullable=True)
    meter_id = Column(Integer, ForeignKey("meters.id"), nullable=True)
    firmware_version = Column(String(64), nullable=False)
    test_case = Column(String(128), nullable=False)
    error_type = Column(String(64), nullable=False)  # TIMEOUT, READ_FAILED, SNRM_FAILED, etc.
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    solution = Column(Text, nullable=True)
    severity = Column(String(32), default="HIGH")  # CRITICAL, HIGH, MEDIUM, LOW
    similarity_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    test_result = relationship("TestResult", back_populates="failures")


class FirmwareVersion(Base):
    __tablename__ = "firmware_versions"

    id = Column(Integer, primary_key=True, index=True)
    meter_model = Column(String(64), default="AM550-TD1")
    version_string = Column(String(64), unique=True, nullable=False)
    release_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(32), default="RELEASED")  # DRAFT, RELEASED, DEPRECATED
    changelog = Column(Text, nullable=True)


class RegressionRun(Base):
    __tablename__ = "regression_runs"

    id = Column(Integer, primary_key=True, index=True)
    firmware_a = Column(String(64), nullable=False)
    firmware_b = Column(String(64), nullable=False)
    total_tests = Column(Integer, default=0)
    fixed_issues = Column(Integer, default=0)
    new_failures = Column(Integer, default=0)
    unchanged_failures = Column(Integer, default=0)
    pass_rate_change = Column(Float, default=0.0)  # e.g. +2.9%
    created_at = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON, nullable=True)


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
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

    id = Column(Integer, primary_key=True, index=True)
    change_summary = Column(String(256), nullable=False)
    recommended_suite_name = Column(String(128), default="Load Profile & HDLC Regression")
    total_candidates = Column(Integer, default=500)
    selected_count = Column(Integer, default=31)
    reasoning = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AlertRecord(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(Integer, ForeignKey("meters.id"), nullable=True)
    severity = Column(String(32), default="WARNING")  # CRITICAL, WARNING, INFO
    message = Column(Text, nullable=False)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
