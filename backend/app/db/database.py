import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

try:
    from dotenv import load_dotenv
    # Skip loading a real .env during test runs — same reasoning as
    # config.py's identical guard: a real .env on disk must never leak
    # into a test process no matter what it contains. When TESTING is
    # unset, this is byte-for-byte the same unconditional load_dotenv()
    # call as before.
    if os.getenv("TESTING", "0") != "1":
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

    _engine_url = DATABASE_URL
    _engine_kwargs = {
        "echo": False,
        "pool_pre_ping": True,
        "connect_args": {"connect_timeout": 10},
    }

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
