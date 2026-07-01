from sqlalchemy import select
from sqlalchemy.orm import Session

from netagent_db.models import User
from webapp.auth import hash_password, verify_password


class AuthError(ValueError):
    pass


def register_user(session: Session, email: str, password: str) -> User:
    normalized = email.strip().lower()
    if len(password) < 8:
        raise AuthError("Пароль — минимум 8 символов")
    if not normalized or "@" not in normalized:
        raise AuthError("Укажите корректный email")

    exists = session.scalar(select(User.id).where(User.email == normalized))
    if exists:
        raise AuthError("Email уже зарегистрирован")

    user = User(
        email=normalized,
        password_hash=hash_password(password),
        status="active",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    normalized = email.strip().lower()
    user = session.scalar(select(User).where(User.email == normalized))
    if not user or not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
