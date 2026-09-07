from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from ..db.database import get_db
from ..db.models import User
from .security import decode_access_token

# tokenUrl is where a client would exchange credentials for a token — used
# for OpenAPI docs / the Swagger "Authorize" button, not enforced here.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decodes the JWT and loads the User it names. Raises 401 if the token
    is missing (handled by oauth2_scheme itself), invalid, expired, or the
    user it names no longer exists or is inactive."""
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise _CREDENTIALS_ERROR

    raw_user_id = payload.get("sub")
    if raw_user_id is None:
        raise _CREDENTIALS_ERROR
    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        raise _CREDENTIALS_ERROR

    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None or not user.is_active:
        raise _CREDENTIALS_ERROR
    return user


def require_role(*roles: str):
    """Dependency factory: `Depends(require_role("admin", "tester"))`.
    401s (via get_current_user) if there's no valid session at all; 403s if
    there is one but its role isn't in `roles`."""
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return current_user
    return dependency
