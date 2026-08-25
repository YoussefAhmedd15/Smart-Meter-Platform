import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator

# SQLite fallback for seamless out-of-the-box local operation, PostgreSQL URL when DB is active
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./smart_meter_intelligence.db"
)

# SQLite setup requires check_same_thread=False
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing database session to FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes database tables if they do not exist."""
    from . import models  # Ensure all models are loaded
    Base.metadata.create_all(bind=engine)
