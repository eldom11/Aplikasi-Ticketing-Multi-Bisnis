import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.deps import get_current_user, get_db
from app.models import User
from app.schemas.auth import (
    AccessToken,
    LoginRequest,
    RefreshRequest,
    RegisterBusinessRequest,
    TokenPair,
)
from app.schemas.user import MeOut, UserOut
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register-business", response_model=UserOut, status_code=status.HTTP_201_CREATED
)
def register_business(data: RegisterBusinessRequest, db: Session = Depends(get_db)):
    return auth_service.register_business(db, data)


@router.post("/login", response_model=TokenPair)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, data.email, data.password)
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=AccessToken)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token, "refresh")
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Refresh token tidak valid atau kedaluwarsa",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if db.get(User, user_id) is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User tidak ditemukan")
    return AccessToken(access_token=create_access_token(user_id))


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user)):
    return user