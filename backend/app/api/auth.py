from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db.models import User
from ..schemas.schemas import (
    UserRegisterRequest, UserLoginRequest, UserPublicResponse, TokenResponse,
)
from ..core.security import hash_password, verify_password, create_access_token
from ..core.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Same generic message for "no such user" and "wrong password" — deliberately
# not distinguishing them, so a caller can't use this endpoint to enumerate
# registered emails.
_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid email or password.",
)

# The only role public self-registration can ever create. Not read from the
# request — UserRegisterRequest doesn't even have a `role` field. Creating a
# user with an elevated role (admin, etc.) must go through a separate,
# authenticated, require_role("admin")-protected endpoint — not this one.
_SELF_REGISTER_ROLE = "tester"


@router.post("/register", response_model=UserPublicResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserRegisterRequest, db: Session = Depends(get_db)):
    email = data.email.strip().lower()
    if not email:
        raise HTTPException(status_code=422, detail="Email cannot be empty.")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="A user with this email already exists.")

    user = User(
        email=email,
        password_hash=hash_password(data.password),
        role=_SELF_REGISTER_ROLE,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: UserLoginRequest, db: Session = Depends(get_db)):
    email = data.email.strip().lower() if data.email else ""
    user = db.query(User).filter(User.email == email).first()

    if user is None or not user.is_active or not verify_password(data.password, user.password_hash):
        # Deliberately identical whether the email doesn't exist, the account
        # is inactive, or the password is wrong.
        raise _INVALID_CREDENTIALS

    token = create_access_token(user.user_id, user.role)
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout():
    """No-op: this is a stateless JWT setup with no token-blacklist mechanism
    anywhere in the codebase, and none is introduced here. "Logout" is the
    client discarding its access token — this endpoint exists so a frontend
    has something to call, not because the server does anything with it."""
    return {"detail": "Logged out. Discard the access token client-side."}


@router.get("/me", response_model=UserPublicResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
