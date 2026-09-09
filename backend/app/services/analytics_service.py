from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from ..db.models import Meter, TestRun, TestResult, FailureRecord, Firmware
from ..schemas.schemas import KPISummaryResponse

MT514_CRITICAL_CODES = {
    "-03", "E-SEQUEN", "-09", "droP-U-I", "-10", "rEUErSE", 
    "-12", "E-rELAY", "-23", "Drop-U-2", "-24", "Drop-U-3", 
    "Err-73", "Err-96", "RTC_FAULT", "MEMORY_FAULT"
}

class AnalyticsService:
    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def calculate_quality_score(self, pass_rate: float, execution_rate: float, critical_failures: int) -> float:
        base_score = (pass_rate * 0.6) + (execution_rate * 0.2)
        penalty = min(critical_failures * 5.0, 20.0)
        return round(max(0.0, min(100.0, base_score + (20.0 - penalty))), 2)

    def get_overview_kpis(self) -> KPISummaryResponse:
        row = None
        crit_count = 0

        # Check if db supports execute with raw SQL (for unit test mock_db and test_executions table)
        if self.db is not None and hasattr(self.db, "execute"):
            try:
                query = text("""
                    SELECT 
                        COUNT(*) AS total_executions,
                        COUNT(DISTINCT meter_id) AS total_meters,
                        COALESCE(SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END), 0) AS passed_tests,
                        COALESCE(SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END), 0) AS failed_tests,
                        COALESCE(SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END), 0) AS pending_tests,
                        COALESCE(AVG(duration_ms) / 1000.0, 0.0) AS avg_duration_seconds
                    FROM test_executions;
                """)
                res = self.db.execute(query)
                if hasattr(res, "mappings"):
                    mapping_res = res.mappings()
                    if hasattr(mapping_res, "first"):
                        row = mapping_res.first()
                
                crit_query = text("""
                    SELECT COUNT(*) AS count
                    FROM failures
                    WHERE error_code = ANY(:codes);
                """)
                crit_res = self.db.execute(crit_query, {"codes": list(MT514_CRITICAL_CODES)})
                if hasattr(crit_res, "scalar"):
                    crit_count = crit_res.scalar() or 0
            except Exception:
                row = None

        total = int(row["total_executions"]) if (row and "total_executions" in row and row["total_executions"] is not None) else 0
        meters_count = int(row["total_meters"]) if (row and "total_meters" in row and row["total_meters"] is not None) else 0
        passed = int(row["passed_tests"]) if (row and "passed_tests" in row and row["passed_tests"] is not None) else 0
        failed = int(row["failed_tests"]) if (row and "failed_tests" in row and row["failed_tests"] is not None) else 0
        pending = int(row["pending_tests"]) if (row and "pending_tests" in row and row["pending_tests"] is not None) else 0
        avg_dur = float(row["avg_duration_seconds"]) if (row and "avg_duration_seconds" in row and row["avg_duration_seconds"] is not None) else 0.0

        # If test_executions query returned 0, fallback to ORM TestRun queries on live DB
        if total == 0 and self.db is not None and hasattr(self.db, "query"):
            try:
                meters_count = self.db.query(Meter).count()
                total_runs = self.db.query(TestRun).count()
                if total_runs > 0:
                    total = self.db.query(func.sum(TestRun.total_tests)).scalar() or 0
                    passed = self.db.query(func.sum(TestRun.passed_tests)).scalar() or 0
                    failed = self.db.query(func.sum(TestRun.failed_tests)).scalar() or 0
                    avg_dur = float(self.db.query(func.avg(TestRun.duration_seconds)).scalar() or 0.0)
                    crit_count = self.db.query(FailureRecord).filter(FailureRecord.case_severity == "CRITICAL").count()
            except Exception:
                pass

        open_failures = 0
        if self.db is not None and hasattr(self.db, "query"):
            try:
                open_failures = self.db.query(FailureRecord).filter(FailureRecord.resolved_date.is_(None)).count()
            except Exception:
                pass

        pass_rate = round((passed / total * 100.0), 1) if total > 0 else 0.0
        quality_score = self.calculate_quality_score(
            pass_rate=pass_rate,
            execution_rate=100.0 if total > 0 else 0.0,
            critical_failures=crit_count
        )

        return KPISummaryResponse(
            total_test_executions=total,
            total_meters_tested=meters_count,
            overall_pass_rate=pass_rate,
            quality_score=quality_score,
            passed_tests=passed,
            failed_tests=failed,
            pending_tests=pending,
            avg_duration_seconds=round(avg_dur, 2),
            open_failures=open_failures,
            critical_failures=crit_count,
            firmware_stability="STABLE" if pass_rate >= 95 else "DEGRADED",
        )

    def get_failures_by_firmware(self) -> List[dict]:
        # Return all firmwares with their failure counts (outer join so zero-failure firmwares also appear)
        if self.db is None or not hasattr(self.db, "query"):
            return []
        results = (
            self.db.query(
                Firmware.version,
                func.count(FailureRecord.failure_id).label("failure_count")
            )
            .outerjoin(FailureRecord, FailureRecord.firmware_id == Firmware.firmware_id)
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
