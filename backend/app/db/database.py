import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. This app requires PostgreSQL — there is no SQLite "
        "fallback. Set DATABASE_URL to a postgresql:// connection string, e.g.\n"
        "  postgresql://postgres:<password>@localhost:5432/smart_meter_db\n"
        "See .env.example, or docker-compose.yml if you're running via Docker."
    )

if not (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgresql+")):
    raise RuntimeError(
        f"DATABASE_URL must be a PostgreSQL connection string (postgresql://...). "
        f"Got: {DATABASE_URL.split('://')[0]}://... — SQLite and other engines are "
        f"not supported by this app."
    )

engine = create_engine(
    DATABASE_URL,
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
    """Initializes database tables if they do not exist.

    Note: this only creates tables that don't already exist — it does not alter
    existing ones. Once Alembic migrations are in place (see alembic/), schema
    changes should go through a migration, not a change to models.py alone.
    """
    from . import models  # Ensure all models are loaded
    Base.metadata.create_all(bind=engine)
