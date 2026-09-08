"""
Auth-layer tests for code paths that had no automated coverage:

- decode_access_token / get_current_user rejecting a genuinely EXPIRED token
  (only garbage/tampered tokens had been exercised before, live via curl —
  not as an automated test).
- require_role() actually gating a route by role. Nothing in this codebase
  had ever called it before this file — it existed but had zero real
  exercise.

Uses an in-memory SQLite database (TESTING=1) — no live PostgreSQL required.
The TESTING env-var is consumed by backend/app/db/database.py before its
PostgreSQL guards run, so the entire import chain works without any real DB.

FastAPI's dependency_overrides mechanism is used to inject a per-test
SQLite-backed Session, keeping each test's DB state fully isolated.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Set TESTING + SECRET_KEY BEFORE importing anything from the backend so that
# backend/app/db/database.py skips its postgresql:// guard and
# backend/app/core/config.py accepts a well-known test secret.
# ---------------------------------------------------------------------------
os.environ["TESTING"] = "1"
os.environ.setdefault("SECRET_KEY", "test-only-secret-" + os.urandom(16).hex())
os.environ.setdefault("APP_MODE", "demo")

GRANDPARENT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if GRANDPARENT not in sys.path:
    sys.path.insert(0, GRANDPARENT)

import jwt  # noqa: E402
from fastapi import Depends, FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlalchemy.orm import sessionmaker, Session  # noqa: E402

# Now safe to import — database.py will use SQLite in-memory.
from backend.app.core.config import settings  # noqa: E402
from backend.app.core.security import create_access_token, hash_password  # noqa: E402
from backend.app.core.dependencies import get_current_user, require_role  # noqa: E402
from backend.app.db.database import Base, get_db  # noqa: E402
from backend.app.db.models import User  # noqa: E402

# ---------------------------------------------------------------------------
# Per-test SQLite in-memory engine + session factory.
# Each test class creates its own engine so tables are fully isolated.
# ---------------------------------------------------------------------------

def _make_test_engine():
    """Create a fresh in-memory SQLite engine whose single connection is shared
    across all sessions (StaticPool). This keeps the tables and rows created
    during setUp visible to every subsequent request within the same test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


def _make_user(SessionFactory, email: str, role: str) -> User:
    """Create (or replace) a throwaway user via the given session factory."""
    db: Session = SessionFactory()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            db.delete(existing)
            db.commit()
        user = User(
            email=email,
            password_hash=hash_password("irrelevant-test-password-123"),
            role=role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.expunge(user)
        return user
    finally:
        db.close()


class ExpiredTokenTests(unittest.TestCase):
    """get_current_user must 401 an expired token, not crash or accept it."""

    def setUp(self):
        self._engine = _make_test_engine()
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
        self._TestSessionLocal = TestSessionLocal

        # Build a tiny throwaway FastAPI app with the DB override.
        app = FastAPI()

        def override_get_db():
            db = TestSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        @app.get("/whoami")
        def whoami(current_user: User = Depends(get_current_user)):
            return {"email": current_user.email}

        self.client = TestClient(app)
        self.user = _make_user(TestSessionLocal, "expiry-check@example.com", "tester")

    def tearDown(self):
        self._engine.dispose()

    def test_expired_token_is_rejected(self):
        now = datetime.now(timezone.utc)
        expired_payload = {
            "sub": str(self.user.user_id),
            "role": self.user.role,
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),  # expired an hour ago
        }
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm="HS256")

        resp = self.client.get("/whoami", headers={"Authorization": f"Bearer {expired_token}"})
        self.assertEqual(resp.status_code, 401, resp.text)


class RequireRoleTests(unittest.TestCase):
    """require_role("admin") must 403 a non-admin and 200 an admin, against a
    real (throwaway) protected route — the one piece of Session B's auth
    logic that had never actually been run before this."""

    def setUp(self):
        self._engine = _make_test_engine()
        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

        self.admin = _make_user(TestSessionLocal, "role-check-admin@example.com", "admin")
        self.tester = _make_user(TestSessionLocal, "role-check-tester@example.com", "tester")

        self.admin_token = create_access_token(self.admin.user_id, self.admin.role)
        self.tester_token = create_access_token(self.tester.user_id, self.tester.role)

        app = FastAPI()

        def override_get_db():
            db = TestSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        @app.get("/admin-only")
        def admin_only(current_user: User = Depends(require_role("admin"))):
            return {"ok": True, "email": current_user.email}

        self.client = TestClient(app)

    def tearDown(self):
        self._engine.dispose()

    def test_tester_is_403d(self):
        resp = self.client.get("/admin-only", headers={"Authorization": f"Bearer {self.tester_token}"})
        self.assertEqual(resp.status_code, 403, resp.text)

    def test_admin_is_200d(self):
        resp = self.client.get("/admin-only", headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["email"], "role-check-admin@example.com")

    def test_no_token_is_401d_not_403d(self):
        resp = self.client.get("/admin-only")
        self.assertEqual(resp.status_code, 401, resp.text)


if __name__ == "__main__":
    unittest.main()
