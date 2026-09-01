# Smart Meter Intelligence Platform - REST API Reference

Base Endpoint: `http://localhost:8000`

## Health & System
* `GET /health` - System health check, database status, and current mode (`demo` or `hardware`).

## Meters & Telemetry
* `GET /api/meters` - List all registered smart meters.
* `POST /api/meters` - Register a new smart meter.
* `GET /api/meters/{id}` - Fetch single meter details.
* `GET /api/meters/{id}/objects` - Retrieve COSEM object Association View.
* `GET /api/meters/{id}/readings` - Fetch recent telemetry readings.
* `POST /api/meters/{id}/connect` - Establish SNRM & AARQ DLMS connection.
* `POST /api/meters/{id}/disconnect` - Close media connection.

## Automated Testing Engine
* `GET /api/test-suites` - List available test suites (includes Azure sync state).
* `POST /api/test-suites` - Create a test suite.
* `PUT /api/test-suites/{id}` - Update a test suite.
* `DELETE /api/test-suites/{id}` - Delete a test suite.
* `POST /api/test-runs` - Execute a test run suite against a meter.
* `GET /api/test-runs` - List past test run history.
* `GET /api/test-runs/{id}` - Fetch detailed test run results and logs.

## Test Cases & Azure DevOps Test Plans Sync
* `POST /api/test-cases` - Create a test case. Saved locally first, then synced to
  Azure DevOps Test Plans (creates/reuses the Azure Test Suite, creates the Azure
  Test Case work item, and adds it to the suite). If Azure sync fails, the local
  test case is still kept with `azure_sync_status=FAILED` and `azure_sync_error` set.
* `GET /api/test-cases` - List test cases (optional `?suite_id=` filter).
* `GET /api/test-cases/{id}` - Fetch a single test case.
* `PUT /api/test-cases/{id}` - Update a test case locally and re-sync to Azure.
* `DELETE /api/test-cases/{id}` - Delete a test case (local only; does not delete
  the Azure work item).
* `POST /api/test-cases/{id}/sync-azure` - Retry a previously failed Azure sync.

`azure_sync_status` is one of `NOT_SYNCED`, `SYNCED`, `FAILED`, `NOT_CONFIGURED`
(the last meaning `AZURE_DEVOPS_ORG`/`PROJECT`/`PAT`/`TEST_PLAN_ID` are not all set).
See `backend/app/services/azure_devops_service.py` for the exact Azure REST calls used.

## Failure Intelligence & RAG
* `GET /api/failures` - List captured meter failure records.
* `GET /api/failures/{id}/similar` - Find similar historical failures using deterministic string similarity & confidence ratings.
* `POST /api/ai/chat` - Interact with grounded AI testing assistant.

## Analytics & Regression
* `GET /api/analytics/overview` - Fetch overall Quality Score, pass rate, and KPIs.
* `GET /api/analytics/firmware` - Failure rate breakdown by firmware version.
* `GET /api/analytics/models` - Failure rate breakdown by meter model.
* `GET /api/analytics/trends` - Daily testing pass/fail trends.
* `POST /api/regression/compare` - Compare Firmware A vs Firmware B side-by-side.
* `POST /api/recommendations/tests` - Generate recommended regression test suite based on changed code components.

## Reports & Knowledge Base
* `POST /api/reports/test-run/{id}?format_type=pdf` - Generate structured test run certificate report.
* `GET /api/knowledge` - List knowledge base entries.
* `POST /api/knowledge` - Create a new knowledge base solution item.
