import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from netagent_db.models import AdminUser, Plan


PLAN_SEED = [
    {
        "slug": "combo_max",
        "name": "Combo Max",
        "description": "3 устройства + AI без лимита — для семьи",
        "duration_days": 30,
        "price_rub": 449,
        "device_limit": 3,
        "sort_order": 1,
        "product_type": "bundle",
    },
    {
        "slug": "combo",
        "name": "Combo",
        "description": "Подключение + AI без лимита · 1 устройство",
        "duration_days": 30,
        "price_rub": 299,
        "device_limit": 1,
        "sort_order": 2,
        "product_type": "bundle",
    },
    {
        "slug": "connect_plus",
        "name": "Connect+",
        "description": "Стабильное подключение · 2 устройства",
        "duration_days": 30,
        "price_rub": 279,
        "device_limit": 2,
        "sort_order": 3,
        "product_type": "vpn",
    },
    {
        "slug": "connect",
        "name": "Connect",
        "description": "Стабильное подключение · 1 устройство",
        "duration_days": 30,
        "price_rub": 179,
        "device_limit": 1,
        "sort_order": 4,
        "product_type": "vpn",
    },
    {
        "slug": "lite_ai",
        "name": "Lite AI",
        "description": "AI-ассистент без лимита сообщений",
        "duration_days": 30,
        "price_rub": 99,
        "device_limit": 0,
        "sort_order": 5,
        "product_type": "ai",
    },
]


def seed_plans(session: Session) -> None:
    for item in PLAN_SEED:
        exists = session.scalar(select(Plan.id).where(Plan.slug == item["slug"]))
        if exists is None:
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
