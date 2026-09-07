"""
Password hashing and JWT access tokens.

Password hashing/verification is ported from root-level users.py, which had
already-working, already-validated bcrypt logic — same calls, same defaults
(bcrypt.gensalt() with no arguments, i.e. the library's default work factor),
not reimplemented or retuned here.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import bcrypt
import jwt

from .config import settings

JWT_ALGORITHM = "HS256"


# ---------------------------------------------------------------------------
# Password hashing — ported as-is from users.py's hash_password/verify_password.
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    if not plain:
        raise ValueError("Password cannot be empty.")
    return bcrypt.hashpw(
        plain.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not plain or not hashed:
        return False
    return bcrypt.checkpw(
        plain.encode("utf-8"),
        hashed.encode("utf-8"),
    )


# ---------------------------------------------------------------------------
# JWT access tokens
# ---------------------------------------------------------------------------

def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Raises jwt.PyJWTError (ExpiredSignatureError, InvalidTokenError, etc.)
    on any missing/invalid/expired/tampered token — callers decide how to
    turn that into an HTTP response."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
