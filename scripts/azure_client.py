"""
azure_client.py
~~~~~~~~~~~~~~~
Encapsulates Azure DevOps *test execution result* reporting: creating a Test
Run linked to test points, publishing PASS/FAIL/skipped results per test
case, filing a Bug work item on failure (with screenshots attached), and
completing the run.

This is a separate concern from `backend/app/services/azure_devops_service.py`,
which handles *Test Case creation* (Phase 1: our platform -> Azure Test Plans)
via raw REST calls and is wired into the FastAPI API. This module is meant to
be imported from an external pytest `conftest.py` that actually executes
tests (e.g. a Selenium/UI suite) and needs to report their outcomes back to
Azure Test Plans — it is not currently called by the FastAPI app.

It uses the official `azure-devops` SDK (not raw REST), since the SDK already
provides typed models for test runs/results/attachments that would otherwise
be a lot of REST boilerplate to reimplement.

Environment variables (aligned with the names used elsewhere in this project —
see .env.example):
    AZURE_DEVOPS_ORG              org name (e.g. "fabrikam") or full org URL
    AZURE_DEVOPS_PROJECT          project name
    AZURE_DEVOPS_PAT              personal access token
    AZURE_DEVOPS_TEST_PLAN_ID     test plan id
    AZURE_DEVOPS_TEST_SUITE_ID    a single default suite id (optional)
    AZURE_DEVOPS_DEFAULT_SUITE_IDS  comma-separated suite ids searched when
                                     looking up test points (optional; empty
                                     by default — pass suite_ids explicitly to
                                     create_test_run() if this isn't set)
    AZURE_DEVOPS_BUG_ASSIGNEE     "Display Name <email>" used as the default
                                   assignee for auto-filed bugs (optional;
                                   bugs are left unassigned if unset)

Usage
-----
from azure_client import AzureDevOpsClient

client = AzureDevOpsClient()                    # reads env-vars automatically
run_id, mapping = client.create_test_run(...)
client.publish_result(...)
client.complete_run(run_id, suite_name)
"""

from __future__ import annotations

import base64
import os
import shutil
import traceback
from datetime import datetime
from inspect import signature
from typing import Any

from azure.devops.connection import Connection
from azure.devops.v7_1.test.models import RunCreateModel, TestCaseResult
from msrest.authentication import BasicAuthentication


# ---------------------------------------------------------------------------
# Helper (module-level, stateless)
# ---------------------------------------------------------------------------

def normalize_test_case_id(test_case_id: Any) -> tuple[int | None, str | None]:
    """Return (int_id, str_id) or (None, None) on bad input."""
    try:
        tc_int = int(test_case_id)
        return tc_int, str(tc_int)
    except (ValueError, TypeError):
        print(f"[WARN] Invalid test case ID format: {test_case_id}")
        return None, None


def _parse_suite_ids(raw: str) -> list[int]:
    """Parses a comma-separated env var into a list of int suite ids."""
    ids: list[int] = []
    for part in (raw or "").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            print(f"[WARN] Ignoring non-numeric suite id in AZURE_DEVOPS_DEFAULT_SUITE_IDS: {part!r}")
    return ids


def _normalize_org_url(org: str) -> str:
    """Accepts either a bare org name ("fabrikam") or a full URL and always
    returns a usable Azure DevOps base URL."""
    if not org:
        return org
    if org.startswith("http://") or org.startswith("https://"):
        return org.rstrip("/")
    return f"https://dev.azure.com/{org}"


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class AzureDevOpsClient:
    """Wraps all Azure DevOps Test-Plans and Work-Item operations."""

    def __init__(
        self,
        org: str | None = None,
        project: str | None = None,
        pat: str | None = None,
        plan_id: str | None = None,
        suite_id: str | None = None,
        default_suite_ids: list[int] | None = None,
        bug_assignee: str | None = None,
    ) -> None:
        self.org      = org      or os.getenv("AZURE_DEVOPS_ORG",             "")
        self.project  = project  or os.getenv("AZURE_DEVOPS_PROJECT",         "")
        self.pat      = pat      or os.getenv("AZURE_DEVOPS_PAT",             "")
        self.plan_id  = plan_id  or os.getenv("AZURE_DEVOPS_TEST_PLAN_ID",    "")
        self.suite_id = suite_id or os.getenv("AZURE_DEVOPS_TEST_SUITE_ID",   "")

        # Suite IDs searched when looking up test points, in create_test_run().
        # No suite ids are hardcoded here — configure via AZURE_DEVOPS_DEFAULT_SUITE_IDS
        # (comma-separated) or pass suite_ids= explicitly to create_test_run().
        self.default_suite_ids: list[int] = default_suite_ids or _parse_suite_ids(
            os.getenv("AZURE_DEVOPS_DEFAULT_SUITE_IDS", "")
        )

        # Default assignee for auto-filed bugs. Left unassigned if not set —
        # do not hardcode a specific person here.
        self.bug_assignee = bug_assignee or os.getenv("AZURE_DEVOPS_BUG_ASSIGNEE", "")

        self._print_env_check()

    # ------------------------------------------------------------------
    # Environment / diagnostics
    # ------------------------------------------------------------------

    def _print_env_check(self) -> None:
        print("[INFO] Checking Azure DevOps environment variables...")
        print(f"   AZURE_DEVOPS_ORG:               {self.org}")
        print(f"   AZURE_DEVOPS_PROJECT:            {self.project}")
        print(f"   AZURE_DEVOPS_TEST_PLAN_ID:       {self.plan_id}")
        print(f"   AZURE_DEVOPS_TEST_SUITE_ID:      {self.suite_id}")
        print(f"   AZURE_DEVOPS_DEFAULT_SUITE_IDS:  {self.default_suite_ids or '(none configured)'}")
        print(f"   AZURE_DEVOPS_BUG_ASSIGNEE:       {self.bug_assignee or '(unassigned)'}")

    def _require_credentials(self) -> None:
        if not self.org or not self.pat:
            raise ValueError("Missing AZURE_DEVOPS_ORG or AZURE_DEVOPS_PAT.")

    def diagnose_sdk(self) -> None:
        """Log SDK version / property-name compatibility info."""
        print("\n[DEBUG] Diagnosing Azure DevOps SDK compatibility...")
        try:
            params = list(signature(RunCreateModel.__init__).parameters.keys())
            print(f"   RunCreateModel parameters: {params}")
            if "point_ids" in params:
                print("   OK: SDK uses 'point_ids' (snake_case)")
            elif "pointIds" in params:
                print("   OK: SDK uses 'pointIds' (camelCase)")
            else:
                print("   [WARN] Could not detect point IDs parameter name")

            tc = self.get_test_client()
            methods = [m for m in dir(tc) if not m.startswith("_")]
            print(f"   Test client has {len(methods)} public methods")
            for name in ("create_test_result_attachment", "get_test_cases", "get_points"):
                if name in methods:
                    print(f"   OK: {name} available")
        except Exception as exc:
            print(f"   [WARN] SDK diagnostics failed: {exc}")
        print("[DEBUG] SDK diagnostics complete\n")

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _connection(self) -> Connection:
        self._require_credentials()
        return Connection(
            base_url=_normalize_org_url(self.org),
            creds=BasicAuthentication("", self.pat),
        )

    def get_test_client(self):
        """Return an Azure DevOps Test client."""
        client = self._connection().clients.get_test_client()
        print(f"[OK] Connected to Azure DevOps Org: {self.org}")
        return client

    def get_wit_client(self):
        """Return an Azure DevOps Work-Item Tracking client."""
        return self._connection().clients.get_work_item_tracking_client()

    # ------------------------------------------------------------------
    # Screenshot helpers
    # ------------------------------------------------------------------

    @staticmethod
    def copy_screenshot(screenshot_path: str, dest_dir: str) -> str:
        """Copy *screenshot_path* into *dest_dir* and return the new path."""
        try:
            os.makedirs(dest_dir, exist_ok=True)
            filename = os.path.basename(screenshot_path)
            dest = os.path.join(dest_dir, filename)
            shutil.copy2(screenshot_path, dest)
            print(f"[SCREENSHOT] Copied screenshot to Azure folder: {filename}")
            return dest
        except Exception as exc:
            print(f"[WARN] Failed to copy screenshot: {exc}")
            return screenshot_path

    @staticmethod
    def _extract_screenshot_path(screenshot_data: Any) -> str | None:
        if isinstance(screenshot_data, dict):
            path = screenshot_data.get("path") or screenshot_data.get("file_path")
            if not path:
                print(f"[WARN] Screenshot dict missing path key: {list(screenshot_data.keys())}")
            return path
        return str(screenshot_data)

    def upload_screenshot_to_result(
        self,
        test_client,
        run_id: int,
        result_id: int,
        screenshot_data: Any,
        test_name: str,
        azure_screenshots_dir: str,
    ) -> None:
        """Upload a single screenshot as an attachment to a test result."""
        try:
            path = self._extract_screenshot_path(screenshot_data)
            if not path or not os.path.exists(path):
                print(f"[WARN] Screenshot file not found: {path}")
                return

            azure_path = self.copy_screenshot(path, azure_screenshots_dir)
            with open(azure_path, "rb") as fh:
                encoded = base64.b64encode(fh.read()).decode("utf-8")

            attachment = {
                "stream":         encoded,
                "fileName":       os.path.basename(path),
                "comment":        f"Screenshot for {test_name}",
                "attachmentType": "GeneralAttachment",
            }

            try:
                test_client.create_test_result_attachment(
                    attachment, self.project, run_id, result_id
                )
                print(f"[SCREENSHOT] Uploaded screenshot: {os.path.basename(path)}")
            except TypeError as exc:
                print(f"[WARN] First upload attempt failed ({exc}), trying alternative format...")
                test_client.create_test_result_attachment(
                    encoded,
                    os.path.basename(path),
                    self.project,
                    run_id,
                    result_id,
                    attachment_type="GeneralAttachment",
                    comment=f"Screenshot for {test_name}",
                )
                print("[SCREENSHOT] Uploaded screenshot with alternative format")

        except Exception as exc:
            print(f"[ERROR] Failed to upload screenshot to Azure: {exc}")
            traceback.print_exc()

    def attach_screenshots_to_bug(
        self,
        bug_id: int,
        screenshots: list,
        azure_screenshots_dir: str,
    ) -> int:
        """Attach screenshots whose filename starts with 'failed' to a Bug work item."""
        if not screenshots:
            print(f"[INFO] No screenshots to attach to Bug #{bug_id}")
            return 0

        try:
            wit_client = self.get_wit_client()
            attached = skipped = 0

            for screenshot_data in screenshots:
                try:
                    path = self._extract_screenshot_path(screenshot_data)
                    if not path:
                        continue

                    filename = os.path.basename(path)
                    if not filename.lower().startswith("failed"):
                        print(f"[SKIP] Skipping non-failed screenshot: {filename}")
                        skipped += 1
                        continue

                    if not os.path.exists(path):
                        print(f"[WARN] Screenshot not found: {path}")
                        continue

                    with open(path, "rb") as fh:
                        attachment = wit_client.create_attachment(
                            upload_stream=fh,
                            project=self.project,
                            file_name=filename,
                            upload_type="Simple",
                        )

                    wit_client.update_work_item(
                        document=[{
                            "op":    "add",
                            "path":  "/relations/-",
                            "value": {
                                "rel": "AttachedFile",
                                "url": attachment.url,
                                "attributes": {
                                    "comment": "Failed test screenshot from automated execution"
                                },
                            },
                        }],
                        id=bug_id,
                        project=self.project,
                    )
                    print(f"[SCREENSHOT] Attached to Bug #{bug_id}: {filename}")
                    attached += 1

                except Exception as exc:
                    print(f"[WARN] Could not attach screenshot to Bug #{bug_id}: {exc}")

            print(
                f"[OK] Attached {attached} failed screenshot(s) to Bug #{bug_id} "
                f"(skipped {skipped} non-failed)"
            )
            return attached

        except Exception as exc:
            print(f"[ERROR] Failed attaching screenshots to Bug #{bug_id}: {exc}")
            traceback.print_exc()
            return 0

    # ------------------------------------------------------------------
    # Bug creation
    # ------------------------------------------------------------------

    def create_bug(
        self,
        test_result: dict,
        run_id: int,
        test_case_id: int,
        suite_name: str,
        test_point_info: dict | None = None,
    ) -> int | None:
        """Create a Bug work item for a failed test and return its ID."""
        try:
            wit_client = self.get_wit_client()

            bug_title = f"Automated Test Failure: {test_result['test_name']}"

            parts = [
                "<h2>Test Failure Details</h2>",
                f"<p><strong>Test Name:</strong> {test_result['test_name']}</p>",
                f"<p><strong>Suite:</strong> {suite_name}</p>",
                f"<p><strong>Execution Time:</strong> {test_result.get('execution_time', 'N/A')}</p>",
                f"<p><strong>Duration:</strong> {test_result.get('duration', 0):.2f} seconds</p>",
                "<h3>Error Message</h3>",
                f"<pre>{test_result.get('error_message', 'No error message available')}</pre>",
            ]

            steps = test_result.get("steps", [])
            if steps:
                parts += ["<h3>Test Steps</h3>", "<ol>"]
                parts += [f"<li>{s}</li>" for s in steps]
                parts.append("</ol>")

            description_html = "\n".join(parts)

            document = [
                {"op": "add", "path": "/fields/System.Title",
                 "value": bug_title},
                {"op": "add", "path": "/fields/System.Description",
                 "value": description_html},
                {"op": "add", "path": "/fields/Microsoft.VSTS.TCM.ReproSteps",
                 "value": description_html},
                {"op": "add", "path": "/fields/System.Tags",
                 "value": "Automated Test Failure; pytest; AutoCreated"},
                {"op": "add", "path": "/fields/Microsoft.VSTS.Common.Priority",
                 "value": 2},
                {"op": "add", "path": "/fields/Microsoft.VSTS.Common.Severity",
                 "value": "3 - Medium"},
            ]
            if self.bug_assignee:
                document.append({
                    "op": "add", "path": "/fields/System.AssignedTo",
                    "value": self.bug_assignee,
                })

            print(f"[BUG] Creating bug for failed test: {test_result['test_name']}")
            bug = wit_client.create_work_item(
                document=document,
                project=self.project,
                type="Bug",
            )
            print(f"[OK] Created Bug #{bug.id}: {bug_title}")
            print(f"[LINK] {_normalize_org_url(self.org)}/{self.project}/_workitems/edit/{bug.id}")
            return bug.id

        except Exception as exc:
            print(f"[ERROR] Failed to create bug for '{test_result['test_name']}': {exc}")
            traceback.print_exc()
            return None

    def link_bug_to_test_case(self, bug_id: int, test_case_id: int) -> None:
        """Create a 'TestedBy' relationship between Bug and Test Case."""
        try:
            wit_client = self.get_wit_client()
            test_case = wit_client.get_work_item(test_case_id, project=self.project)

            wit_client.update_work_item(
                document=[{
                    "op":    "add",
                    "path":  "/relations/-",
                    "value": {
                        "rel": "Microsoft.VSTS.Common.TestedBy-Reverse",
                        "url": test_case.url,
                        "attributes": {"comment": "Linked from automated test failure"},
                    },
                }],
                id=bug_id,
                project=self.project,
            )
            print(f"[LINK] Linked Bug #{bug_id} -> Test Case #{test_case_id}")

        except Exception as exc:
            print(f"[WARN] Could not link Bug #{bug_id} to TC #{test_case_id}: {exc}")

    # ------------------------------------------------------------------
    # Test-run creation
    # ------------------------------------------------------------------

    def _run_name(self, suite_name: str) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"Automated Test Run - {suite_name} - {ts}"

    def create_test_run(
        self,
        suite_name: str,
        test_case_ids: list,
        suite_ids: list[int] | None = None,
    ) -> tuple[int, dict]:
        """
        Create a **planned** Azure test run linked to *test_case_ids*.

        Returns
        -------
        (run_id, test_point_mapping)
            test_point_mapping: {str(tc_id): {"point_id": int, "revision": int, "suite_id": int}}
        """
        test_client = self.get_test_client()
        suite_ids   = suite_ids or self.default_suite_ids

        if not isinstance(suite_ids, list):
            suite_ids = [suite_ids]

        if not suite_ids:
            print(
                "[WARN] No suite_ids provided and AZURE_DEVOPS_DEFAULT_SUITE_IDS is not "
                "set -> falling back to unplanned run"
            )
            return self.create_unplanned_run(suite_name), {}

        # Normalise requested test-case IDs
        normalized: dict[str, int] = {}
        for tc_id in test_case_ids:
            tc_int, tc_str = normalize_test_case_id(tc_id)
            if tc_int is not None:
                normalized[tc_str] = tc_int

        if not normalized:
            print("[WARN] No valid test case IDs -> falling back to unplanned run")
            return self.create_unplanned_run(suite_name), {}

        print(
            f"[SEARCH] Searching {len(normalized)} test case(s) across "
            f"{len(suite_ids)} suite(s)"
        )
        print(f"   Test Case IDs : {list(normalized.keys())}")
        print(f"   Suite IDs     : {suite_ids}")

        test_points:       list[int] = []
        test_point_mapping: dict     = {}
        found: set[str]              = set()

        for suite_id in suite_ids:
            print(f"\n[SEARCH] Searching Suite ID: {suite_id}")
            for tc_str in normalized:
                if tc_str in found:
                    continue
                try:
                    print(f"   -> TC {tc_str} in suite {suite_id}")
                    points = test_client.get_points(
                        self.project, self.plan_id, suite_id,
                        test_case_id=tc_str,
                    )
                    if not points:
                        print(f"     [WARN] No points found")
                        continue

                    print(f"     OK: {len(points)} point(s) found")
                    point = points[0]

                    # Extract point ID
                    if hasattr(point, "id"):
                        point_id = int(point.id)
                    elif hasattr(point, "point_id"):
                        point_id = int(point.point_id)
                    else:
                        point_id = int(point)

                    # Extract revision
                    revision = 1
                    if hasattr(point, "test_case") and hasattr(point.test_case, "revision"):
                        revision = point.test_case.revision or 1
                    elif hasattr(point, "revision"):
                        revision = point.revision or 1

                    test_points.append(point_id)
                    test_point_mapping[tc_str] = {
                        "point_id": point_id,
                        "revision": revision,
                        "suite_id": suite_id,
                    }
                    found.add(tc_str)
                    print(f"       point_id={point_id}, revision={revision}")

                    if len(points) > 1:
                        print(f"       [INFO] {len(points)} points available; using first only")

                except Exception as exc:
                    print(f"     [WARN] Error for TC {tc_str} in suite {suite_id}: {exc}")

        missing = set(normalized.keys()) - found
        print(f"\n[INFO] Collected {len(test_points)} point(s). Missing: {missing or 'none'}")

        if not test_points:
            print("[WARN] No points found -> creating unplanned run")
            return self.create_unplanned_run(suite_name), {}

        model = RunCreateModel(
            name=self._run_name(suite_name),
            plan={"id": str(self.plan_id)},
            point_ids=[int(p) for p in test_points],
            automated=True,
            state="InProgress",
            comment=(
                f"Automated execution for {suite_name} - "
                f"{len(normalized)} test case(s) across {len(suite_ids)} suite(s)"
            ),
        )

        try:
            run = test_client.create_test_run(model, self.project)
            if not run:
                print("[WARN] run creation returned None -> unplanned fallback")
                return self.create_unplanned_run(suite_name), {}

            print(f"[OK] Created PLANNED run: {run.id}")
            self._verify_run(test_client, run.id)
            return run.id, test_point_mapping

        except Exception as exc:
            print(f"[ERROR] Planned run creation failed: {exc}")
            traceback.print_exc()
            return self.create_unplanned_run(suite_name), {}

    def create_unplanned_run(self, suite_name: str) -> int:
        """Create an unplanned (fallback) Azure test run."""
        test_client = self.get_test_client()
        model = RunCreateModel(
            name=self._run_name(suite_name),
            automated=True,
            state="InProgress",
            comment=f"Automated execution for {suite_name} (Unplanned)",
        )
        run = test_client.create_test_run(model, self.project)
        print(f"[INFO] Created UNPLANNED run: {run.id}")
        return run.id

    def complete_run(self, run_id: int, suite_name: str = "") -> None:
        """Mark an Azure test run as Completed."""
        try:
            test_client = self.get_test_client()
            test_client.update_test_run({"state": "Completed"}, self.project, run_id)
            print(f"[OK] Completed run {run_id} (suite: {suite_name!r})")
            print(
                f"[LINK] {_normalize_org_url(self.org)}/{self.project}/_testManagement/runs"
                f"?runId={run_id}&_a=runCharts"
            )
        except Exception as exc:
            print(f"[WARN] Failed to complete run {run_id}: {exc}")

    # ------------------------------------------------------------------
    # Publish results
    # ------------------------------------------------------------------

    def publish_result(
        self,
        test_result: dict,
        run_id: int,
        test_case_id: Any,
        azure_screenshots_dir: str,
        test_point_info: dict | None = None,
        suite_name: str | None = None,
        create_bug: bool = False,
    ) -> None:
        """
        Publish a single test result to Azure Test Plans.

        Optionally creates a Bug work item for failures when *create_bug* is True.
        """
        test_client = self.get_test_client()
        tc_int, tc_str = normalize_test_case_id(test_case_id)
        if tc_int is None:
            print(f"[ERROR] Invalid test case ID: {test_case_id}")
            return

        outcome = "Passed" if test_result["status"].upper() == "PASSED" else "Failed"
        bug_id:  int | None = None

        # -- Step 1: create bug if needed -----------------------------
        if outcome == "Failed" and create_bug:
            print("[BUG] Test failed -> creating bug work item...")
            try:
                bug_id = self.create_bug(
                    test_result=test_result,
                    run_id=run_id,
                    test_case_id=tc_int,
                    suite_name=suite_name or test_result.get("suite", "Unknown Suite"),
                    test_point_info=test_point_info,
                )
                if bug_id:
                    self.attach_screenshots_to_bug(
                        bug_id,
                        test_result.get("screenshots", []),
                        azure_screenshots_dir,
                    )
                    self.link_bug_to_test_case(bug_id, tc_int)
            except Exception as exc:
                print(f"[WARN] Bug creation failed, continuing: {exc}")
                bug_id = None
        elif outcome == "Failed":
            print("[INFO] Test failed -> bug creation disabled (use --bug flag)")

        # -- Step 2: update/add test result ----------------------------
        try:
            print(f"[SEARCH] Fetching existing results from run {run_id}...")
            existing = test_client.get_test_results(self.project, run_id)
            print(f"   Found {len(existing)} result(s)")

            result_id: int | None = None
            for ex in existing:
                ex_tc = str(getattr(ex.test_case, "id", "")) if hasattr(ex, "test_case") else ""
                if ex_tc == tc_str:
                    result_id = ex.id
                    print(f"[INFO] Will update result {result_id} for TC {tc_str}")
                    break

            base_payload = {
                "testCase":              {"id": tc_str},
                "testCaseTitle":         test_result["test_name"],
                "testCaseReferenceId":   tc_int,
                "automatedTestName":     test_result["test_name"],
                "outcome":               outcome,
                "state":                 "Completed",
                "comment":               (test_result.get("error_message") or "")[:1000],
                "durationInMs":          int(test_result.get("duration", 0) * 1000),
                "errorMessage":          (test_result.get("error_message") or "")[:1000],
            }

            if test_point_info and isinstance(test_point_info, dict):
                point_id = test_point_info.get("point_id")
                revision = test_point_info.get("revision", 1)
                if point_id:
                    base_payload["testPoint"]        = {"id": str(point_id)}
                    base_payload["testCaseRevision"] = revision
                    print(f"   Including point {point_id}, revision {revision}")

            if bug_id:
                base_payload["associatedBugs"] = [{"id": str(bug_id)}]
                print(f"[LINK] Linking Bug #{bug_id} to result")

            if result_id:
                test_client.update_test_results(
                    [{**base_payload, "id": result_id}],
                    self.project,
                    run_id,
                )
                print(f"[OK] UPDATED result {result_id} for '{test_result['test_name']}'")
            else:
                tc_result = TestCaseResult(
                    test_case={"id": tc_str},
                    test_case_title=test_result["test_name"],
                    test_case_reference_id=tc_int,
                    automated_test_name=test_result["test_name"],
                    outcome=outcome,
                    state="Completed",
                    comment=(test_result.get("error_message") or "")[:1000],
                    duration_in_ms=int(test_result.get("duration", 0) * 1000),
                    error_message=(test_result.get("error_message") or "")[:1000],
                )
                if test_point_info and isinstance(test_point_info, dict):
                    point_id = test_point_info.get("point_id")
                    revision = test_point_info.get("revision", 1)
                    if point_id:
                        tc_result.test_point       = {"id": str(point_id)}
                        tc_result.test_case_revision = revision
                if bug_id:
                    tc_result.associated_bugs = [{"id": str(bug_id)}]

                added     = test_client.add_test_results_to_test_run(
                    [tc_result], self.project, run_id
                )
                result_id = added[0].id if added else None
                print(f"[OK] ADDED result {result_id} for '{test_result['test_name']}'")

            # -- Step 3: upload screenshots to result -------------------
            if result_id:
                screenshots = test_result.get("screenshots", [])
                print(f"[SCREENSHOT] {len(screenshots)} screenshot(s) to upload to result")
                for idx, ss in enumerate(screenshots, 1):
                    print(f"  -> Uploading {idx}/{len(screenshots)}")
                    self.upload_screenshot_to_result(
                        test_client, run_id, result_id,
                        ss, test_result["test_name"], azure_screenshots_dir,
                    )

        except Exception as exc:
            print(f"[ERROR] Failed to publish result to Azure: {exc}")
            traceback.print_exc()

    def publish_skipped_result(
        self,
        test_result: dict,
        run_id: int,
        test_case_id: Any,
        azure_screenshots_dir: str,
        test_point_info: dict | None = None,
    ) -> None:
        """Publish a skipped test result to Azure as *NotApplicable*."""
        test_client = self.get_test_client()
        tc_int, tc_str = normalize_test_case_id(test_case_id)
        if tc_int is None:
            print(f"[ERROR] Invalid test case ID: {test_case_id}")
            return

        try:
            existing   = test_client.get_test_results(self.project, run_id)
            result_id: int | None = None
            for ex in existing:
                ex_tc = str(getattr(ex.test_case, "id", "")) if hasattr(ex, "test_case") else ""
                if ex_tc == tc_str:
                    result_id = ex.id
                    break

            base_payload = {
                "testCase":            {"id": tc_str},
                "testCaseTitle":       test_result["test_name"],
                "testCaseReferenceId": tc_int,
                "automatedTestName":   test_result["test_name"],
                "outcome":             "NotApplicable",
                "state":               "Completed",
                "comment":             (test_result.get("error_message") or "Test was skipped")[:1000],
                "durationInMs":        0,
                "errorMessage":        (test_result.get("error_message") or "")[:1000],
            }

            if test_point_info and isinstance(test_point_info, dict):
                point_id = test_point_info.get("point_id")
                revision = test_point_info.get("revision", 1)
                if point_id:
                    base_payload["testPoint"]        = {"id": str(point_id)}
                    base_payload["testCaseRevision"] = revision

            if result_id:
                test_client.update_test_results(
                    [{**base_payload, "id": result_id}],
                    self.project,
                    run_id,
                )
                print(f"[OK] Updated skipped result {result_id} for '{test_result['test_name']}'")
            else:
                tc_result = TestCaseResult(
                    test_case={"id": tc_str},
                    test_case_title=test_result["test_name"],
                    test_case_reference_id=tc_int,
                    automated_test_name=test_result["test_name"],
                    outcome="NotApplicable",
                    state="Completed",
                    comment=(test_result.get("error_message") or "Test was skipped")[:1000],
                    duration_in_ms=0,
                    error_message=(test_result.get("error_message") or "")[:1000],
                )
                if test_point_info and isinstance(test_point_info, dict):
                    point_id = test_point_info.get("point_id")
                    revision = test_point_info.get("revision", 1)
                    if point_id:
                        tc_result.test_point        = {"id": str(point_id)}
                        tc_result.test_case_revision = revision

                test_client.add_test_results_to_test_run([tc_result], self.project, run_id)
                print(f"[OK] Added skipped result for '{test_result['test_name']}'")

        except Exception as exc:
            print(f"[ERROR] Failed to publish skipped result: {exc}")
            traceback.print_exc()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _verify_run(self, test_client, run_id: int) -> None:
        """Print a quick summary of results inside a freshly created run."""
        try:
            results = test_client.get_test_results(self.project, run_id)
            print(f"\n[INFO] Run {run_id} contains {len(results)} result(s):")
            for idx, r in enumerate(results, 1):
                tc = getattr(r.test_case, "id", "?") if hasattr(r, "test_case") else "?"
                print(f"   {idx}. TC={tc}, outcome={getattr(r, 'outcome', '?')}")
        except Exception as exc:
            print(f"[WARN] Could not verify run contents: {exc}")
