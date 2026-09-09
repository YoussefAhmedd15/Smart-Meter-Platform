"""
Admin-only user management API.

All routes require the caller's JWT role == "admin".
Public self-registration (/auth/register) is intentionally separate and never
touches these endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..db.database import get_db
from ..db.models import User
from ..schemas.schemas import UserPublicResponse, UserCreateAdmin, UserUpdateAdmin
from ..core.security import hash_password
from ..core.dependencies import require_role

router = APIRouter(prefix="/api/admin", tags=["admin"])

# All routes in this file require admin role.
_admin_required = require_role("admin")


@router.get("/users", response_model=List[UserPublicResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(_admin_required),
):
    """Return all registered users (admin-only)."""
    return db.query(User).order_by(User.user_id).all()


@router.post("/users", response_model=UserPublicResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreateAdmin,
    db: Session = Depends(get_db),
    _: User = Depends(_admin_required),
):
    """Create a user with any role (admin-only)."""
    email = data.email.strip().lower()
    if not email:
        raise HTTPException(status_code=422, detail="Email cannot be empty.")

    allowed_roles = {"tester", "admin"}
    if data.role not in allowed_roles:
        raise HTTPException(status_code=422, detail=f"Role must be one of: {', '.join(sorted(allowed_roles))}.")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="A user with this email already exists.")

    user = User(
        email=email,
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserPublicResponse)
def update_user(
    user_id: int,
    data: UserUpdateAdmin,
    db: Session = Depends(get_db),
    current_admin: User = Depends(_admin_required),
):
    """Update any field on a user (admin-only)."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    allowed_roles = {"tester", "admin"}

    if data.email is not None:
        new_email = data.email.strip().lower()
        if not new_email:
            raise HTTPException(status_code=422, detail="Email cannot be empty.")
        conflict = db.query(User).filter(User.email == new_email, User.user_id != user_id).first()
        if conflict:
            raise HTTPException(status_code=409, detail="That email is already taken.")
        user.email = new_email

    if data.password is not None:
        if not data.password:
            raise HTTPException(status_code=422, detail="Password cannot be empty.")
        user.password_hash = hash_password(data.password)

    if data.role is not None:
        if data.role not in allowed_roles:
            raise HTTPException(status_code=422, detail=f"Role must be one of: {', '.join(sorted(allowed_roles))}.")
        user.role = data.role

    if data.is_active is not None:
        user.is_active = data.is_active

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(_admin_required),
):
    """Delete a user (admin-only). An admin cannot delete themselves."""
    if current_admin.user_id == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    db.delete(user)
    db.commit()
