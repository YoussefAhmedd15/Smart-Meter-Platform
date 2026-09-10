"""
Endpoint tests for backend/app/api/admin.py's user-management routes.
Confirmed zero dedicated test coverage existed for these routes before
this file — require_role() itself was tested (test_auth.py), but only
against a synthetic throwaway route, never against these real ones.

Same isolation mechanism as test_meter_endpoints.py (see that file's
docstring for the full explanation): conftest.py's TESTING=1 forces
in-memory SQLite regardless of DATABASE_URL, which is the actual current
behavior of every test in this directory.

Uses TestClient against the REAL backend.app.main.app (which already
includes admin_router) with only the DB session overridden.
"""
import os
import sys

os.environ["TESTING"] = "1"
os.environ.setdefault("SECRET_KEY", "test-only-secret-" + os.urandom(16).hex())
os.environ.setdefault("APP_MODE", "demo")

GRANDPARENT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if GRANDPARENT not in sys.path:
    sys.path.insert(0, GRANDPARENT)

import unittest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from backend.app.main import app  # noqa: E402
from backend.app.db.database import Base, get_db  # noqa: E402
from backend.app.db.models import User  # noqa: E402
from backend.app.core.security import create_access_token, hash_password, verify_password  # noqa: E402


def _make_test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


class AdminEndpointTests(unittest.TestCase):
    def setUp(self):
        self._engine = _make_test_engine()
        self.SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

        def override_get_db():
            db = self.SessionFactory()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

        db = self.SessionFactory()
        self.admin = User(
            email="admin-endpoint-test@example.com",
            password_hash=hash_password("irrelevant-test-password"),
            role="admin",
            is_active=True,
        )
        self.tester = User(
            email="tester-endpoint-test@example.com",
            password_hash=hash_password("irrelevant-test-password"),
            role="tester",
            is_active=True,
        )
        db.add_all([self.admin, self.tester])
        db.commit()
        db.refresh(self.admin)
        db.refresh(self.tester)
        self.admin_token = create_access_token(self.admin.user_id, self.admin.role)
        self.tester_token = create_access_token(self.tester.user_id, self.tester.role)
        db.close()

    def tearDown(self):
        app.dependency_overrides.clear()
        self._engine.dispose()

    def _admin_headers(self):
        return {"Authorization": f"Bearer {self.admin_token}"}

    def _tester_headers(self):
        return {"Authorization": f"Bearer {self.tester_token}"}

    def _get_user_by_email(self, email):
        db = self.SessionFactory()
        try:
            return db.query(User).filter(User.email == email).first()
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # GET /api/admin/users
    # ------------------------------------------------------------------ #

    def test_list_users_401_with_no_token(self):
        resp = self.client.get("/api/admin/users")
        self.assertEqual(resp.status_code, 401, resp.text)

    def test_list_users_403_with_non_admin_token(self):
        resp = self.client.get("/api/admin/users", headers=self._tester_headers())
        self.assertEqual(resp.status_code, 403, resp.text)

    def test_list_users_200_with_real_data_for_admin_token(self):
        resp = self.client.get("/api/admin/users", headers=self._admin_headers())
        self.assertEqual(resp.status_code, 200, resp.text)
        emails = {u["email"] for u in resp.json()}
        self.assertIn("admin-endpoint-test@example.com", emails)
        self.assertIn("tester-endpoint-test@example.com", emails)

    # ------------------------------------------------------------------ #
    # POST /api/admin/users
    # ------------------------------------------------------------------ #

    def test_create_user_403_for_non_admin(self):
        resp = self.client.post(
            "/api/admin/users",
            headers=self._tester_headers(),
            json={"email": "should-not-be-created@example.com", "password": "SomePass123!", "role": "tester"},
        )
        self.assertEqual(resp.status_code, 403, resp.text)
        self.assertIsNone(self._get_user_by_email("should-not-be-created@example.com"))

    def test_create_user_admin_can_set_role_admin(self):
        """Confirms admin-only role="admin" creation is actually enforced
        by the endpoint, not merely assumed — created via the real route,
        then checked directly in the DB."""
        resp = self.client.post(
            "/api/admin/users",
            headers=self._admin_headers(),
            json={"email": "new-admin@example.com", "password": "NewAdminPass123!", "role": "admin"},
        )
        self.assertEqual(resp.status_code, 201, resp.text)
        body = resp.json()
        self.assertEqual(body["role"], "admin")

        db_user = self._get_user_by_email("new-admin@example.com")
        self.assertIsNotNone(db_user)
        self.assertEqual(db_user.role, "admin")
        self.assertTrue(verify_password("NewAdminPass123!", db_user.password_hash))

    def test_create_user_email_conflict_returns_409(self):
        """Confirmed current real behavior (not assumed): admin.py raises
        HTTPException(409, "A user with this email already exists.")."""
        resp = self.client.post(
            "/api/admin/users",
            headers=self._admin_headers(),
            json={"email": "admin-endpoint-test@example.com", "password": "Whatever123!", "role": "tester"},
        )
        self.assertEqual(resp.status_code, 409, resp.text)

    def test_create_user_invalid_role_returns_422(self):
        resp = self.client.post(
            "/api/admin/users",
            headers=self._admin_headers(),
            json={"email": "bad-role@example.com", "password": "Whatever123!", "role": "superuser"},
        )
        self.assertEqual(resp.status_code, 422, resp.text)

    # ------------------------------------------------------------------ #
    # PUT /api/admin/users/{id}
    # ------------------------------------------------------------------ #

    def test_update_user_403_for_non_admin(self):
        resp = self.client.put(
            f"/api/admin/users/{self.tester.user_id}",
            headers=self._tester_headers(),
            json={"role": "admin"},
        )
        self.assertEqual(resp.status_code, 403, resp.text)

    def test_update_user_admin_can_change_real_fields(self):
        resp = self.client.put(
            f"/api/admin/users/{self.tester.user_id}",
            headers=self._admin_headers(),
            json={"role": "admin", "is_active": False},
        )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["role"], "admin")
        self.assertFalse(body["is_active"])

        db_user = self._get_user_by_email("tester-endpoint-test@example.com")
        self.assertEqual(db_user.role, "admin")
        self.assertFalse(db_user.is_active)

    def test_update_user_404_for_nonexistent_user(self):
        resp = self.client.put(
            "/api/admin/users/999999",
            headers=self._admin_headers(),
            json={"role": "admin"},
        )
        self.assertEqual(resp.status_code, 404, resp.text)

    # ------------------------------------------------------------------ #
    # DELETE /api/admin/users/{id}
    # ------------------------------------------------------------------ #

    def test_delete_user_403_for_non_admin(self):
        resp = self.client.delete(f"/api/admin/users/{self.admin.user_id}", headers=self._tester_headers())
        self.assertEqual(resp.status_code, 403, resp.text)

    def test_delete_user_removes_the_real_row(self):
        resp = self.client.delete(f"/api/admin/users/{self.tester.user_id}", headers=self._admin_headers())
        self.assertEqual(resp.status_code, 204, resp.text)
        self.assertIsNone(self._get_user_by_email("tester-endpoint-test@example.com"))

    def test_delete_self_is_blocked(self):
        """Confirmed existing logic (admin.py: "An admin cannot delete
        themselves.") — a permanent regression test for it."""
        resp = self.client.delete(f"/api/admin/users/{self.admin.user_id}", headers=self._admin_headers())
        self.assertEqual(resp.status_code, 400, resp.text)
        # The account must still be there — the block actually prevented
        # the delete, not just returned an error after deleting anyway.
        self.assertIsNotNone(self._get_user_by_email("admin-endpoint-test@example.com"))

    def test_delete_user_404_for_nonexistent_user(self):
        resp = self.client.delete("/api/admin/users/999999", headers=self._admin_headers())
        self.assertEqual(resp.status_code, 404, resp.text)


if __name__ == "__main__":
    unittest.main()
