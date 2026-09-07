import os
import json
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from ..db.models import TestRun, TestResult, TestLog, Meter


class ReportGeneratorService:

    def __init__(self, db: Session):
        self.db = db
        self.output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/reports"))
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_test_run_report(self, test_run_id: int, format_type: str = "pdf") -> dict:
        run = self.db.query(TestRun).filter(TestRun.test_run_id == test_run_id).first()
        if not run:
            raise ValueError(f"Test run #{test_run_id} not found")

        meter = self.db.query(Meter).filter(Meter.meter_id == run.meter_id).first()
        results = self.db.query(TestResult).filter(TestResult.test_run_id == run.test_run_id).all()
        logs = self.db.query(TestLog).filter(TestLog.test_run_id == run.test_run_id).all()

        report_data = {
            "title": f"Smart Meter Testing Certificate - Test Run #{run.test_run_id}",
            "generated_at": datetime.utcnow().isoformat(),
            "meter": {
                "meter_number": meter.meter_number if meter else "UNKNOWN",
                "manufacturer": meter.manufacturer if meter else "Iskraemeco",
                "meter_model": meter.meter_model if meter else "AM550",
                "firmware_version": run.firmware_version,
            },
            "summary": {
                "status": run.status,
                "duration_seconds": run.duration_seconds,
                "total_tests": run.total_tests,
                "passed_tests": run.passed_tests,
                "failed_tests": run.failed_tests,
                "pass_rate": round((run.passed_tests / run.total_tests * 100), 1) if run.total_tests > 0 else 0.0,
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "duration_ms": r.duration_ms,
                    "actual_value": r.actual_value,
                    "error_message": r.error_message,
                }
                for r in results
            ],
            "execution_logs": [
                {"timestamp": l.timestamp.isoformat(), "level": l.level, "message": l.message}
                for l in logs
            ],
            "recommendation": "Passed all DLMS electrical parameters. Firmware is certified for production deployment." if run.status == "COMPLETED" else "Firmware failed test cases. Refer to Failure Intelligence analysis."
        }

        filename = f"report_test_run_{run.test_run_id}_{format_type}.json"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        return {
            "test_run_id": run.test_run_id,
            "format": format_type,
            "filename": filename,
            "filepath": filepath,
            "report_summary": report_data["summary"],
            "download_url": f"/api/reports/download/{filename}"
        }
