import sys
import os
import random
from datetime import datetime, timedelta

# Path setup
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from backend.app.db.database import init_db, SessionLocal
from backend.app.db.models import (
    Meter, MeterObject, MeterReading, TestSuite, TestCase, TestRun,
    TestResult, TestLog, FailureRecord, FirmwareVersion, RegressionRun,
    KnowledgeItem, TestRecommendation, AlertRecord
)

def seed():
    print("Initializing Database tables...")
    init_db()
    db = SessionLocal()

    # Clear existing demo data
    db.query(MeterReading).delete()
    db.query(FailureRecord).delete()
    db.query(TestLog).delete()
    db.query(TestResult).delete()
    db.query(TestRun).delete()
    db.query(TestCase).delete()
    db.query(TestSuite).delete()
    db.query(MeterObject).delete()
    db.query(Meter).delete()
    db.query(FirmwareVersion).delete()
    db.query(KnowledgeItem).delete()
    db.query(RegressionRun).delete()
    db.query(TestRecommendation).delete()
    db.query(AlertRecord).delete()
    db.commit()

    print("Seeding 10 Iskraemeco Smart Meters...")
    models = ["AM550-TD1", "MT880-D2", "MT382-T1", "AM550-E2"]
    firmwares = ["v3.12.1", "v3.13.0", "v3.14.2", "v3.15.0-RC1"]
    
    created_meters = []
    for i in range(1, 11):
        m = Meter(
            serial_number=f"ISK-2026-984{100+i}",
            manufacturer="Iskraemeco",
            model=models[i % len(models)],
            firmware_version=firmwares[i % len(firmwares)],
            hardware_revision=f"HW-2.{i%3 + 1}",
            communication_interface="HDLC_WITH_MODE_E",
            status="ONLINE" if i != 4 else "ERROR",
        )
        db.add(m)
        created_meters.append(m)
    db.commit()
    for m in created_meters:
        db.refresh(m)

    print("Seeding Firmware Versions...")
    for fw in firmwares:
        fv = FirmwareVersion(
            meter_model="AM550-TD1",
            version_string=fw,
            release_date=datetime.utcnow() - timedelta(days=random.randint(10, 100)),
            status="RELEASED",
            changelog=f"Release {fw}: Improved HDLC frame timeout & Mode E optical handshake.",
        )
        db.add(fv)
    db.commit()

    print("Seeding Test Suites & Test Cases...")
    suite_comm = TestSuite(
        name="Communication & Optical Handshake Suite",
        category="Communication",
        description="Validates Mode E 300 baud request, identification, and HDLC SNRM/AARQ association.",
    )
    suite_elec = TestSuite(
        name="Electrical Telemetry & Registers Suite",
        category="Voltage & Power",
        description="Validates 3-phase RMS voltage, current, frequency, active power, and power factor.",
    )
    suite_lp = TestSuite(
        name="Load Profile 1 & RTC Generic Suite",
        category="LoadProfile",
        description="Validates RTC real-time clock accuracy and 15-minute load profile buffer integrity.",
    )
    db.add_all([suite_comm, suite_elec, suite_lp])
    db.commit()

    tc_list = [
        TestCase(suite_id=suite_comm.id, name="Mode E Optical Handshake 300 Baud", severity="CRITICAL", obis_target="0.0.96.1.1.255"),
        TestCase(suite_id=suite_comm.id, name="HDLC SNRM / UA Negotiation", severity="CRITICAL", obis_target="0.0.1.0.0.255"),
        TestCase(suite_id=suite_comm.id, name="AARQ Low-Level Authentication", severity="HIGH", obis_target="0.0.96.1.0.255"),
        
        TestCase(suite_id=suite_elec.id, name="Phase L1 RMS Voltage (230V)", severity="HIGH", obis_target="1.0.32.7.0.255"),
        TestCase(suite_id=suite_elec.id, name="Phase L2 RMS Voltage (230V)", severity="HIGH", obis_target="1.0.52.7.0.255"),
        TestCase(suite_id=suite_elec.id, name="Phase L3 RMS Voltage (230V)", severity="HIGH", obis_target="1.0.72.7.0.255"),
        TestCase(suite_id=suite_elec.id, name="Phase L1 RMS Current (4.3A)", severity="HIGH", obis_target="1.0.31.7.0.255"),
        TestCase(suite_id=suite_elec.id, name="Active Energy Import Cumulative", severity="CRITICAL", obis_target="1.0.1.8.0.255"),
        TestCase(suite_id=suite_elec.id, name="Grid Frequency Stability (50Hz)", severity="HIGH", obis_target="1.0.14.7.0.255"),

        TestCase(suite_id=suite_lp.id, name="Real-Time Clock Read", severity="MEDIUM", obis_target="0.0.1.0.0.255"),
        TestCase(suite_id=suite_lp.id, name="Load Profile 1 Buffer Reading", severity="HIGH", obis_target="1.0.99.1.0.255"),
    ]
    db.add_all(tc_list)
    db.commit()

    print("Seeding Test Runs & Results...")
    sample_error_types = ["TIMEOUT", "READ_FAILED", "SNRM_FAILED", "AARQ_FAILED", "DECODING_ERROR"]
    sample_errors = [
        "Communication timeout while waiting for UA response frame from optical head.",
        "Meter returned invalid checksum (FCS) on HDLC frame.",
        "AARQ authentication rejected by meter logical address 0.",
        "OBIS 1.0.99.1.0.255 buffer payload corrupted during block transfer.",
    ]

    for m in created_meters:
        for suite in [suite_comm, suite_elec, suite_lp]:
            for r_idx in range(5):  # 5 runs per meter/suite -> 150 test runs total!
                started = datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
                
                is_failed_run = (r_idx == 2 and m.id == 4)  # Simulate specific failed run for meter 4
                
                run = TestRun(
                    meter_id=m.id,
                    firmware_version=m.firmware_version,
                    suite_id=suite.id,
                    status="FAILED" if is_failed_run else "COMPLETED",
                    started_at=started,
                    finished_at=started + timedelta(seconds=random.uniform(3.0, 8.0)),
                    duration_seconds=round(random.uniform(3.0, 8.0), 2),
                    total_tests=len(suite.test_cases),
                    passed_tests=len(suite.test_cases) - (1 if is_failed_run else 0),
                    failed_tests=1 if is_failed_run else 0,
                    skipped_tests=0,
                )
                db.add(run)
                db.commit()
                db.refresh(run)

                for tc in suite.test_cases:
                    is_tc_fail = (is_failed_run and tc.id == suite.test_cases[0].id)
                    t_res = TestResult(
                        test_run_id=run.id,
                        test_case_id=tc.id,
                        test_name=tc.name,
                        status="FAIL" if is_tc_fail else "PASS",
                        duration_ms=round(random.uniform(150, 450), 1),
                        expected_value="Valid DLMS Response",
                        actual_value="ERROR" if is_tc_fail else f"{round(random.uniform(228, 232), 1)} V",
                        error_code=random.choice(sample_error_types) if is_tc_fail else None,
                        error_message=random.choice(sample_errors) if is_tc_fail else None,
                    )
                    db.add(t_res)
                    db.commit()
                    db.refresh(t_res)

                    if is_tc_fail:
                        fail_rec = FailureRecord(
                            test_result_id=t_res.id,
                            meter_id=m.id,
                            firmware_version=m.firmware_version,
                            test_case=tc.name,
                            error_type=t_res.error_code,
                            error_message=t_res.error_message,
                            root_cause="Optical probe alignment shifted causing serial parity frame noise during 300 baud Mode E handshake.",
                            solution="Re-align optical probe head, clean lens, and set serial parity to EVEN (7E1 mode).",
                            severity=tc.severity,
                        )
                        db.add(fail_rec)

    print("Seeding Knowledge Base Items...")
    k1 = KnowledgeItem(
        title="HDLC Frame FCS Checksum Error on Iskraemeco AM550",
        problem="Random FCS parity mismatch during high-speed block transfers on serial COM ports.",
        symptoms="DLMS reader throws ReadFailedError during 15-minute Load Profile buffer download.",
        affected_models="Iskraemeco AM550-TD1, MT880-D2",
        firmware="v3.12.1 - v3.13.0",
        root_cause="Serial driver parity mismatch when switching from 300 baud Mode E to 9600 baud HDLC.",
        solution="Ensure serial media stop bits is explicitly set to 1 and parity set to EVEN in GXSerial settings.",
        fixed_version="v3.14.2",
        severity="HIGH",
        tags="HDLC, FCS, Parity, Mode E, Serial",
    )
    k2 = KnowledgeItem(
        title="AARQ Association Failure with Low Authentication Password",
        problem="Meter rejects AARQ request with AuthenticationFailed error code.",
        symptoms="initializeConnection() raises AARQFailedError during handshake.",
        affected_models="Iskraemeco MT382-T1",
        firmware="v3.13.0",
        root_cause="Low authentication password hex string format misconfigured in DLMS client settings.",
        solution="Format password with 0x prefix if hex value is used, or supply plain ASCII string.",
        fixed_version="v3.14.2",
        severity="CRITICAL",
        tags="AARQ, Authentication, Password, Security",
    )
    db.add_all([k1, k2])
    db.commit()

    print("Seeding Regression Run Baseline Data...")
    reg = RegressionRun(
        firmware_a="v3.13.0",
        firmware_b="v3.14.2",
        total_tests=500,
        fixed_issues=17,
        new_failures=4,
        unchanged_failures=2,
        pass_rate_change=2.9,
        details={
            "fixed_cases": ["Mode E Optical Handshake", "Load Profile 1 Buffer Overflow", "FCS Checksum Validation"],
            "new_cases": ["Clock Drift under 60Hz Noise"],
            "unchanged_cases": ["Low Auth Timeout"],
        }
    )
    db.add(reg)
    db.commit()

    print("DEMO DATA SEEDED SUCCESSFULLY!")
    print(f"Meters: {db.query(Meter).count()}")
    print(f"Test Runs: {db.query(TestRun).count()}")
    print(f"Failures: {db.query(FailureRecord).count()}")
    print(f"Knowledge Items: {db.query(KnowledgeItem).count()}")

if __name__ == "__main__":
    seed()
