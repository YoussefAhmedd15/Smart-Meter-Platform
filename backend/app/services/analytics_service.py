from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.schemas.schemas import KPISummaryResponse, TrendsResponse, DailyTrendPoint, FirmwareComparisonResponse, RegressionDetail

MT514_CRITICAL_CODES = {
    "-03", "E-SEQUEN", "-09", "droP-U-I", "-10", "rEUErSE", 
    "-12", "E-rELAY", "-23", "Drop-U-2", "-24", "Drop-U-3", 
    "Err-73", "Err-96", "RTC_FAULT", "MEMORY_FAULT"
}

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_quality_score(self, pass_rate: float, execution_rate: float, critical_failures: int) -> float:
        base_score = (pass_rate * 0.6) + (execution_rate * 0.2)
        penalty = min(critical_failures * 5.0, 20.0)
        return round(max(0.0, min(100.0, base_score + (20.0 - penalty))), 2)

    def get_overview_kpis(self) -> KPISummaryResponse:
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
        row = self.db.execute(query).mappings().first()

        total = row["total_executions"] or 0
        passed = row["passed_tests"] or 0
        failed = row["failed_tests"] or 0
        pending = row["pending_tests"] or 0
        pass_rate = (passed / total * 100.0) if total > 0 else 0.0

        crit_query = text("""
            SELECT COUNT(*) AS count
            FROM failures
            WHERE error_code = ANY(:codes);
        """)
        crit_count = self.db.execute(crit_query, {"codes": list(MT514_CRITICAL_CODES)}).scalar() or 0

        quality_score = self.calculate_quality_score(
            pass_rate=pass_rate,
            execution_rate=100.0 if total > 0 else 0.0,
            critical_failures=crit_count
        )

        return KPISummaryResponse(
            total_test_executions=total,
            total_meters_tested=row["total_meters"] or 0,
            overall_pass_rate=round(pass_rate, 2),
            quality_score=quality_score,
            passed_tests=passed,
            failed_tests=failed,
            pending_tests=pending,
            avg_duration_seconds=round(float(row["avg_duration_seconds"]), 2)
        )

    def get_failure_trends(self, limit_days: int = 7) -> TrendsResponse:
        trends_query = text("""
            SELECT 
                TO_CHAR(started_at, 'YYYY-MM-DD') AS test_date,
                COUNT(*) AS total_runs,
                COALESCE(SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END), 0) AS passed,
                COALESCE(SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END), 0) AS failed
            FROM test_executions
            WHERE started_at IS NOT NULL
            GROUP BY TO_CHAR(started_at, 'YYYY-MM-DD')
            ORDER BY test_date DESC
            LIMIT :limit;
        """)
        rows = self.db.execute(trends_query, {"limit": limit_days}).mappings().all()

        daily_trends = []
        for r in rows:
            t_total = r["total_runs"] or 0
            t_pass = r["passed"] or 0
            rate = (t_pass / t_total * 100.0) if t_total > 0 else 0.0
            daily_trends.append(DailyTrendPoint(
                date=r["test_date"],
                total_runs=t_total,
                passed=t_pass,
                failed=r["failed"] or 0,
                pass_rate=round(rate, 2)
            ))

        top_failing_query = text("""
            SELECT tc.name AS test_name, COUNT(*) AS failure_count
            FROM test_executions te
            JOIN test_cases tc ON te.test_case_id = tc.test_case_id
            WHERE te.status = 'FAIL'
            GROUP BY tc.name
            ORDER BY failure_count DESC
            LIMIT 5;
        """)
        top_tests = [dict(r) for r in self.db.execute(top_failing_query).mappings().all()]

        return TrendsResponse(trends=daily_trends, top_failing_tests=top_tests)

    def compare_firmwares(self, version_a: str, version_b: str) -> FirmwareComparisonResponse:
        rate_query = text("""
            SELECT 
                f.version,
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN te.status = 'PASS' THEN 1 ELSE 0 END), 0) AS passed
            FROM test_executions te
            JOIN firmwares f ON te.firmware_id = f.firmware_id
            WHERE f.version IN (:va, :vb)
            GROUP BY f.version;
        """)
        rows = self.db.execute(rate_query, {"va": version_a, "vb": version_b}).mappings().all()
        rates = {r["version"]: (r["passed"] / r["total"] * 100.0) if r["total"] > 0 else 0.0 for r in rows}
        
        pass_a = rates.get(version_a, 0.0)
        pass_b = rates.get(version_b, 0.0)

        regression_query = text("""
            WITH passed_a AS (
                SELECT DISTINCT te.test_case_id, tc.name
                FROM test_executions te
                JOIN test_cases tc ON te.test_case_id = tc.test_case_id
                JOIN firmwares f ON te.firmware_id = f.firmware_id
                WHERE f.version = :va AND te.status = 'PASS'
            ),
            failed_b AS (
                SELECT DISTINCT te.test_case_id
                FROM test_executions te
                JOIN firmwares f ON te.firmware_id = f.firmware_id
                WHERE f.version = :vb AND te.status = 'FAIL'
            )
            SELECT p.test_case_id, p.name
            FROM passed_a p
            JOIN failed_b f ON p.test_case_id = f.test_case_id;
        """)
        reg_rows = self.db.execute(regression_query, {"va": version_a, "vb": version_b}).mappings().all()
        
        regressed_tests = [
            RegressionDetail(
                test_case_id=r["test_case_id"],
                test_name=r["name"],
                status_firmware_a="PASS",
                status_firmware_b="FAIL"
            )
            for r in reg_rows
        ]

        handoff_payload = {
            "source": "regression_engine",
            "base_version": version_a,
            "target_version": version_b,
            "regression_count": len(regressed_tests),
            "affected_tests": [t.test_name for t in regressed_tests]
        }

        return FirmwareComparisonResponse(
            firmware_a=version_a,
            firmware_b=version_b,
            pass_rate_a=round(pass_a, 2),
            pass_rate_b=round(pass_b, 2),
            pass_rate_delta=round(pass_b - pass_a, 2),
            regressions_detected=len(regressed_tests),
            regressed_tests=regressed_tests,
            handoff_payload=handoff_payload
        )