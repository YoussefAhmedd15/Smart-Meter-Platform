import os
from dotenv import load_dotenv
from pydantic import BaseModel

if os.getenv("TESTING", "0") != "1":
    # Skip loading a real .env during test runs. TESTING is set by
    # backend/tests/conftest.py before any test module is collected — a
    # real .env file on disk (which may contain real credentials, e.g.
    # Azure DevOps) must never be able to leak into a test process no
    # matter what it contains. When TESTING is unset, this is
    # byte-for-byte the same unconditional load_dotenv() call as before.
    load_dotenv()

# This exact string was the old hardcoded fallback below. It no longer
# authenticates anything (see the check after Settings is instantiated) —
# kept as a named constant purely so that check has something to compare
# against without repeating the literal.
_INSECURE_DEFAULT_SECRET_KEY = "super-secret-smart-meter-key-2026"


class Settings(BaseModel):
    PROJECT_NAME: str = "Smart Meter Intelligence Platform"
    API_V1_STR: str = "/api"
    # No secure default on purpose — the check below refuses to start the
    # app if this is unset or still the old hardcoded literal.
    SECRET_KEY: str = os.getenv("SECRET_KEY", _INSECURE_DEFAULT_SECRET_KEY)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h
    APP_MODE: str = os.getenv("APP_MODE", "hardware")
    # No default here on purpose — backend/app/db/database.py fails loudly at
    # import time if DATABASE_URL isn't set or isn't a postgresql:// URL. This
    # field exists for informational/API use; it isn't what actually connects.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    CORS_ORIGINS: list = ["*"]

    # Azure DevOps Test Plans integration
    AZURE_DEVOPS_ORG: str = os.getenv("AZURE_DEVOPS_ORG", "")
    AZURE_DEVOPS_PROJECT: str = os.getenv("AZURE_DEVOPS_PROJECT", "")
    AZURE_DEVOPS_PAT: str = os.getenv("AZURE_DEVOPS_PAT", "")
    AZURE_DEVOPS_API_VERSION: str = os.getenv("AZURE_DEVOPS_API_VERSION", "7.1")
    AZURE_DEVOPS_TEST_PLAN_ID: str = os.getenv("AZURE_DEVOPS_TEST_PLAN_ID", "")

    @property
    def azure_devops_configured(self) -> bool:
        return bool(
            self.AZURE_DEVOPS_ORG
            and self.AZURE_DEVOPS_PROJECT
            and self.AZURE_DEVOPS_PAT
            and self.AZURE_DEVOPS_TEST_PLAN_ID
        )


settings = Settings()

_is_testing = os.getenv("TESTING", "0") == "1"

if not settings.SECRET_KEY or settings.SECRET_KEY == _INSECURE_DEFAULT_SECRET_KEY:
    if _is_testing:
        import secrets
        os.environ["SECRET_KEY"] = secrets.token_urlsafe(48)
        settings = Settings()  # re-read with new key
    else:
        raise RuntimeError(
            "SECRET_KEY is not set (or is still the old hardcoded default). This "
            "signs auth tokens — the app refuses to start with it unset or with "
            "that default. Set a real random SECRET_KEY in your environment "
            "(see .env.example), e.g.: python -c \"import secrets; "
            "print(secrets.token_urlsafe(48))\""
        )
