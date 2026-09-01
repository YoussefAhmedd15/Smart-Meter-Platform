"""
Azure DevOps Test Plans integration service.

All communication with Azure DevOps REST API goes through this module — no
other part of the application should call Azure directly.

Verified endpoints (Azure DevOps REST API, api-version 7.1, as documented at
learn.microsoft.com/en-us/rest/api/azure/devops/ on 2026-09-01):

1. Create Test Case work item
   POST https://dev.azure.com/{org}/{project}/_apis/wit/workitems/$Test%20Case?api-version={v}
   Content-Type: application/json-patch+json
   Body: JSON Patch document setting System.Title, System.Description,
         Microsoft.VSTS.TCM.Steps (XML), Microsoft.VSTS.Common.Priority.
   Response: WorkItem object, `.id` is the Azure test case id.

2. Get Test Plan (to resolve the plan's root suite)
   GET https://dev.azure.com/{org}/{project}/_apis/testplan/plans/{planId}?api-version={v}
   Response: TestPlan object, `.rootSuite.id` is the root suite id.

3. List suites in a plan (used for get-or-create-by-name)
   GET https://dev.azure.com/{org}/{project}/_apis/testplan/Plans/{planId}/suites?api-version={v}
   Response: { "value": [TestSuite, ...] }

4. Create Test Suite (static, child of a parent suite)
   POST https://dev.azure.com/{org}/{project}/_apis/testplan/Plans/{planId}/suites?api-version={v}
   Body: {"suiteType": "staticTestSuite", "name": "...", "parentSuite": {"id": <parentSuiteId>}}
   Response: TestSuite object, `.id` is the Azure suite id.

5. Add Test Case to Suite
   POST https://dev.azure.com/{org}/{project}/_apis/testplan/Plans/{planId}/Suites/{suiteId}/TestCase?api-version={v}
   Body: [{"workItem": {"id": <testCaseId>}}]
   Response: TestCase[] (suite test case entries).

Auth: HTTP Basic, empty username, Personal Access Token as password.
"""
import base64
import logging
from typing import Any, Dict, List, Optional
from xml.sax.saxutils import escape

import requests

from ..core.config import settings

logger = logging.getLogger("azure_devops")

REQUEST_TIMEOUT_SECONDS = 15


class AzureDevOpsError(Exception):
    """Raised when an Azure DevOps REST call fails."""


class AzureDevOpsNotConfiguredError(AzureDevOpsError):
    """Raised when required Azure DevOps settings are missing."""


def _steps_to_xml(test_steps: Optional[List[Dict[str, str]]]) -> str:
    """Converts our JSON step list into the XML format Azure's Steps field expects."""
    steps = test_steps or []
    if not steps:
        steps = [{"action": "Execute the test case.", "expected": "Result matches expectation."}]
    body = "".join(
        f'<step id="{i + 1}" type="ActionStep">'
        f'<parameterizedString isformatted="true">{escape(str(s.get("action", "")))}</parameterizedString>'
        f'<parameterizedString isformatted="true">{escape(str(s.get("expected", "")))}</parameterizedString>'
        f"</step>"
        for i, s in enumerate(steps)
    )
    return f'<steps id="0" last="{len(steps)}">{body}</steps>'


class AzureDevOpsService:
    """Thin client over the Azure DevOps Test Plans + Work Item Tracking REST APIs."""

    def __init__(
        self,
        org: Optional[str] = None,
        project: Optional[str] = None,
        pat: Optional[str] = None,
        api_version: Optional[str] = None,
        plan_id: Optional[str] = None,
    ):
        self.org = org or settings.AZURE_DEVOPS_ORG
        self.project = project or settings.AZURE_DEVOPS_PROJECT
        self.pat = pat or settings.AZURE_DEVOPS_PAT
        self.api_version = api_version or settings.AZURE_DEVOPS_API_VERSION
        self.plan_id = plan_id or settings.AZURE_DEVOPS_TEST_PLAN_ID
        self.base_url = f"https://dev.azure.com/{self.org}/{self.project}/_apis"

    @property
    def is_configured(self) -> bool:
        return bool(self.org and self.project and self.pat and self.plan_id)

    def _auth_header(self) -> Dict[str, str]:
        token = base64.b64encode(f":{self.pat}".encode("utf-8")).decode("utf-8")
        return {"Authorization": f"Basic {token}"}

    def _require_configured(self):
        if not self.is_configured:
            raise AzureDevOpsNotConfiguredError(
                "Azure DevOps integration is not configured "
                "(AZURE_DEVOPS_ORG / AZURE_DEVOPS_PROJECT / AZURE_DEVOPS_PAT / AZURE_DEVOPS_TEST_PLAN_ID)."
            )

    def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        try:
            resp = requests.request(method, url, timeout=REQUEST_TIMEOUT_SECONDS, **kwargs)
        except requests.RequestException as exc:
            raise AzureDevOpsError(f"Network error calling Azure DevOps: {exc}") from exc

        if not resp.ok:
            raise AzureDevOpsError(
                f"Azure DevOps API {method} {url} failed with {resp.status_code}: {resp.text[:500]}"
            )
        if not resp.content:
            return {}
        return resp.json()

    # ------------------------------------------------------------------
    # Test Case (work item) operations
    # ------------------------------------------------------------------

    def create_test_case(
        self,
        name: str,
        description: str = "",
        test_steps: Optional[List[Dict[str, str]]] = None,
        priority: int = 2,
    ) -> int:
        """Creates a Test Case work item in Azure DevOps. Returns the Azure work item id."""
        self._require_configured()
        url = f"{self.base_url}/wit/workitems/$Test%20Case?api-version={self.api_version}"
        patch = [
            {"op": "add", "path": "/fields/System.Title", "value": name},
            {"op": "add", "path": "/fields/System.Description", "value": description or ""},
            {"op": "add", "path": "/fields/Microsoft.VSTS.TCM.Steps", "value": _steps_to_xml(test_steps)},
            {"op": "add", "path": "/fields/Microsoft.VSTS.Common.Priority", "value": priority},
        ]
        data = self._request(
            "POST",
            url,
            json=patch,
            headers={**self._auth_header(), "Content-Type": "application/json-patch+json"},
        )
        return data["id"]

    def update_test_case(
        self,
        azure_test_case_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        test_steps: Optional[List[Dict[str, str]]] = None,
    ) -> int:
        """Updates fields on an existing Azure Test Case work item. Returns the work item id."""
        self._require_configured()
        url = f"{self.base_url}/wit/workitems/{azure_test_case_id}?api-version={self.api_version}"
        patch = []
        if name is not None:
            patch.append({"op": "add", "path": "/fields/System.Title", "value": name})
        if description is not None:
            patch.append({"op": "add", "path": "/fields/System.Description", "value": description})
        if test_steps is not None:
            patch.append({"op": "add", "path": "/fields/Microsoft.VSTS.TCM.Steps", "value": _steps_to_xml(test_steps)})
        if not patch:
            return azure_test_case_id
        data = self._request(
            "PATCH",
            url,
            json=patch,
            headers={**self._auth_header(), "Content-Type": "application/json-patch+json"},
        )
        return data["id"]

    # ------------------------------------------------------------------
    # Test Suite operations
    # ------------------------------------------------------------------

    def _get_plan_root_suite_id(self) -> int:
        url = f"{self.base_url}/testplan/plans/{self.plan_id}?api-version={self.api_version}"
        data = self._request("GET", url, headers=self._auth_header())
        return data["rootSuite"]["id"]

    def _find_suite_by_name(self, name: str) -> Optional[int]:
        url = f"{self.base_url}/testplan/Plans/{self.plan_id}/suites?api-version={self.api_version}"
        try:
            data = self._request("GET", url, headers=self._auth_header())
        except AzureDevOpsError:
            return None
        for suite in data.get("value", []):
            if suite.get("name") == name:
                return suite.get("id")
        return None

    def create_test_suite(self, name: str, parent_suite_id: Optional[int] = None) -> int:
        """Creates a static Test Suite under the configured plan. Returns the Azure suite id."""
        self._require_configured()
        parent_id = parent_suite_id or self._get_plan_root_suite_id()
        url = f"{self.base_url}/testplan/Plans/{self.plan_id}/suites?api-version={self.api_version}"
        body = {
            "suiteType": "staticTestSuite",
            "name": name,
            "parentSuite": {"id": parent_id},
        }
        data = self._request("POST", url, json=body, headers=self._auth_header())
        return data["id"]

    def get_or_create_test_suite(self, name: str) -> int:
        """Returns the Azure suite id for `name` under the configured plan, creating it if absent."""
        self._require_configured()
        existing = self._find_suite_by_name(name)
        if existing is not None:
            return existing
        return self.create_test_suite(name)

    def add_test_case_to_suite(self, azure_suite_id: int, azure_test_case_id: int) -> None:
        """Adds an existing Azure Test Case work item to a Test Suite."""
        self._require_configured()
        url = (
            f"{self.base_url}/testplan/Plans/{self.plan_id}/Suites/{azure_suite_id}/TestCase"
            f"?api-version={self.api_version}"
        )
        body = [{"workItem": {"id": azure_test_case_id}}]
        self._request("POST", url, json=body, headers=self._auth_header())
