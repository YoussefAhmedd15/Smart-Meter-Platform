from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.schemas.schemas import FirmwareComparisonResponse, RegressionDetail


class RegressionService:
    def __init__(self, db: Session):
        self.db = db

    def compare_firmwares(self, version_a: str, version_b: str) -> FirmwareComparisonResponse:
        """
        مقارنة نسختين فيرموير وحساب الـ Pass Rate واكتشاف الـ Regression
        """
        # 1. حساب نسب النجاح للنسختين
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

        # 2. كشف الاختبارات المنحدرة (كانت PASS في A وبقت FAIL في B)
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

        # 3. تجهيز تسليم البيانات لـ Member 5
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

    def compare_firmware_versions(self, firmware_a: str, firmware_b: str) -> FirmwareComparisonResponse:
        """
        TODO(merge-bridge): backend/app/main.py:510 still calls this old method
        name. This is a thin pass-through to compare_firmwares() so that
        endpoint keeps working, but it silently drops behavior the pre-merge
        HEAD version of this method used to have: persisting a RegressionRun
        row to the database (self.db.add(reg_run) / self.db.commit()) on every
        comparison. That history is no longer written anywhere.
        Whoever owns the /api/regression/compare endpoint in main.py should
        migrate it to call compare_firmwares() directly and adapt to the
        FirmwareComparisonResponse return type (a Pydantic model, not a dict)
        — once that's done, delete this wrapper.
        """
        return self.compare_firmwares(firmware_a, firmware_b)
