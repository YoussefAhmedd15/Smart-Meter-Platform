"""
Endpoint tests for the meter routes in backend/app/main.py, backed by
backend/app/services/meter_service.py — connect, disconnect, readings, and
profile. Confirmed zero dedicated test coverage existed for this area
before this file.

Isolation note (confirmed empirically before writing this file, not
assumed): conftest.py sets TESTING=1 unconditionally for every test module
in this directory, and backend/app/db/database.py's TESTING branch binds
an in-memory SQLite engine *regardless of DATABASE_URL/TEST_DATABASE_URL*.
That means every test in backend/tests/ — including this one — actually
runs against SQLite today, not real PostgreSQL, no matter what env vars
are set. (test_test_case_sync_workflow.py's docstring claims "real
PostgreSQL... no SQLite fallback", but that claim is now stale relative to
the current database.py — TESTING=1 overrides it unconditionally.)

One real, known coverage gap from this: Meter.last_seen is a Postgres
TIMESTAMPTZ in production and comes back timezone-aware; SQLite has no
such concept and always returns naive datetimes. get_meter_profile()'s
"normalize an aware timestamp" branch (added to fix a real aware/naive
TypeError bug) is therefore not exercised here — only its "normalize a
naive timestamp" branch is. The staleness/is_online *behavior* itself is
still fully exercised.

Uses TestClient against the REAL backend.app.main.app and its REAL
routes — only the DB session is swapped via FastAPI's
dependency_overrides (the standard FastAPI testing pattern), so this
exercises the actual endpoint wiring (auth dependencies, response models,
status codes), not a reimplemented stand-in route.
"""
import os
import sys
from datetime import datetime, timedelta

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
from backend.app.db.models import Meter, MeterReading, TestRun, User  # noqa: E402
from backend.app.core.security import create_access_token, hash_password  # noqa: E402


def _make_test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


class MeterEndpointTests(unittest.TestCase):
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
        user = User(
            email="meter-endpoint-test@example.com",
            password_hash=hash_password("irrelevant-test-password"),
            role="tester",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        self.token = create_access_token(user.user_id, user.role)
        db.close()

    def tearDown(self):
        app.dependency_overrides.clear()
        self._engine.dispose()

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def _get_meter(self, meter_id):
        db = self.SessionFactory()
        try:
            return db.query(Meter).filter(Meter.meter_id == meter_id).first()
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # connect
    # ------------------------------------------------------------------ #

    def test_connect_requires_auth(self):
        resp = self.client.post("/api/meters/1/connect")
        self.assertEqual(resp.status_code, 401, resp.text)

    def test_connect_sets_real_status_online_and_last_seen(self):
        resp = self.client.post("/api/meters/1/connect", headers=self._auth_headers())
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertTrue(body["connected"])
        meter_id = body["meter_id"]

        db_meter = self._get_meter(meter_id)
        self.assertIsNotNone(db_meter)
        self.assertEqual(db_meter.status, "ONLINE")
        self.assertIsNotNone(db_meter.last_seen)

    # ------------------------------------------------------------------ #
    # disconnect
    # ------------------------------------------------------------------ #

    def test_disconnect_requires_auth(self):
        resp = self.client.post("/api/meters/1/disconnect")
        self.assertEqual(resp.status_code, 401, resp.text)

    def test_disconnect_persists_offline_status_and_last_seen_to_the_real_row(self):
        """Regression test for a real, previously-confirmed bug: disconnect
        must persist status/last_seen to the DB row, not just report
        success in the response body. Queries the DB directly rather than
        trusting the endpoint's own response."""
        connect_resp = self.client.post("/api/meters/1/connect", headers=self._auth_headers())
        meter_id = connect_resp.json()["meter_id"]
        pre_last_seen = self._get_meter(meter_id).last_seen
        self.assertEqual(self._get_meter(meter_id).status, "ONLINE")

        disconnect_resp = self.client.post(f"/api/meters/{meter_id}/disconnect", headers=self._auth_headers())
        self.assertEqual(disconnect_resp.status_code, 200, disconnect_resp.text)
        self.assertEqual(disconnect_resp.json()["status"], "OFFLINE")

        db_meter = self._get_meter(meter_id)
        self.assertEqual(db_meter.status, "OFFLINE")
        self.assertIsNotNone(db_meter.last_seen)
        self.assertGreaterEqual(db_meter.last_seen, pre_last_seen)

    # ------------------------------------------------------------------ #
    # readings
    # ------------------------------------------------------------------ #

    def test_readings_returns_real_data_source_and_takes_a_fresh_read_every_call(self):
        """No auth required on this route (confirmed in main.py — no
        Depends(get_current_user) on GET /readings). Confirmed current
        behavior (superseding an older "only refresh if empty" design):
        every call takes a genuinely fresh read, not a replay of the first
        call's rows — verified by asserting the reading count actually
        grows across two calls, not just that the response looks plausible."""
        resp1 = self.client.get("/api/meters/1/readings")
        self.assertEqual(resp1.status_code, 200, resp1.text)
        body1 = resp1.json()
        self.assertGreater(len(body1), 0)
        for row in body1:
            self.assertEqual(row["data_source"], "mock")

        db = self.SessionFactory()
        count_after_first_call = db.query(MeterReading).count()
        db.close()

        resp2 = self.client.get("/api/meters/1/readings")
        self.assertEqual(resp2.status_code, 200, resp2.text)

        db = self.SessionFactory()
        count_after_second_call = db.query(MeterReading).count()
        db.close()
        self.assertGreater(count_after_second_call, count_after_first_call)

    # ------------------------------------------------------------------ #
    # profile
    # ------------------------------------------------------------------ #

    def test_profile_with_no_test_runs_is_offline_and_not_certified(self):
        connect_resp = self.client.post("/api/meters/1/connect", headers=self._auth_headers())
        meter_id = connect_resp.json()["meter_id"]

        # Force last_seen far in the past directly in the DB — the same
        # DB-timestamp-manipulation approach used in the original Meter
        # Profile session to test staleness without waiting real minutes.
        db = self.SessionFactory()
        m = db.query(Meter).filter(Meter.meter_id == meter_id).first()
        m.last_seen = datetime.utcnow() - timedelta(hours=1)
        db.commit()
        db.close()

        resp = self.client.get(f"/api/meters/{meter_id}/profile")
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertFalse(body["is_online"])
        self.assertFalse(body["is_certified"])
        self.assertIsNone(body["last_test_run"])
        self.assertEqual(body["total_test_runs"], 0)

    def test_profile_recent_pass_and_recent_contact_is_certified(self):
        connect_resp = self.client.post("/api/meters/1/connect", headers=self._auth_headers())
        meter_id = connect_resp.json()["meter_id"]
        # connect already set last_seen to "now" — real recent contact.

        db = self.SessionFactory()
        run = TestRun(
            meter_id=meter_id,
            status="COMPLETED",
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            duration_seconds=1.23,
            total_tests=3,
            passed_tests=3,
            failed_tests=0,
        )
        db.add(run)
        db.commit()
        db.close()

        resp = self.client.get(f"/api/meters/{meter_id}/profile")
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertTrue(body["is_online"])
        self.assertTrue(body["is_certified"])
        self.assertEqual(body["last_test_run"]["status"], "COMPLETED")
        self.assertEqual(body["total_test_runs"], 1)

    def test_profile_stale_last_seen_is_offline_regardless_of_passed_run(self):
        connect_resp = self.client.post("/api/meters/1/connect", headers=self._auth_headers())
        meter_id = connect_resp.json()["meter_id"]

        db = self.SessionFactory()
        run = TestRun(
            meter_id=meter_id,
            status="COMPLETED",
            started_at=datetime.utcnow(),
            finished_at=datetime.utcnow(),
            duration_seconds=1.0,
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
        )
        db.add(run)
        m = db.query(Meter).filter(Meter.meter_id == meter_id).first()
        # Stale — well past the 5-minute ONLINE_STALENESS_THRESHOLD.
        m.last_seen = datetime.utcnow() - timedelta(minutes=30)
        db.commit()
        db.close()

        resp = self.client.get(f"/api/meters/{meter_id}/profile")
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertFalse(body["is_online"])
        self.assertFalse(body["is_certified"])  # certified requires BOTH online AND a passed run

    def test_profile_404s_for_a_meter_that_does_not_exist(self):
        resp = self.client.get("/api/meters/999999/profile")
        self.assertEqual(resp.status_code, 404, resp.text)


if __name__ == "__main__":
    unittest.main()
