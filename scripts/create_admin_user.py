"""
Provisions a real admin account against the real configured database.

Unlike scripts/seed_demo.py — which is confined to disposable/demo
databases by its own --force-neon guard and ships a documented fallback
demo credential — this script may be run against the real shared
database. It gets the same strictness as SECRET_KEY's guard: no
hardcoded credential, no default, fails loudly if unset.

Usage:
    ADMIN_EMAIL=you@example.com ADMIN_PASSWORD=... python scripts/create_admin_user.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv()

from backend.app.db.database import init_db, SessionLocal
from backend.app.db.models import User
from backend.app.core.security import hash_password

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if not ADMIN_EMAIL or not ADMIN_PASSWORD:
    raise RuntimeError(
        "ADMIN_EMAIL and ADMIN_PASSWORD are not set. Set them before running this script "
        "(see .env.example) — there is no hardcoded default."
    )

email = ADMIN_EMAIL.strip().lower()
role = "admin"

init_db()
db = SessionLocal()
try:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        # Fail loudly rather than silently overwrite an existing account's
        # password/role — re-running this script for an email that already
        # exists is far more likely to be a mistake than an intentional
        # reset, and a silent overwrite of a real admin's credentials is
        # exactly the kind of thing that should never happen by accident.
        raise RuntimeError(
            f"A user with email {email} already exists (user_id={existing.user_id}, "
            f"role={existing.role!r}). Refusing to overwrite their password/role. "
            "If you intend to change this account, do it explicitly via the admin API "
            "(PUT /api/admin/users/{id}) or by hand — not by re-running this script."
        )

    user = User(
        email=email,
        password_hash=hash_password(ADMIN_PASSWORD),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"SUCCESS: created admin user user_id={user.user_id} email={user.email} role={user.role}")
finally:
    db.close()
