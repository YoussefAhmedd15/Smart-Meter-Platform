import os
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "Smart Meter Intelligence Platform"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-smart-meter-key-2026")
    APP_MODE: str = os.getenv("APP_MODE", "hardware")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./smart_meter_intelligence.db")
    CORS_ORIGINS: list = ["*"]


settings = Settings()
