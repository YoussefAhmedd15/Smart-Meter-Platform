import os
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "Smart Meter Intelligence Platform"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-smart-meter-key-2026")
    APP_MODE: str = os.getenv("APP_MODE", "hardware")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./smart_meter_intelligence.db")
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
