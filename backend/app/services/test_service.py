import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from ..db.models import (
    Meter, TestSuite, TestCase, TestRun, TestResult, TestLog, FailureRecord
)
from meter.reader import DLMSMeterReader
from meter.config import MeterConfig

logger = logging.getLogger("smart_meter_api")


def _numeric(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value))


def _compare_exact(expected: dict, res: Any) -> Tuple[bool, str]:
    actual_str = str(res.value)
    return actual_str == str(expected.get("value")), actual_str


def _compare_range(expected: dict, res: Any) -> Tuple[bool, str]:
    try:
        actual_num = _numeric(res.value)
    except (TypeError, ValueError):
        return False, f"{res.value} {res.unit}".strip()
    passed = expected.get("min") <= actual_num <= expected.get("max")
    return passed, f"{actual_num} {res.unit}".strip()


def _compare_freshness(expected: dict, res: Any) -> Tuple[bool, str]:
    max_age = expected.get("max_age_seconds", 60)
    try:
        ts = datetime.fromisoformat(str(res.value).rstrip("Z"))
        age = abs((datetime.utcnow() - ts).total_seconds())
        passed = age <= max_age
    except (TypeError, ValueError):
        passed = False
    return passed, str(res.value)


def _summarize(value: Any) -> str:
    """TestResult.actual_value is a String(256) column — a raw str() of a
    multi-record load-profile buffer would overflow it, so structural checks
    report a short summary instead of the full structure."""
    if isinstance(value, (list, dict)):
        return f"{len(value)} record(s)"
    return str(value)[:256]


def _compare_structural(expected: dict, res: Any) -> Tuple[bool, str]:
    check = expected.get("check", "non_empty")
    value = res.value
    if check == "non_empty":
        passed = len(value) > 0 if isinstance(value, (list, dict, str)) else value is not None
    else:
        passed = False
    return passed, _summarize(value)


_COMPARATORS = {
    "exact": _compare_exact,
    "range": _compare_range,
    "freshness": _compare_freshness,
    "structural": _compare_structural,
}


def _describe_expected(case: TestCase) -> str:
    """Human-readable expected value for TestResult.expected_value — used on
    PASS, FAIL-by-mismatch, and FAIL-by-exception alike, so a failed read
    still shows what the case actually expected, not just "ERROR"."""
    raw = case.expected_result
    if not raw:
        return "Valid Reading"
    try:
        expected = json.loads(raw)
        t = expected.get("type")
    except (ValueError, TypeError, AttributeError):
        return "Valid Reading"
    if t == "exact":
        return str(expected.get("value"))
    if t == "range":
        return f"{expected.get('min')} - {expected.get('max')} {expected.get('unit', '')}".strip()
    if t == "freshness":
        return f"within {expected.get('max_age_seconds', 60)}s of now"
    if t == "structural":
        return f"structural: {expected.get('check', 'non_empty')}"
    return "Valid Reading"


def _evaluate(case: TestCase, res: Any) -> Tuple[bool, str]:
    """Returns (passed, actual_value_str). Falls back to the old
    reachability-only behavior (always PASS if the read didn't throw) when
    expected_result is missing or unparseable/has an unknown type — so a
    case someone adds later without setting expected_result doesn't crash
    the whole run, it just doesn't get a real comparison yet."""
    raw = case.expected_result
    actual_fallback = f"{_summarize(res.value)} {res.unit}".strip()
    if not raw:
        return True, actual_fallback
    try:
        expected = json.loads(raw)
        comparator = _COMPARATORS[expected["type"]]
    except (ValueError, KeyError, TypeError) as e:
        logger.warning(
            f"TestCase {case.test_case_id} ({case.name}) has an unparseable or "
            f"unknown-type expected_result ({raw!r}): {e}. Falling back to "
            f"reachability-only PASS/FAIL for this case."
        )
        return True, actual_fallback
    return comparator(expected, res)


class TestEngineService:

    def __init__(self, db: Session):
        self.db = db
        self.reader = DLMSMeterReader(MeterConfig())

    def create_default_suites(self):
        """Seeds default DLMS verification test suites if none exist.

        TODO(schema-reconciliation): this still seeds from hardcoded Python
        literals instead of reading the real `test_cases` catalog the Data &
        Analytics pipeline populates in Postgres. Now that `test_cases` has a
        `suite_id` FK and matches the canonical schema, this should be rewired
        to read existing suites/cases from the database instead of creating
        its own fixed set. Deliberately left alone here — that's a follow-up
        owned by the Testing Engine work, not part of the schema reconciliation.
        """
        if self.db.query(TestSuite).count() == 0:
            suites_data = [
                {
                    "name": "Communication & Handshake Suite",
                    "category": "Communication",
                    "description": "Verifies physical media, Mode E baudrate switching, SNRM, UA, and AARQ association.",
                    "cases": [
                        {
                            "name": "Mode E Identification", "priority": "CRITICAL", "target": "0.0.96.1.1.255",
                            # Exact match against MockMeterAdapter.serial_number (meter/mock_meter.py).
                            "expected": {"type": "exact", "value": "ISK-2026-984210"},
                        },
                        {
                            "name": "SNRM / UA Negotiation", "priority": "CRITICAL", "target": "0.0.96.1.1.255",
                            # This is an HDLC data-link-layer handshake, not a COSEM/application-layer
                            # object — there is no OBIS logical name for it. It previously reused
                            # 0.0.1.0.0.255 (the Clock object's real, standard logical name — see
                            # meter/obis.py's COMMON_OBIS_CODES, which already labels that code
                            # "Clock / Real Time"), colliding with Real-Time Clock Read below. Moved
                            # here to the Serial Number OBIS instead: reading the device identifier
                            # right after the handshake is a real, common way to confirm the
                            # association is actually usable. Real-Time Clock Read keeps the
                            # standard clock OBIS unchanged, since that one was already correct.
                            "expected": {"type": "structural", "check": "non_empty"},
                        },
                        {
                            "name": "AARQ Association", "priority": "HIGH", "target": "0.0.96.1.0.255",
                            # Exact match against MockMeterAdapter.firmware_version.
                            "expected": {"type": "exact", "value": "v3.14.2"},
                        },
                    ]
                },
                {
                    "name": "Electrical Parameters Suite",
                    "category": "Voltage & Power",
                    "description": "Validates single & 3-phase RMS voltage, current, frequency, active power, and power factor.",
                    "cases": [
                        {
                            "name": "Voltage L1 Range Check (207V - 253V)", "priority": "HIGH", "target": "1.0.32.7.0.255",
                            "expected": {"type": "range", "min": 207, "max": 253, "unit": "V"},
                        },
                        {
                            "name": "Current L1 Range Check (0A - 100A)", "priority": "HIGH", "target": "1.0.31.7.0.255",
                            "expected": {"type": "range", "min": 0, "max": 100, "unit": "A"},
                        },
                        {
                            "name": "Grid Frequency Stability (49.5Hz - 50.5Hz)", "priority": "HIGH", "target": "1.0.14.7.0.255",
                            "expected": {"type": "range", "min": 49.5, "max": 50.5, "unit": "Hz"},
                        },
                        {
                            "name": "Active Power Instantaneous", "priority": "MEDIUM", "target": "1.0.1.7.0.255",
                            # 100-2000W: a plausible instantaneous active-power range for a single
                            # residential/small-commercial connection on this meter class (base load
                            # up to a few kW of simultaneous appliance use) — not the mock's own
                            # 850-900W jitter band, which the mock's output simply happens to fall
                            # inside, the same way a real meter's reading would.
                            "expected": {"type": "range", "min": 100, "max": 2000, "unit": "W"},
                        },
                    ]
                },
                {
                    "name": "Load Profile & Clock Suite",
                    "category": "LoadProfile",
                    "description": "Verifies RTC accuracy, 15-min profile generic register structure, and buffer integrity.",
                    "cases": [
                        {
                            "name": "Real-Time Clock Read", "priority": "MEDIUM", "target": "0.0.1.0.0.255",
                            "expected": {"type": "freshness", "max_age_seconds": 60},
                        },
                        {
                            "name": "Load Profile 1 Buffer Reading", "priority": "HIGH", "target": "1.0.99.1.0.255",
                            "expected": {"type": "structural", "check": "non_empty"},
                        },
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
                        suite_id=suite.suite_id,
                        name=c_info["name"],
                        priority=c_info["priority"],
                        obis_target=c_info["target"],
                        expected_result=json.dumps(c_info["expected"]),
                    )
                    self.db.add(tc)
            self.db.commit()

    def execute_test_run(self, meter_id: int, suite_id: int) -> TestRun:
        meter = self.db.query(Meter).filter(Meter.meter_id == meter_id).first()
        suite = self.db.query(TestSuite).filter(TestSuite.suite_id == suite_id).first()

        if not meter or not suite:
            raise ValueError("Invalid meter or test suite ID")

        test_run = TestRun(
            meter_id=meter.meter_id,
            firmware_id=meter.firmware_id,
            suite_id=suite.suite_id,
            status="RUNNING",
            started_at=datetime.utcnow(),
            total_tests=len(suite.test_cases),
        )
        self.db.add(test_run)
        self.db.commit()
        self.db.refresh(test_run)

        # Log start
        log_start = TestLog(
            test_run_id=test_run.test_run_id,
            level="INFO",
            message=f"Started execution of suite '{suite.name}' on meter {meter.meter_number} ({meter.firmware_version}).",
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

                case_passed, actual_str = _evaluate(case, res)
                expected_str = _describe_expected(case)

                t_result = TestResult(
                    test_run_id=test_run.test_run_id,
                    test_case_id=case.test_case_id,
                    test_name=case.name,
                    status="PASS" if case_passed else "FAIL",
                    duration_ms=t_duration,
                    expected_value=expected_str,
                    actual_value=actual_str,
                    created_at=datetime.utcnow(),
                )
                self.db.add(t_result)

                if case_passed:
                    passed += 1

                    log_entry = TestLog(
                        test_run_id=test_run.test_run_id,
                        level="INFO",
                        message=f"[PASS] {case.name}: Received {actual_str} ({t_duration} ms)",
                    )
                    self.db.add(log_entry)
                else:
                    self.db.commit()
                    self.db.refresh(t_result)
                    failed += 1

                    # A successful read that doesn't match its expected_result is a
                    # real assertion failure, not a communication error — distinct
                    # error_code from the except-branch's READ_FAILED below.
                    failure = FailureRecord(
                        test_result_id=t_result.test_result_id,
                        meter_id=meter.meter_id,
                        firmware_id=meter.firmware_id,
                        test_case_id=case.test_case_id,
                        case_severity=case.priority,
                        error_code="ASSERTION_FAILED",
                        case_details=f"Expected {expected_str}, got {actual_str}",
                        source="test_engine",
                        created_at=datetime.utcnow(),
                    )
                    self.db.add(failure)

                    log_entry = TestLog(
                        test_run_id=test_run.test_run_id,
                        level="ERROR",
                        message=f"[FAIL] {case.name}: expected {expected_str}, got {actual_str} ({t_duration} ms)",
                    )
                    self.db.add(log_entry)

            except Exception as e:
                t_duration = round((time.time() - t_start) * 1000, 2)
                t_result = TestResult(
                    test_run_id=test_run.test_run_id,
                    test_case_id=case.test_case_id,
                    test_name=case.name,
                    status="FAIL",
                    duration_ms=t_duration,
                    expected_value=_describe_expected(case),
                    actual_value="ERROR",
                    error_code="READ_FAILED",
                    error_message=str(e),
                    created_at=datetime.utcnow(),
                )
                self.db.add(t_result)
                self.db.commit()
                self.db.refresh(t_result)
                failed += 1

                # Record failure intelligence entry — source='test_engine' distinguishes
                # this from failures imported from the SCDC tracker or Azure DevOps bugs.
                failure = FailureRecord(
                    test_result_id=t_result.test_result_id,
                    meter_id=meter.meter_id,
                    firmware_id=meter.firmware_id,
                    test_case_id=case.test_case_id,
                    case_severity=case.priority,
                    error_code="READ_FAILED",
                    case_details=str(e),
                    source="test_engine",
                    created_at=datetime.utcnow(),
                )
                self.db.add(failure)

                log_entry = TestLog(
                    test_run_id=test_run.test_run_id,
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
