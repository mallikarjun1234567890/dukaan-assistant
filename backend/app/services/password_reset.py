"""Create and consume one-time password reset tokens."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from threading import Lock

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PasswordResetToken, User, utc_now

TOKEN_MINUTES = 60


class ResetRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, list[datetime]] = {}
        self._lock = Lock()

    def too_many(self, email: str, limit: int = 5) -> bool:
        now = datetime.now(timezone.utc)
        window = now - timedelta(hours=1)
        with self._lock:
            stamps = [ts for ts in self._hits.get(email, []) if ts > window]
            if len(stamps) >= limit:
                return True
            stamps.append(now)
            self._hits[email] = stamps
        return False


rate_limiter = ResetRateLimiter()


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def issue_reset_token(db: Session, user: User) -> str:
    raw = secrets.token_urlsafe(32)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=utc_now() + timedelta(minutes=TOKEN_MINUTES),
        )
    )
    db.commit()
    return raw


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def consume_reset_token(db: Session, raw: str) -> User | None:
    row = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(raw.strip()))
    )
    now = utc_now()
    if row is None or row.used_at is not None or _aware(row.expires_at) <= now:
        return None
    user = db.get(User, row.user_id)
    if user is None:
        return None
    row.used_at = now
    return user
