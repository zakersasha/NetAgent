import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from netagent_db.models import AdminUser, Plan


PLAN_SEED = [
    {
        "slug": "combo_max",
        "name": "Семья",
        "description": "до 5 устройств · семья + AI-помощник",
        "duration_days": 30,
        "price_rub": 399,
        "device_limit": 5,
        "traffic_limit_gb": 150,
        "sort_order": 1,
        "product_type": "bundle",
    },
    {
        "slug": "combo",
        "name": "Стандарт",
        "description": "до 3 устройств · канал и AI-помощник",
        "duration_days": 30,
        "price_rub": 279,
        "device_limit": 3,
        "traffic_limit_gb": 80,
        "sort_order": 2,
        "product_type": "bundle",
    },
    {
        "slug": "connect_plus",
        "name": "Команда",
        "description": "до 3 устройств · малая команда",
        "duration_days": 30,
        "price_rub": 249,
        "device_limit": 3,
        "traffic_limit_gb": 80,
        "sort_order": 3,
        "product_type": "vpn",
    },
    {
        "slug": "connect",
        "name": "Личный",
        "description": "1 устройство · личная подписка",
        "duration_days": 30,
        "price_rub": 149,
        "device_limit": 1,
        "traffic_limit_gb": 40,
        "sort_order": 4,
        "product_type": "vpn",
    },
    {
        "slug": "lite_ai",
        "name": "AI Помощник",
        "description": "AI-помощник в Telegram без лимита",
        "duration_days": 30,
        "price_rub": 99,
        "device_limit": 0,
        "traffic_limit_gb": None,
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
