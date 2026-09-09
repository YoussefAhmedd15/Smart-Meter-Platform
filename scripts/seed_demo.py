"""
MANUAL-ONLY DEMO DATA SEEDER (OPT-IN FOR LOCAL DEVELOPMENT)

This script populates synthetic demo/mock data (meters, test runs, synthetic failures)
for isolated local development or offline test environments.

IT MUST NEVER BE RUN AUTOMATICALLY ON STARTUP.
The shared Neon PostgreSQL database is the production source of truth.

Usage:
    python scripts/seed_demo.py --confirm
"""
import sys
import os
import random
from datetime import datetime, timedelta, date

# ---------------------------------------------------------------------------
# Path setup — make the project root importable so backend.app.* works.
# ---------------------------------------------------------------------------
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from backend.app.db.database import init_db, SessionLocal
from backend.app.db.models import (
    Firmware, Meter, MeterReading, MeterObject,
    TestSuite, TestCase, TestRun, TestResult, TestLog,
    FailureRecord, RegressionRun, KnowledgeItem, TestRecommendation,
    User,
)
from backend.app.core.security import hash_password


def seed():
    if "--confirm" not in sys.argv:
        print("====================================================================")
        print(" [MANUAL DEMO SEED SCRIPT]")
        print(" The shared PostgreSQL/Neon database is the source of truth.")
        print(" Automatic demo seeding has been removed from the normal startup flow.")
        print(" To explicitly seed synthetic demo data into an isolated database, run:")
        print("     python scripts/seed_demo.py --confirm")
        print("====================================================================")
        return

    db_url = os.getenv("DATABASE_URL", "")
    if "neon.tech" in db_url.lower() and "--force-neon" not in sys.argv:
        print("[SAFETY ABORT] DATABASE_URL points to the shared Neon PostgreSQL database.")
        print("Demo data seeding is prohibited on the shared database to protect real records.")
        print("If you need demo data, configure DATABASE_URL to an isolated local database.")
        return

    print("Initializing database tables...")
    try:
        init_db()
        db = SessionLocal()
        existing_meters = db.query(Meter).count()
        if existing_meters > 0 and "--overwrite" not in sys.argv:
            print(f"Database already contains data ({existing_meters} meters found). Skipping demo seed to protect existing data.")
            print("Pass --overwrite along with --confirm if you explicitly wish to reset.")
            db.close()
            return
    except Exception as exc:
        print(f"Warning: Database unreachable or not ready ({exc}). Skipping seed.")
        return

    # -----------------------------------------------------------------------
    # Clear existing demo data (only reached if database is empty or --overwrite)
    # -----------------------------------------------------------------------
    print("Clearing existing demo data...")
    for model in [
        MeterReading, MeterObject, FailureRecord,
        TestLog, TestResult, TestRun,
        TestCase, TestSuite,
        Meter, Firmware,
        KnowledgeItem, RegressionRun, TestRecommendation,
    ]:
        db.query(model).delete()
    db.commit()

    # -----------------------------------------------------------------------
    # Firmwares
    # -----------------------------------------------------------------------
    print("Seeding Firmware versions...")
    fw_versions = ["v3.12.1", "v3.13.0", "v3.14.2", "v3.15.0-RC1"]
    firmwares = []
    for i, ver in enumerate(fw_versions):
        fw = Firmware(
            version=ver,
            release_date=date.today() - timedelta(days=10 + i * 20),
            notes=f"Release {ver}: Improved HDLC frame timeout & Mode E optical handshake.",
            status="RELEASED" if ver != "v3.15.0-RC1" else "DRAFT",
        )
        db.add(fw)
        firmwares.append(fw)
    db.commit()
    for fw in firmwares:
        db.refresh(fw)

    # -----------------------------------------------------------------------
    # Meters
    # -----------------------------------------------------------------------
    print("Seeding 10 Iskraemeco Smart Meters...")
    meter_models = ["AM550-TD1", "MT880-D2", "MT382-T1", "AM550-E2"]
    districts = ["North", "South", "East", "West", "Central"]
    created_meters = []
    for i in range(1, 11):
        m = Meter(
            meter_number=f"ISK-2026-984{100 + i}",
            meter_type="Smart Meter",
            meter_model=meter_models[i % len(meter_models)],
            manufacturer="Iskraemeco",
            firmware_id=firmwares[i % len(firmwares)].firmware_id,
            hardware_revision=f"HW-2.{i % 3 + 1}",
            communication_interface="HDLC_WITH_MODE_E",
            district=districts[i % len(districts)],
            pos=f"POS-{i:03d}",
            status="ONLINE" if i != 4 else "ERROR",
        )
        db.add(m)
        created_meters.append(m)
    db.commit()
    for m in created_meters:
        db.refresh(m)

    # -----------------------------------------------------------------------
    # Test Suites & Test Cases
    # -----------------------------------------------------------------------
    print("Seeding Test Suites & Test Cases...")
    suite_comm = TestSuite(
        name="Communication & Optical Handshake Suite",
        category="Communication",
        description="Validates Mode E 300 baud request, identification, and HDLC SNRM/AARQ association.",
    )
    suite_elec = TestSuite(
        name="Electrical Telemetry & Registers Suite",
        category="Functional",
        description="Validates 3-phase RMS voltage, current, frequency, active power, and power factor.",
    )
    suite_lp = TestSuite(
        name="Load Profile 1 & RTC Generic Suite",
        category="LoadProfile",
        description="Validates RTC real-time clock accuracy and 15-minute load profile buffer integrity.",
    )
    db.add_all([suite_comm, suite_elec, suite_lp])
    db.commit()
    for s in [suite_comm, suite_elec, suite_lp]:
        db.refresh(s)

    tc_list = [
        # Communication suite
        TestCase(suite_id=suite_comm.suite_id, name="Mode E Optical Handshake 300 Baud",  priority="CRITICAL", obis_target="0.0.96.1.1.255"),
        TestCase(suite_id=suite_comm.suite_id, name="HDLC SNRM / UA Negotiation",         priority="CRITICAL", obis_target="0.0.1.0.0.255"),
        TestCase(suite_id=suite_comm.suite_id, name="AARQ Low-Level Authentication",       priority="HIGH",     obis_target="0.0.96.1.0.255"),
        # Electrical suite
        TestCase(suite_id=suite_elec.suite_id, name="Phase L1 RMS Voltage (230V)",         priority="HIGH",     obis_target="1.0.32.7.0.255"),
        TestCase(suite_id=suite_elec.suite_id, name="Phase L2 RMS Voltage (230V)",         priority="HIGH",     obis_target="1.0.52.7.0.255"),
        TestCase(suite_id=suite_elec.suite_id, name="Phase L3 RMS Voltage (230V)",         priority="HIGH",     obis_target="1.0.72.7.0.255"),
        TestCase(suite_id=suite_elec.suite_id, name="Phase L1 RMS Current (4.3A)",         priority="HIGH",     obis_target="1.0.31.7.0.255"),
        TestCase(suite_id=suite_elec.suite_id, name="Active Energy Import Cumulative",     priority="CRITICAL", obis_target="1.0.1.8.0.255"),
        TestCase(suite_id=suite_elec.suite_id, name="Grid Frequency Stability (50Hz)",     priority="HIGH",     obis_target="1.0.14.7.0.255"),
        # Load profile suite
        TestCase(suite_id=suite_lp.suite_id,   name="Real-Time Clock Read",                priority="MEDIUM",   obis_target="0.0.1.0.0.255"),
        TestCase(suite_id=suite_lp.suite_id,   name="Load Profile 1 Buffer Reading",       priority="HIGH",     obis_target="1.0.99.1.0.255"),
    ]
    db.add_all(tc_list)
    db.commit()
    for tc in tc_list:
        db.refresh(tc)

    # -----------------------------------------------------------------------
    # Test Runs & Results
    # -----------------------------------------------------------------------
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
            suite_cases = [tc for tc in tc_list if tc.suite_id == suite.suite_id]
            for r_idx in range(5):
                started = datetime.utcnow() - timedelta(
                    days=random.randint(0, 30), hours=random.randint(0, 23)
                )
                is_failed_run = (r_idx == 2 and m.meter_id == created_meters[3].meter_id)

                run = TestRun(
                    meter_id=m.meter_id,
                    firmware_id=m.firmware_id,
                    suite_id=suite.suite_id,
                    status="FAILED" if is_failed_run else "COMPLETED",
                    started_at=started,
                    finished_at=started + timedelta(seconds=random.uniform(3.0, 8.0)),
                    duration_seconds=round(random.uniform(3.0, 8.0), 2),
                    total_tests=len(suite_cases),
                    passed_tests=len(suite_cases) - (1 if is_failed_run else 0),
                    failed_tests=1 if is_failed_run else 0,
                    skipped_tests=0,
                )
                db.add(run)
                db.commit()
                db.refresh(run)

                for tc in suite_cases:
                    is_tc_fail = is_failed_run and tc.test_case_id == suite_cases[0].test_case_id
                    t_res = TestResult(
                        test_run_id=run.test_run_id,
                        test_case_id=tc.test_case_id,
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
                            test_result_id=t_res.test_result_id,
                            meter_id=m.meter_id,
                            firmware_id=m.firmware_id,
                            test_case_id=tc.test_case_id,
                            error_code=t_res.error_code,
                            case_details=t_res.error_message,
                            root_cause="Optical probe alignment shifted causing serial parity frame noise during 300 baud Mode E handshake.",
                            solution="Re-align optical probe head, clean lens, and set serial parity to EVEN (7E1 mode).",
                            case_severity=tc.priority,
                            source="test_engine",
                            status="OPEN",
                        )
                        db.add(fail_rec)
        db.commit()

    # -----------------------------------------------------------------------
    # Knowledge Base
    # -----------------------------------------------------------------------
    print("Seeding Knowledge Base Items...")
    db.add_all([
        KnowledgeItem(
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
        ),
        KnowledgeItem(
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
        ),
    ])
    db.commit()

    # -----------------------------------------------------------------------
    # Regression Run
    # -----------------------------------------------------------------------
    print("Seeding Regression Run baseline data...")
    db.add(RegressionRun(
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
        },
    ))
    # -----------------------------------------------------------------------
    # Users
    # -----------------------------------------------------------------------
    print("Seeding default Users...")
    admin_user = db.query(User).filter(User.email == "admin@iskraemeco.com").first()
    if not admin_user:
        db.add(User(
            email="admin@iskraemeco.com",
            password_hash=hash_password("admin123"),
            role="admin",
            is_active=True,
        ))
    tester_user = db.query(User).filter(User.email == "tester@iskraemeco.com").first()
    if not tester_user:
        db.add(User(
            email="tester@iskraemeco.com",
            password_hash=hash_password("tester123"),
            role="tester",
            is_active=True,
        ))
    db.commit()

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print("\nDEMO DATA SEEDED SUCCESSFULLY!")
    print(f"   Meters:          {db.query(Meter).count()}")
    print(f"   Test Runs:       {db.query(TestRun).count()}")
    print(f"   Test Results:    {db.query(TestResult).count()}")
    print(f"   Failures:        {db.query(FailureRecord).count()}")
    print(f"   Knowledge Items: {db.query(KnowledgeItem).count()}")
    db.close()


if __name__ == "__main__":
    seed()
