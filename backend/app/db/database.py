import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# TESTING escape hatch
# When TESTING=1 is set (automated test runs only), we use an in-memory SQLite
# engine so the test suite can run without a live PostgreSQL server. All
# production guards below remain fully in force when TESTING is not set.
# ---------------------------------------------------------------------------
_TESTING = os.getenv("TESTING", "0") == "1"

DATABASE_URL = os.getenv("DATABASE_URL")

if _TESTING:
    # In-memory SQLite — fast, isolated, zero infrastructure required.
    # StaticPool forces all connections to share the same in-memory DB so
    # tables created during setUp remain visible across request boundaries.
    from sqlalchemy.pool import StaticPool
    _engine_url = "sqlite:///:memory:"
    _engine_kwargs: dict = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
else:
    if not DATABASE_URL:
        # Graceful fallback to local SQLite database for development and testing
        _user_db = os.path.expanduser("~/.smart_meter.db").replace("\\", "/")
        _engine_url = f"sqlite:///{_user_db}"
        _engine_kwargs = {
            "connect_args": {"check_same_thread": False},
        }
    elif DATABASE_URL.startswith("sqlite"):
        _engine_url = DATABASE_URL
        _engine_kwargs = {
            "connect_args": {"check_same_thread": False},
        }
    elif DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgresql+"):
        _engine_url = DATABASE_URL
        _engine_kwargs = {
            "echo": False,
            "pool_pre_ping": True,
            "connect_args": {"connect_timeout": 10},
        }
    else:
        raise RuntimeError(
            f"DATABASE_URL must be a PostgreSQL or SQLite connection string. Got: {DATABASE_URL}"
        )

engine = create_engine(_engine_url, **_engine_kwargs)

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
    from . import models  # noqa: F401
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        import logging
        logging.getLogger("smart_meter_api").warning(
            f"init_db could not reach database ({exc})."
        )
