from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User
from app.schemas.user import UserCreate
from app.services.auth import get_user_by_email


def list_users(db: Session, admin: User) -> list[User]:
    return list(
        db.scalars(
            select(User).where(User.business_id == admin.business_id).order_by(User.id)
        )
    )


def create_user(db: Session, admin: User, data: UserCreate) -> User:
    if get_user_by_email(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email sudah terdaftar")

    user = User(
        business_id=admin.business_id,  # SELALU dari admin yang login, bukan dari body
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email sudah terdaftar")
    db.refresh(user)
    return user