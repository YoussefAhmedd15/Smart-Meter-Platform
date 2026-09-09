"""
Test-session isolation for backend/tests/.

pytest imports every conftest.py in a directory (and its parents) before
collecting or importing any test module in that directory — this file's
top-level code is guaranteed to run first, for the whole test session,
exactly once. That's what makes it the right place to establish isolation,
rather than relying on each test file to defend itself individually, which
is exactly what did NOT happen for test_azure_devops_service.py: it fired a
real (harmless only by luck — the org name was still the unfilled
.env.example placeholder) POST to https://dev.azure.com/... during a
routine test run, because this machine's real .env got loaded via
config.py's load_dotenv() call and its (placeholder, but present)
AZURE_DEVOPS_* values reached AzureDevOpsService through the
`org or settings.AZURE_DEVOPS_ORG`-style fallback in its constructor.

Two layers, deliberately redundant:

1. Set TESTING=1 — the same flag backend/app/core/config.py's SECRET_KEY
   guard and backend/app/db/database.py's Postgres-only guard already use.
   As of this change, both of those modules also skip calling
   load_dotenv() entirely when this flag is set, so a real .env file on
   disk cannot leak into a test run no matter what it contains.

2. Belt-and-suspenders: explicitly force every AZURE_DEVOPS_* environment
   variable to "" regardless of (1). This is specifically because
   AzureDevOpsService.__init__'s `org or settings.AZURE_DEVOPS_ORG`
   fallback is exactly what turned an intentionally-unconfigured test
   service into a "configured" one and let it fire a real request — this
   makes sure that fallback never has anything to fall back to during a
   test run, no matter what else changes later in config.py, and no
   matter whether the value would have come from a real .env file or from
   something already exported in the calling shell's environment (a
   threat (1) alone doesn't cover).
"""
import os

os.environ["TESTING"] = "1"

for _key in (
    "AZURE_DEVOPS_ORG",
    "AZURE_DEVOPS_PROJECT",
    "AZURE_DEVOPS_PAT",
    "AZURE_DEVOPS_API_VERSION",
    "AZURE_DEVOPS_TEST_PLAN_ID",
    "AZURE_DEVOPS_TEST_SUITE_ID",
    "AZURE_DEVOPS_DEFAULT_SUITE_IDS",
    "AZURE_DEVOPS_BUG_ASSIGNEE",
):
    os.environ[_key] = ""
