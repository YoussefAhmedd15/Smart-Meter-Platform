"""
Unit tests for AzureDevOpsService. The real Azure REST API is never called —
`requests.request` is mocked throughout, per the project's testing rule that
this suite must not depend on a live Azure DevOps account.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)
GRANDPARENT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if GRANDPARENT not in sys.path:
    sys.path.insert(0, GRANDPARENT)

from backend.app.services.azure_devops_service import (
    AzureDevOpsService, AzureDevOpsError, AzureDevOpsNotConfiguredError, _steps_to_xml,
)


def _service():
    return AzureDevOpsService(
        org="fabrikam",
        project="SmartMeter",
        pat="fake-pat-token",
        api_version="7.1",
        plan_id="10",
    )


def _ok_response(json_body):
    resp = MagicMock()
    resp.ok = True
    resp.content = b"1"
    resp.json.return_value = json_body
    return resp


def _error_response(status_code=500, text="Internal Server Error"):
    resp = MagicMock()
    resp.ok = False
    resp.status_code = status_code
    resp.text = text
    return resp


class TestConfiguration(unittest.TestCase):
    def test_not_configured_without_all_fields(self):
        svc = AzureDevOpsService(org="", project="", pat="", plan_id="")
        self.assertFalse(svc.is_configured)

    def test_configured_with_all_fields(self):
        self.assertTrue(_service().is_configured)

    def test_create_test_case_raises_when_not_configured(self):
        svc = AzureDevOpsService(org="", project="", pat="", plan_id="")
        with self.assertRaises(AzureDevOpsNotConfiguredError):
            svc.create_test_case("Some test")


class TestCreateTestCase(unittest.TestCase):
    @patch("backend.app.services.azure_devops_service.requests.request")
    def test_creates_work_item_and_returns_id(self, mock_request):
        mock_request.return_value = _ok_response({"id": 4312, "fields": {}})
        svc = _service()

        azure_id = svc.create_test_case(
            name="Voltage L1 Range Check",
            description="Validates OBIS 1.0.32.7.0.255",
            test_steps=[{"action": "Read OBIS", "expected": "207V-253V"}],
        )

        self.assertEqual(azure_id, 4312)
        called_url = mock_request.call_args.args[1]
        self.assertIn("_apis/wit/workitems/$Test%20Case", called_url)
        self.assertIn("api-version=7.1", called_url)
        sent_headers = mock_request.call_args.kwargs["headers"]
        self.assertEqual(sent_headers["Content-Type"], "application/json-patch+json")
        self.assertTrue(sent_headers["Authorization"].startswith("Basic "))

    @patch("backend.app.services.azure_devops_service.requests.request")
    def test_raises_azure_devops_error_on_http_failure(self, mock_request):
        mock_request.return_value = _error_response(401, "Unauthorized")
        svc = _service()
        with self.assertRaises(AzureDevOpsError):
            svc.create_test_case("Some test")

    @patch("backend.app.services.azure_devops_service.requests.request")
    def test_raises_azure_devops_error_on_network_failure(self, mock_request):
        import requests
        mock_request.side_effect = requests.ConnectionError("DNS failure")
        svc = _service()
        with self.assertRaises(AzureDevOpsError):
            svc.create_test_case("Some test")


class TestSuiteOperations(unittest.TestCase):
    @patch("backend.app.services.azure_devops_service.requests.request")
    def test_get_or_create_finds_existing_suite_by_name(self, mock_request):
        mock_request.return_value = _ok_response({"value": [{"id": 77, "name": "Electrical Parameters Suite"}]})
        svc = _service()

        suite_id = svc.get_or_create_test_suite("Electrical Parameters Suite")

        self.assertEqual(suite_id, 77)
        # Only the list call was needed — no create call issued.
        self.assertEqual(mock_request.call_count, 1)

    @patch("backend.app.services.azure_devops_service.requests.request")
    def test_get_or_create_creates_when_absent(self, mock_request):
        list_resp = _ok_response({"value": []})
        plan_resp = _ok_response({"rootSuite": {"id": 6}})
        create_resp = _ok_response({"id": 88, "name": "New Suite"})
        mock_request.side_effect = [list_resp, plan_resp, create_resp]
        svc = _service()

        suite_id = svc.get_or_create_test_suite("New Suite")

        self.assertEqual(suite_id, 88)
        create_call = mock_request.call_args_list[-1]
        self.assertIn("/suites?api-version=7.1", create_call.args[1])
        self.assertEqual(create_call.kwargs["json"]["parentSuite"]["id"], 6)

    @patch("backend.app.services.azure_devops_service.requests.request")
    def test_add_test_case_to_suite_posts_correct_body(self, mock_request):
        mock_request.return_value = _ok_response([])
        svc = _service()

        svc.add_test_case_to_suite(azure_suite_id=77, azure_test_case_id=4312)

        called_url = mock_request.call_args.args[1]
        self.assertIn("/Plans/10/Suites/77/TestCase", called_url)
        self.assertEqual(mock_request.call_args.kwargs["json"], [{"workItem": {"id": 4312}}])


class TestStepsXmlConversion(unittest.TestCase):
    def test_escapes_special_characters(self):
        xml = _steps_to_xml([{"action": "Check <voltage> & \"range\"", "expected": "OK"}])
        self.assertIn("&lt;voltage&gt;", xml)
        self.assertIn("&amp;", xml)

    def test_default_step_when_empty(self):
        xml = _steps_to_xml([])
        self.assertIn('<steps id="0" last="1">', xml)


if __name__ == "__main__":
    unittest.main()
