"""Пароли (PBKDF2, stdlib) и cookie-сессии."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import SESSION_COOKIE, SESSION_TTL_DAYS
from app.database import get_db
from app.models import AuthSession, User

_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITERATIONS)
    return f"pbkdf2${_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt, expected = stored.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations))
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


def create_session(db: Session, user: User) -> AuthSession:
    session = AuthSession(
        token=secrets.token_urlsafe(32),
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=SESSION_TTL_DAYS),
    )
    db.add(session)
    db.commit()
    return session


def delete_session(db: Session, token: str) -> None:
    db.query(AuthSession).filter(AuthSession.token == token).delete()
    db.commit()


def get_current_user(
    db: Session = Depends(get_db),
    kydir_session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> User:
    if not kydir_session:
        raise HTTPException(status_code=401, detail="Не авторизован")
    session = db.get(AuthSession, kydir_session)
    if session is None or session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Сессия истекла")
    return session.user
