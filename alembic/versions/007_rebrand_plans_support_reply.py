"""Rebrand plan copy, support admin replies

Revision ID: 007
Revises: 006
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PLAN_UPDATES = [
    ("connect", "Личный", "1 устройство · личная подписка · защищённый канал", 1),
    ("connect_plus", "Команда", "до 3 устройств · удалённая работа команды", 3),
    ("combo", "Бизнес", "до 5 устройств · команда + AI-помощник", 5),
    ("combo_max", "Семья", "до 10 устройств · семья и расширенная команда + AI", 10),
    ("lite_ai", "AI Помощник", "AI-помощник в Telegram без лимита", 0),
]


def upgrade() -> None:
    op.add_column("support_tickets", sa.Column("admin_reply", sa.Text(), nullable=True))
    op.add_column(
        "support_tickets",
        sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("support_tickets", "telegram_id", existing_type=sa.BigInteger(), nullable=True)

    op.drop_constraint("ck_plans_device_limit", "plans", type_="check")
    op.drop_constraint("ck_subscriptions_device_limit", "subscriptions", type_="check")
    op.create_check_constraint(
        "ck_plans_device_limit",
        "plans",
        "device_limit BETWEEN 0 AND 20",
    )
    op.create_check_constraint(
        "ck_subscriptions_device_limit",
        "subscriptions",
        "device_limit BETWEEN 0 AND 20",
    )

    bind = op.get_bind()
    for slug, name, description, device_limit in PLAN_UPDATES:
        bind.execute(
            sa.text(
                "UPDATE plans SET name = :name, description = :description, "
                "device_limit = :device_limit WHERE slug = :slug"
            ),
            {"slug": slug, "name": name, "description": description, "device_limit": device_limit},
        )


def downgrade() -> None:
    bind = op.get_bind()
    for slug, _, _, device_limit in PLAN_UPDATES:
        if device_limit <= 3:
            bind.execute(
                sa.text("UPDATE plans SET device_limit = :device_limit WHERE slug = :slug"),
                {"slug": slug, "device_limit": min(device_limit, 3)},
            )
    bind.execute(
        sa.text("UPDATE plans SET device_limit = 1 WHERE slug IN ('combo', 'combo_max')")
    )

    op.drop_constraint("ck_subscriptions_device_limit", "subscriptions", type_="check")
    op.drop_constraint("ck_plans_device_limit", "plans", type_="check")
    op.create_check_constraint(
        "ck_plans_device_limit",
        "plans",
        "device_limit BETWEEN 0 AND 3",
    )
    op.create_check_constraint(
        "ck_subscriptions_device_limit",
        "subscriptions",
        "device_limit BETWEEN 0 AND 3",
    )

    op.alter_column("support_tickets", "telegram_id", existing_type=sa.BigInteger(), nullable=False)
    op.drop_column("support_tickets", "replied_at")
    op.drop_column("support_tickets", "admin_reply")
