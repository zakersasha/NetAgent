"""Adjust plan device tiers and prices

Revision ID: 008
Revises: 007
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PLAN_UPDATES = [
    # slug, name, description, price, device_limit, traffic_gb, product_type, sort_order
    ("connect", "Личный", "1 устройство · личная подписка", 149, 1, 40, "vpn", 4),
    ("connect_plus", "Команда", "до 3 устройств · малая команда", 249, 3, 80, "vpn", 3),
    ("combo", "Команда + AI", "до 3 устройств · канал и AI-помощник", 279, 3, 80, "bundle", 2),
    ("combo_max", "Семья", "до 5 устройств · семья + AI-помощник", 399, 5, 150, "bundle", 1),
    ("lite_ai", "AI Помощник", "AI-помощник в Telegram без лимита", 99, 0, None, "ai", 5),
]


def upgrade() -> None:
    bind = op.get_bind()
    for slug, name, desc, price, devices, traffic, ptype, sort_order in PLAN_UPDATES:
        bind.execute(
            sa.text(
                """
                UPDATE plans SET
                    name = :name,
                    description = :description,
                    price_rub = :price,
                    device_limit = :devices,
                    traffic_limit_gb = :traffic,
                    product_type = :ptype,
                    sort_order = :sort_order
                WHERE slug = :slug
                """
            ),
            {
                "slug": slug,
                "name": name,
                "description": desc,
                "price": price,
                "devices": devices,
                "traffic": traffic,
                "ptype": ptype,
                "sort_order": sort_order,
            },
        )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE plans SET name = 'Личный', description = '1 устройство · личная подписка · защищённый канал',
                price_rub = 179, device_limit = 1, traffic_limit_gb = 50, product_type = 'vpn', sort_order = 4
            WHERE slug = 'connect'
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE plans SET name = 'Команда', description = 'до 3 устройств · удалённая работа команды',
                price_rub = 279, device_limit = 3, traffic_limit_gb = 100, product_type = 'vpn', sort_order = 3
            WHERE slug = 'connect_plus'
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE plans SET name = 'Бизнес', description = 'до 5 устройств · команда + AI-помощник',
                price_rub = 299, device_limit = 5, traffic_limit_gb = 80, product_type = 'bundle', sort_order = 2
            WHERE slug = 'combo'
            """
        )
    )
    bind.execute(
        sa.text(
            """
            UPDATE plans SET name = 'Семья', description = 'до 10 устройств · семья и расширенная команда + AI',
                price_rub = 449, device_limit = 10, traffic_limit_gb = 200, product_type = 'bundle', sort_order = 1
            WHERE slug = 'combo_max'
            """
        )
    )
