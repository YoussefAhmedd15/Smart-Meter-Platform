"""
Proves backend/tests/conftest.py's isolation actually blocks a real
credential from reaching the app during a test run — not just that the
code runs without error. This is the regression coverage for the incident
where test_azure_devops_service.py fired a real POST to dev.azure.com
because this machine's real .env leaked into a test process.

This file deliberately never sets TESTING or clears AZURE_DEVOPS_* itself
— if any assertion below passes, it can only be because
backend/tests/conftest.py already did it, which is the thing being proven.

Also deliberately never lets a real load_dotenv() call happen against the
real project .env, even to "demonstrate what the bug looked like" — that
would reintroduce exactly the risk this file exists to guard against.
Where a real-looking leaked value needs to be simulated, an obviously-fake
value in a throwaway temp file stands in for it.
"""
import importlib
import os
from unittest.mock import patch

import pytest

_OBVIOUSLY_FAKE_ORG = "definitely-fake-should-never-load-abc123"


def test_conftest_already_set_testing_flag():
    """conftest.py's whole job is to have already run by the time any test
    in this directory executes. This file sets nothing itself."""
    assert os.environ.get("TESTING") == "1"


def test_conftest_already_cleared_every_azure_env_var():
    for key in (
        "AZURE_DEVOPS_ORG",
        "AZURE_DEVOPS_PROJECT",
        "AZURE_DEVOPS_PAT",
        "AZURE_DEVOPS_API_VERSION",
        "AZURE_DEVOPS_TEST_PLAN_ID",
        "AZURE_DEVOPS_TEST_SUITE_ID",
        "AZURE_DEVOPS_DEFAULT_SUITE_IDS",
        "AZURE_DEVOPS_BUG_ASSIGNEE",
    ):
        assert os.environ.get(key) == "", f"{key} was not cleared by conftest.py"


def _fake_dotenv_stand_in(fake_env_path):
    """A load_dotenv() replacement that WOULD load an obviously-fake
    "leaked" value if it were ever actually invoked — the real function
    reference is captured by the caller before any patching happens, since
    both config.py and database.py do `from dotenv import load_dotenv`,
    which re-resolves against whatever `dotenv.load_dotenv` currently is
    every time that import line re-executes (e.g. on importlib.reload()).
    Patching a *copy* of the name bound onto one module (rather than the
    real `dotenv.load_dotenv` itself) is not reliable here: reload()
    re-runs that `from dotenv import load_dotenv` line, which silently
    rebinds the module's name back to the real function and orphans the
    mock — so the only patch target that actually holds through a reload
    is the real `dotenv.load_dotenv` attribute itself.
    """
    from dotenv import load_dotenv as real_load_dotenv

    def _stand_in(*args, **kwargs):
        return real_load_dotenv(dotenv_path=str(fake_env_path))

    return _stand_in


def test_config_py_never_calls_load_dotenv_under_testing(tmp_path):
    """
    The actual mechanism under test: config.py must not even attempt to
    read a .env file when TESTING=1.
    """
    fake_env = tmp_path / "fake.env"
    fake_env.write_text(f"AZURE_DEVOPS_ORG={_OBVIOUSLY_FAKE_ORG}\n")

    with patch("dotenv.load_dotenv", side_effect=_fake_dotenv_stand_in(fake_env)) as mock_load_dotenv:
        import backend.app.core.config as config_module
        importlib.reload(config_module)

        mock_load_dotenv.assert_not_called()
        assert os.environ.get("AZURE_DEVOPS_ORG") == ""
        assert config_module.settings.AZURE_DEVOPS_ORG == ""


def test_database_py_never_calls_load_dotenv_under_testing(tmp_path):
    """Same mechanism, same proof, for database.py's own load_dotenv() call."""
    fake_env = tmp_path / "fake.env"
    fake_env.write_text(f"AZURE_DEVOPS_ORG={_OBVIOUSLY_FAKE_ORG}\n")

    # Import once, unpatched, first — so the only call attempt inside the
    # patched window below is the explicit reload, not also this module's
    # very first import in this process.
    import backend.app.db.database as database_module

    with patch("dotenv.load_dotenv", side_effect=_fake_dotenv_stand_in(fake_env)) as mock_load_dotenv:
        importlib.reload(database_module)

        mock_load_dotenv.assert_not_called()
        assert os.environ.get("AZURE_DEVOPS_ORG") == ""


def test_azure_devops_service_reports_not_configured_with_the_exact_original_call():
    """
    The exact construction from the tests that fired the real HTTP call —
    now must genuinely short-circuit, with the real settings.AZURE_DEVOPS_*
    (which come from this machine's real .env, cleared to "" by conftest.py
    for this test run) never reaching the service. A real-request safety
    net (requests.request patched to explode) is also in place, in case
    is_configured is ever wrong again — this test must never depend on
    that net to pass, only to fail loudly and safely if something regresses.
    """
    from backend.app.services.azure_devops_service import (
        AzureDevOpsService, AzureDevOpsNotConfiguredError,
    )

    def _must_never_be_called(*args, **kwargs):
        raise AssertionError(
            f"requests.request was called with args={args} kwargs={kwargs} — "
            "a real outbound HTTP call was about to fire during a test run."
        )

    with patch("backend.app.services.azure_devops_service.requests.request", side_effect=_must_never_be_called):
        svc = AzureDevOpsService(org="", project="", pat="", plan_id="")
        assert svc.is_configured is False
        with pytest.raises(AzureDevOpsNotConfiguredError):
            svc.create_test_case("Some test")
