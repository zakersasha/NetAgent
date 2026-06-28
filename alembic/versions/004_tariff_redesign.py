"""New tariff lineup and bundle product type

Revision ID: 004
Revises: 003
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_PLANS = [
    ("combo_max", "Combo Max", "3 устройства + AI без лимита — для семьи", 449, 3, 1, "bundle"),
    ("combo", "Combo", "Подключение + AI без лимита · 1 устройство", 299, 1, 2, "bundle"),
    ("connect_plus", "Connect+", "Стабильное подключение · 2 устройства", 279, 2, 3, "vpn"),
    ("connect", "Connect", "Стабильное подключение · 1 устройство", 179, 1, 4, "vpn"),
    ("lite_ai", "Lite AI", "AI-ассистент без лимита сообщений", 99, 0, 5, "ai"),
]


def _plan_params(
    slug: str,
    name: str,
    desc: str,
    price: int,
    device_limit: int,
    sort_order: int,
    product_type: str,
) -> sa.TextClause:
    return sa.text(
        """
        INSERT INTO plans (
            slug, name, description, duration_days, price_rub,
            device_limit, is_active, sort_order, product_type
        )
        SELECT
            :slug, :name, :description, 30, :price,
            :device_limit, true, :sort_order, :product_type
        WHERE NOT EXISTS (SELECT 1 FROM plans WHERE slug = :slug)
        """
    ).bindparams(
        slug=slug,
        name=name,
        description=desc,
        price=price,
        device_limit=device_limit,
        sort_order=sort_order,
        product_type=product_type,
    )


def _plan_update_params(
    slug: str,
    name: str,
    desc: str,
    price: int,
    device_limit: int,
    sort_order: int,
    product_type: str,
) -> sa.TextClause:
    return sa.text(
        """
        UPDATE plans SET
            name = :name,
            description = :description,
            price_rub = :price,
            device_limit = :device_limit,
            sort_order = :sort_order,
            product_type = :product_type,
            is_active = true
        WHERE slug = :slug
        """
    ).bindparams(
        slug=slug,
        name=name,
        description=desc,
        price=price,
        device_limit=device_limit,
        sort_order=sort_order,
        product_type=product_type,
    )


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE plans SET is_active = false WHERE slug IN "
            "('start', 'standard', 'family', 'ai_plus')"
        )
    )
    for slug, name, desc, price, device_limit, sort_order, product_type in NEW_PLANS:
        op.execute(_plan_params(slug, name, desc, price, device_limit, sort_order, product_type))
        op.execute(
            _plan_update_params(slug, name, desc, price, device_limit, sort_order, product_type)
        )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE plans SET is_active = false WHERE slug IN "
            "('combo_max', 'combo', 'connect_plus', 'connect', 'lite_ai')"
        )
    )
    op.execute(
        sa.text(
            "UPDATE plans SET is_active = true WHERE slug IN "
            "('start', 'standard', 'family', 'ai_plus')"
        )
    )
