"""Password hashing, JWT cookies, and CSRF helpers."""

import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.config import Settings, get_settings

password_hasher = PasswordHash.recommended()

JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password, password_hash)
    except Exception:
        return False


def create_access_token(
    *,
    user_id: int,
    shop_id: int | None,
    role: str,
    settings: Settings | None = None,
) -> str:
    settings = settings or get_settings()
    secret = settings.require_jwt_secret()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "shop_id": shop_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    secret = settings.require_jwt_secret()
    return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def csrf_tokens_match(expected: str | None, provided: str | None) -> bool:
    if not expected or not provided:
        return False
    return hmac.compare_digest(expected, provided)
