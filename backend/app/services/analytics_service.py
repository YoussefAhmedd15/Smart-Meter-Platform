from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..db.models import Meter, TestRun, TestResult, FailureRecord, Firmware

MT514_CRITICAL_CODES = {
    "-03", "E-SEQUEN", "-09", "droP-U-I", "-10", "rEUErSE", 
    "-12", "E-rELAY", "-23", "Drop-U-2", "-24", "Drop-U-3", 
    "Err-73", "Err-96", "RTC_FAULT", "MEMORY_FAULT"
}

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_overview_kpis(self) -> dict:
        total_meters = self.db.query(Meter).count()
        total_runs = self.db.query(TestRun).count()

        total_tests = self.db.query(func.sum(TestRun.total_tests)).scalar() or 0
        passed_tests = self.db.query(func.sum(TestRun.passed_tests)).scalar() or 0
        failed_tests = self.db.query(func.sum(TestRun.failed_tests)).scalar() or 0

        pass_rate = round((passed_tests / total_tests * 100), 1) if total_tests > 0 else 0.0
        avg_duration = self.db.query(func.avg(TestRun.duration_seconds)).scalar() or 0.0

        open_failures = self.db.query(FailureRecord).filter(FailureRecord.resolved_date.is_(None)).count()
        critical_failures = self.db.query(FailureRecord).filter(FailureRecord.case_severity == "CRITICAL").count()

        quality_score = round(min(100.0, max(0.0, pass_rate - (critical_failures * 1.5))), 1)

        return {
            "overall_quality_score": quality_score,
            "pass_rate_percentage": pass_rate,
            "total_meters_tested": total_meters,
            "total_test_runs": total_runs,
            "total_tests_executed": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "average_duration_seconds": round(avg_duration, 2),
            "open_failures": open_failures,
            "critical_failures": critical_failures,
            "firmware_stability": "STABLE" if pass_rate >= 95 else "DEGRADED",
        }

    def get_failures_by_firmware(self) -> List[dict]:
        # FailureRecord.firmware_version is a computed Python @property (reads
        # through the firmware_id FK to Firmware.version) — not a mapped
        # column, so it can't be used in a query/group_by. Join Firmware and
        # group on Firmware.version directly instead.
        results = (
            self.db.query(
                Firmware.version,
                func.count(FailureRecord.failure_id).label("failure_count")
            )
            .join(Firmware, FailureRecord.firmware_id == Firmware.firmware_id)
            .group_by(Firmware.version)
            .all()
        )
        return [{"firmware_version": r[0], "failure_count": r[1]} for r in results]

    def get_failures_by_model(self) -> List[dict]:
        # FailureRecord -> Meter is a direct FK (meter_id), and meter_model
        # lives on Meter itself — confirmed against models.py, not assumed.
        failure_counts = dict(
            self.db.query(Meter.meter_model, func.count(FailureRecord.failure_id))
            .join(FailureRecord, FailureRecord.meter_id == Meter.meter_id)
            .group_by(Meter.meter_model)
            .all()
        )

        # Same total/passed aggregation pattern get_overview_kpis uses,
        # joined through Meter and grouped by model instead of taken globally.
        run_totals = (
            self.db.query(
                Meter.meter_model,
                func.sum(TestRun.total_tests),
                func.sum(TestRun.passed_tests),
            )
            .join(TestRun, TestRun.meter_id == Meter.meter_id)
            .group_by(Meter.meter_model)
            .all()
        )
        run_totals_by_model = {r[0]: (r[1] or 0, r[2] or 0) for r in run_totals}

        # A model with test runs but zero failures still belongs in the
        # response, so union both sides rather than only iterating failures.
        all_models = set(failure_counts.keys()) | set(run_totals_by_model.keys())

        results = []
        for model in sorted(m for m in all_models if m is not None):
            total_tests, passed_tests = run_totals_by_model.get(model, (0, 0))
            pass_rate = round((passed_tests / total_tests * 100), 1) if total_tests > 0 else 0.0
            results.append({
                "model": model,
                "failures": failure_counts.get(model, 0),
                "pass_rate": pass_rate,
            })
        return results

    def get_test_trends(self) -> List[dict]:
        # Real calendar dates from TestRun.started_at (the actual timestamp
        # column — confirmed against models.py), grouped per day, limited to
        # the most recent 7 distinct days actually present in the data.
        day_col = func.date(TestRun.started_at)
        rows = (
            self.db.query(
                day_col.label("day"),
                func.sum(TestRun.passed_tests).label("passed"),
                func.sum(TestRun.failed_tests).label("failed"),
                func.avg(TestRun.duration_seconds).label("avg_duration"),
            )
            .group_by(day_col)
            .order_by(day_col.desc())
            .limit(7)
            .all()
        )

        trends = [
            {
                "date": r.day.isoformat() if hasattr(r.day, "isoformat") else str(r.day),
                "passed": int(r.passed or 0),
                "failed": int(r.failed or 0),
                "duration": round(float(r.avg_duration or 0.0), 2),
            }
            for r in rows
        ]
        trends.reverse()  # chronological order — oldest of the 7 days first
        return trends
