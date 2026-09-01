"""
Integration tests for the Create Test Case -> Azure DevOps sync workflow
(backend.app.main._sync_test_case_to_azure and the CRUD it backs).

Uses a throwaway on-disk SQLite database (set via DATABASE_URL before the
`backend.app` package is imported) and a mocked AzureDevOpsService injected
the same way FastAPI would inject it via `get_azure_service` — no network
calls, no real Azure DevOps account required.
"""
import itertools
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

_next_azure_case_id = itertools.count(9001)

GRANDPARENT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if GRANDPARENT not in sys.path:
    sys.path.insert(0, GRANDPARENT)

_TMP_DB_FD, _TMP_DB_PATH = tempfile.mkstemp(suffix=".db", prefix="smart_meter_test_")
os.close(_TMP_DB_FD)
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB_PATH}"
os.environ["APP_MODE"] = "demo"

from backend.app.main import _sync_test_case_to_azure  # noqa: E402
from backend.app.db.database import SessionLocal, init_db  # noqa: E402
from backend.app.db.models import TestSuite, TestCase  # noqa: E402
from backend.app.services.azure_devops_service import AzureDevOpsService, AzureDevOpsError  # noqa: E402

init_db()


def make_mock_azure(configured=True, fail=False, plan_id="42"):
    mock = MagicMock(spec=AzureDevOpsService)
    mock.is_configured = configured
    mock.plan_id = plan_id
    if fail:
        mock.get_or_create_test_suite.side_effect = AzureDevOpsError("simulated outage")
        mock.create_test_case.side_effect = AzureDevOpsError("simulated outage")
        mock.update_test_case.side_effect = AzureDevOpsError("simulated outage")
        mock.add_test_case_to_suite.side_effect = AzureDevOpsError("simulated outage")
    else:
        # Unique per call so id-mapping assertions can't collide with rows
        # left behind by other test methods sharing the on-disk test database.
        azure_case_id = next(_next_azure_case_id)
        mock.get_or_create_test_suite.return_value = 501
        mock.create_test_case.return_value = azure_case_id
        mock.update_test_case.return_value = azure_case_id
        mock.add_test_case_to_suite.return_value = None
    return mock


class SyncWorkflowTestCase(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.suite = TestSuite(name=f"Suite-{id(self)}", category="Functional", description="test")
        self.db.add(self.suite)
        self.db.commit()
        self.db.refresh(self.suite)

        self.case = TestCase(
            suite_id=self.suite.id,
            name="Voltage L1 Range Check",
            description="Validates 207V-253V",
            obis_target="1.0.32.7.0.255",
        )
        self.db.add(self.case)
        self.db.commit()
        self.db.refresh(self.case)

    def tearDown(self):
        self.db.close()

    # 1. Local test case creation
    def test_local_test_case_created(self):
        self.assertIsNotNone(self.case.id)
        self.assertEqual(self.case.azure_sync_status, "NOT_SYNCED")

    # 2 & 3. Azure test case creation + successful synchronization
    def test_successful_sync_creates_suite_and_case_and_adds_to_suite(self):
        azure = make_mock_azure()

        _sync_test_case_to_azure(self.db, self.case, self.suite, azure)

        expected_azure_id = azure.create_test_case.return_value
        self.assertEqual(self.case.azure_sync_status, "SYNCED")
        self.assertEqual(self.case.azure_test_case_id, expected_azure_id)
        self.assertIsNone(self.case.azure_sync_error)
        self.assertIsNotNone(self.case.azure_last_synced_at)

        self.assertEqual(self.suite.azure_suite_id, 501)
        self.assertEqual(self.suite.azure_plan_id, 42)

        azure.add_test_case_to_suite.assert_called_once_with(501, expected_azure_id)

    # 4. Azure API failure
    def test_azure_failure_keeps_local_record_and_marks_failed(self):
        azure = make_mock_azure(fail=True)

        _sync_test_case_to_azure(self.db, self.case, self.suite, azure)

        # Local record must survive.
        reloaded = self.db.query(TestCase).filter(TestCase.id == self.case.id).first()
        self.assertIsNotNone(reloaded)
        self.assertEqual(reloaded.azure_sync_status, "FAILED")
        self.assertIn("simulated outage", reloaded.azure_sync_error)
        self.assertIsNone(reloaded.azure_test_case_id)

    # 5. Retry synchronization
    def test_retry_after_failure_succeeds(self):
        azure_failing = make_mock_azure(fail=True)
        _sync_test_case_to_azure(self.db, self.case, self.suite, azure_failing)
        self.assertEqual(self.case.azure_sync_status, "FAILED")

        azure_ok = make_mock_azure()
        _sync_test_case_to_azure(self.db, self.case, self.suite, azure_ok)

        self.assertEqual(self.case.azure_sync_status, "SYNCED")
        self.assertEqual(self.case.azure_test_case_id, azure_ok.create_test_case.return_value)

    # 6. Mapping local id <-> Azure id
    def test_local_to_azure_id_mapping_persisted(self):
        azure = make_mock_azure()
        _sync_test_case_to_azure(self.db, self.case, self.suite, azure)

        azure_id = azure.create_test_case.return_value
        reloaded = self.db.query(TestCase).filter(TestCase.azure_test_case_id == azure_id).first()
        self.assertEqual(reloaded.id, self.case.id)

    # 7. Adding the test case to the correct suite
    def test_add_test_case_uses_the_case_parent_suite(self):
        other_suite = TestSuite(name=f"Other-{id(self)}", category="Functional")
        self.db.add(other_suite)
        self.db.commit()
        self.db.refresh(other_suite)

        azure = make_mock_azure()
        _sync_test_case_to_azure(self.db, self.case, self.suite, azure)

        # Suite passed explicitly is the one used — never a different suite.
        azure.get_or_create_test_suite.assert_called_once_with(self.suite.name)
        self.assertNotEqual(self.suite.id, other_suite.id)

    # Not-configured short-circuit: no network calls, no crash
    def test_not_configured_marks_status_without_calling_azure(self):
        azure = make_mock_azure(configured=False)

        _sync_test_case_to_azure(self.db, self.case, self.suite, azure)

        self.assertEqual(self.case.azure_sync_status, "NOT_CONFIGURED")
        azure.create_test_case.assert_not_called()


if __name__ == "__main__":
    unittest.main()
