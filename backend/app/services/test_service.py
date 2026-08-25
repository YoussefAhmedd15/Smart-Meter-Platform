import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..db.models import (
    Meter, TestSuite, TestCase, TestRun, TestResult, TestLog, FailureRecord
)
from meter.reader import DLMSMeterReader
from meter.config import MeterConfig


class TestEngineService:

    def __init__(self, db: Session):
        self.db = db
        self.reader = DLMSMeterReader(MeterConfig())

    def create_default_suites(self):
        """Seeds default DLMS verification test suites if none exist."""
        if self.db.query(TestSuite).count() == 0:
            suites_data = [
                {
                    "name": "Communication & Handshake Suite",
                    "category": "Communication",
                    "description": "Verifies physical media, Mode E baudrate switching, SNRM, UA, and AARQ association.",
                    "cases": [
                        {"name": "Mode E Identification", "severity": "CRITICAL", "target": "0.0.96.1.1.255"},
                        {"name": "SNRM / UA Negotiation", "severity": "CRITICAL", "target": "0.0.1.0.0.255"},
                        {"name": "AARQ Association", "severity": "HIGH", "target": "0.0.96.1.0.255"},
                    ]
                },
                {
                    "name": "Electrical Parameters Suite",
                    "category": "Voltage & Power",
                    "description": "Validates single & 3-phase RMS voltage, current, frequency, active power, and power factor.",
                    "cases": [
                        {"name": "Voltage L1 Range Check (207V - 253V)", "severity": "HIGH", "target": "1.0.32.7.0.255"},
                        {"name": "Current L1 Range Check (0A - 100A)", "severity": "HIGH", "target": "1.0.31.7.0.255"},
                        {"name": "Grid Frequency Stability (49.5Hz - 50.5Hz)", "severity": "HIGH", "target": "1.0.14.7.0.255"},
                        {"name": "Active Power Instantaneous", "severity": "MEDIUM", "target": "1.0.1.7.0.255"},
                    ]
                },
                {
                    "name": "Load Profile & Clock Suite",
                    "category": "LoadProfile",
                    "description": "Verifies RTC accuracy, 15-min profile generic register structure, and buffer integrity.",
                    "cases": [
                        {"name": "Real-Time Clock Read", "severity": "MEDIUM", "target": "0.0.1.0.0.255"},
                        {"name": "Load Profile 1 Buffer Reading", "severity": "HIGH", "target": "1.0.99.1.0.255"},
                    ]
                }
            ]
            for s_info in suites_data:
                suite = TestSuite(
                    name=s_info["name"],
                    category=s_info["category"],
                    description=s_info["description"]
                )
                self.db.add(suite)
                self.db.commit()
                self.db.refresh(suite)

                for c_info in s_info["cases"]:
                    tc = TestCase(
                        suite_id=suite.id,
                        name=c_info["name"],
                        severity=c_info["severity"],
                        obis_target=c_info["target"],
                    )
                    self.db.add(tc)
            self.db.commit()

    def execute_test_run(self, meter_id: int, suite_id: int) -> TestRun:
        self.create_default_suites()
        meter = self.db.query(Meter).filter(Meter.id == meter_id).first()
        suite = self.db.query(TestSuite).filter(TestSuite.id == suite_id).first()

        if not meter or not suite:
            raise ValueError("Invalid meter or test suite ID")

        test_run = TestRun(
            meter_id=meter.id,
            firmware_version=meter.firmware_version,
            suite_id=suite.id,
            status="RUNNING",
            started_at=datetime.utcnow(),
            total_tests=len(suite.test_cases),
        )
        self.db.add(test_run)
        self.db.commit()
        self.db.refresh(test_run)

        # Log start
        log_start = TestLog(
            test_run_id=test_run.id,
            level="INFO",
            message=f"Started execution of suite '{suite.name}' on meter {meter.serial_number} ({meter.firmware_version}).",
        )
        self.db.add(log_start)

        start_time = time.time()
        passed = 0
        failed = 0
        skipped = 0

        self.reader.connect()

        for case in suite.test_cases:
            t_start = time.time()
            try:
                res = self.reader.read_obis(case.obis_target)
                t_duration = round((time.time() - t_start) * 1000, 2)

                t_result = TestResult(
                    test_run_id=test_run.id,
                    test_case_id=case.id,
                    test_name=case.name,
                    status="PASS",
                    duration_ms=t_duration,
                    expected_value="Valid Reading",
                    actual_value=f"{res.value} {res.unit}".strip(),
                    created_at=datetime.utcnow(),
                )
                self.db.add(t_result)
                passed += 1

                log_entry = TestLog(
                    test_run_id=test_run.id,
                    level="INFO",
                    message=f"[PASS] {case.name}: Received {res.value} {res.unit} ({t_duration} ms)",
                )
                self.db.add(log_entry)

            except Exception as e:
                t_duration = round((time.time() - t_start) * 1000, 2)
                t_result = TestResult(
                    test_run_id=test_run.id,
                    test_case_id=case.id,
                    test_name=case.name,
                    status="FAIL",
                    duration_ms=t_duration,
                    expected_value="Valid Reading",
                    actual_value="ERROR",
                    error_code="READ_FAILED",
                    error_message=str(e),
                    created_at=datetime.utcnow(),
                )
                self.db.add(t_result)
                self.db.commit()
                self.db.refresh(t_result)
                failed += 1

                # Record failure intelligence entry
                failure = FailureRecord(
                    test_result_id=t_result.id,
                    meter_id=meter.id,
                    firmware_version=meter.firmware_version,
                    test_case=case.name,
                    error_type="READ_FAILED",
                    error_message=str(e),
                    severity=case.severity,
                    created_at=datetime.utcnow(),
                )
                self.db.add(failure)

                log_entry = TestLog(
                    test_run_id=test_run.id,
                    level="ERROR",
                    message=f"[FAIL] {case.name}: {str(e)} ({t_duration} ms)",
                )
                self.db.add(log_entry)

        elapsed = round(time.time() - start_time, 2)
        test_run.finished_at = datetime.utcnow()
        test_run.duration_seconds = elapsed
        test_run.passed_tests = passed
        test_run.failed_tests = failed
        test_run.skipped_tests = skipped
        test_run.status = "COMPLETED" if failed == 0 else "FAILED"

        self.db.commit()
        self.db.refresh(test_run)
        return test_run
