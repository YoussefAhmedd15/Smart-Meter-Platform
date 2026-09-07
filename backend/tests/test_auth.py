"""
Auth-layer tests for code paths that had no automated coverage:

- decode_access_token / get_current_user rejecting a genuinely EXPIRED token
  (only garbage/tampered tokens had been exercised before, live via curl —
  not as an automated test).
- require_role() actually gating a route by role. Nothing in this codebase
  had ever called it before this file — it existed but had zero real
  exercise.

Runs against a real PostgreSQL database, same TEST_DATABASE_URL/DATABASE_URL
convention as test_test_case_sync_workflow.py — no SQLite fallback. Uses a
real FastAPI TestClient (not mocks) with tiny throwaway routes defined only
in this file, so this never touches the real app's route table.
"""
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

GRANDPARENT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if GRANDPARENT not in sys.path:
    sys.path.insert(0, GRANDPARENT)

_TEST_DB_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
if not _TEST_DB_URL:
    raise RuntimeError(
        "Set TEST_DATABASE_URL (or DATABASE_URL) to a PostgreSQL connection "
        "string before running this test file — there is no SQLite fallback."
    )
os.environ["DATABASE_URL"] = _TEST_DB_URL
os.environ.setdefault("APP_MODE", "demo")
os.environ.setdefault("SECRET_KEY", "test-only-secret-" + os.urandom(16).hex())

from backend.app.core.config import settings  # noqa: E402
from backend.app.core.security import create_access_token, hash_password  # noqa: E402
from backend.app.core.dependencies import get_current_user, require_role  # noqa: E402
from backend.app.db.database import SessionLocal, init_db  # noqa: E402
from backend.app.db.models import User  # noqa: E402

init_db()


def _make_user(email: str, role: str) -> User:
    """Own session per call, deliberately — SessionLocal defaults to
    expire_on_commit=True, so reusing one session across multiple creates
    silently re-expires earlier objects on each later commit(), which then
    can't be reloaded once the shared session closes. One session per user
    avoids that entirely."""
    db = SessionLocal()
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
        # Detach with attributes already loaded so it's safe to read after
        # this function's session closes.
        db.expunge(user)
        return user
    finally:
        db.close()


class ExpiredTokenTests(unittest.TestCase):
    """get_current_user must 401 an expired token, not crash or accept it."""

    def test_expired_token_is_rejected(self):
        user = _make_user("expiry-check@example.com", "tester")

        now = datetime.now(timezone.utc)
        expired_payload = {
            "sub": str(user.user_id),
            "role": user.role,
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),  # expired an hour ago
        }
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm="HS256")

        app = FastAPI()

        @app.get("/whoami")
        def whoami(current_user: User = Depends(get_current_user)):
            return {"email": current_user.email}

        client = TestClient(app)
        resp = client.get("/whoami", headers={"Authorization": f"Bearer {expired_token}"})
        self.assertEqual(resp.status_code, 401, resp.text)


class RequireRoleTests(unittest.TestCase):
    """require_role("admin") must 403 a non-admin and 200 an admin, against a
    real (throwaway) protected route — the one piece of Session B's auth
    logic that had never actually been run before this."""

    def setUp(self):
        self.admin = _make_user("role-check-admin@example.com", "admin")
        self.tester = _make_user("role-check-tester@example.com", "tester")

        self.admin_token = create_access_token(self.admin.user_id, self.admin.role)
        self.tester_token = create_access_token(self.tester.user_id, self.tester.role)

        app = FastAPI()

        @app.get("/admin-only")
        def admin_only(current_user: User = Depends(require_role("admin"))):
            return {"ok": True, "email": current_user.email}

        self.client = TestClient(app)

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
