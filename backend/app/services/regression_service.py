from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..db.models import TestRun, TestResult, RegressionRun, Firmware


class RegressionService:

    def __init__(self, db: Session):
        self.db = db

    def _runs_for_firmware(self, version: str) -> List[TestRun]:
        firmware = self.db.query(Firmware).filter(Firmware.version == version).first()
        if not firmware:
            return []
        return self.db.query(TestRun).filter(TestRun.firmware_id == firmware.firmware_id).all()

    def compare_firmware_versions(self, firmware_a: str, firmware_b: str) -> dict:
        """
        Compares testing results between Firmware A and Firmware B using database records.
        """
        runs_a = self._runs_for_firmware(firmware_a)
        runs_b = self._runs_for_firmware(firmware_b)

        total_a = sum(r.total_tests for r in runs_a) or 1
        passed_a = sum(r.passed_tests for r in runs_a)
        failed_a = sum(r.failed_tests for r in runs_a)
        pass_rate_a = round((passed_a / total_a) * 100, 1)

        total_b = sum(r.total_tests for r in runs_b) or 1
        passed_b = sum(r.passed_tests for r in runs_b)
        failed_b = sum(r.failed_tests for r in runs_b)
        pass_rate_b = round((passed_b / total_b) * 100, 1)

        pass_rate_delta = round(pass_rate_b - pass_rate_a, 1)

        run_ids_a = [r.test_run_id for r in runs_a]
        run_ids_b = [r.test_run_id for r in runs_b]

        results_a = (
            self.db.query(TestResult).filter(TestResult.test_run_id.in_(run_ids_a)).all()
            if run_ids_a else []
        )
        results_b = (
            self.db.query(TestResult).filter(TestResult.test_run_id.in_(run_ids_b)).all()
            if run_ids_b else []
        )

        failed_cases_a = {r.test_name for r in results_a if r.status == "FAIL"}
        failed_cases_b = {r.test_name for r in results_b if r.status == "FAIL"}

        fixed_issues = list(failed_cases_a - failed_cases_b)
        new_failures = list(failed_cases_b - failed_cases_a)
        unchanged_failures = list(failed_cases_a & failed_cases_b)

        reg_run = RegressionRun(
            firmware_a=firmware_a,
            firmware_b=firmware_b,
            total_tests=total_b,
            fixed_issues=len(fixed_issues),
            new_failures=len(new_failures),
            unchanged_failures=len(unchanged_failures),
            pass_rate_change=pass_rate_delta,
            details={
                "fixed_cases": fixed_issues,
                "new_cases": new_failures,
                "unchanged_cases": unchanged_failures,
            }
        )
        self.db.add(reg_run)
        self.db.commit()
        self.db.refresh(reg_run)

        return {
            "id": reg_run.regression_run_id,
            "firmware_a": {
                "version": firmware_a,
                "pass_rate": pass_rate_a,
                "total_tests": total_a,
                "failures": failed_a,
            },
            "firmware_b": {
                "version": firmware_b,
                "pass_rate": pass_rate_b,
                "total_tests": total_b,
                "failures": failed_b,
            },
            "comparison": {
                "pass_rate_improvement": f"{'+' if pass_rate_delta >= 0 else ''}{pass_rate_delta}%",
                "fixed_issues_count": len(fixed_issues),
                "new_failures_count": len(new_failures),
                "unchanged_failures_count": len(unchanged_failures),
                "fixed_issues_list": fixed_issues,
                "new_failures_list": new_failures,
            }
        }
