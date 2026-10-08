from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import settings

ph = PasswordHasher()
ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    return ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, plain)
    except (VerifyMismatchError, InvalidHashError):
        return False


def _create_token(user_id: int, token_type: str, expires: timedelta) -> str:
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "exp": datetime.now(timezone.utc) + expires,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_access_token(user_id: int) -> str:
    return _create_token(
        user_id, "access", timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        user_id, "refresh", timedelta(days=settings.refresh_token_expire_days)
    )


def decode_token(token: str, expected_type: str) -> dict:
    """jwt.InvalidTokenError token rusak, kedaluwarsa, salah tipe."""
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("wrong token type")
    return payload