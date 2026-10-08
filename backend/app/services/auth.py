import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import Business, User
from app.models.enums import Role
from app.schemas.auth import RegisterBusinessRequest


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "bisnis"


def _unique_slug(db: Session, name: str) -> str:
    base = _slugify(name)
    slug, n = base, 1
    while db.scalar(select(Business.id).where(Business.slug == slug)):
        n += 1
        slug = f"{base}-{n}"
    return slug


def register_business(db: Session, data: RegisterBusinessRequest) -> User:
    if get_user_by_email(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email sudah terdaftar")

    business = Business(name=data.business_name, slug=_unique_slug(db, data.business_name))
    admin = User(
        business=business,
        name=data.admin_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=Role.admin,
    )
    db.add(admin) 
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email atau slug sudah dipakai")
    db.refresh(admin)
    return admin


def authenticate(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Email atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user