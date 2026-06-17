import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from netagent_db.models import AdminUser, Plan


PLAN_SEED = [
    {
        "slug": "start",
        "name": "Start",
        "description": "Для одного телефона или ноутбука",
        "duration_days": 30,
        "price_rub": 150,
        "device_limit": 1,
        "sort_order": 1,
    },
    {
        "slug": "standard",
        "name": "Standard",
        "description": "Оптимально: телефон + ноутбук",
        "duration_days": 30,
        "price_rub": 250,
        "device_limit": 2,
        "sort_order": 2,
    },
    {
        "slug": "family",
        "name": "Family",
        "description": "Для семьи или нескольких личных устройств",
        "duration_days": 30,
        "price_rub": 350,
        "device_limit": 3,
        "sort_order": 3,
    },
]


def seed_plans(session: Session) -> None:
    existing = session.scalar(select(Plan.id).limit(1))
    if existing is not None:
        return
    for item in PLAN_SEED:
        session.add(Plan(**item))
    session.commit()


def seed_admin(session: Session) -> None:
    email = os.getenv("ADMIN_SEED_EMAIL", "adkharlamov.dev@gmail.com").strip()
    password = os.getenv("ADMIN_SEED_PASSWORD", "").strip()
    if not password:
        return

    exists = session.scalar(select(AdminUser.id).where(AdminUser.email == email))
    if exists is not None:
        return

    from passlib.hash import bcrypt

    session.add(
        AdminUser(
            email=email,
            password_hash=bcrypt.hash(password),
            role="admin",
        )
    )
    session.commit()


def run_seed(session: Session) -> None:
    seed_plans(session)
    seed_admin(session)
