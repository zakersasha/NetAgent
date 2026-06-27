"""ai chat usage and plan product type

Revision ID: 003
Revises: 002
Create Date: 2026-06-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ck_plans_device_limit", "plans", type_="check")
    op.drop_constraint("ck_subscriptions_device_limit", "subscriptions", type_="check")

    op.add_column(
        "plans",
        sa.Column("product_type", sa.String(length=20), server_default="vpn", nullable=False),
    )
    op.execute(sa.text("UPDATE plans SET product_type = 'vpn'"))

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

    op.create_table(
        "ai_daily_usage",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("message_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "usage_date", name="uq_ai_daily_usage_user_date"),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO plans (
                slug, name, description, duration_days, price_rub,
                device_limit, is_active, sort_order, product_type
            )
            SELECT
                'ai_plus', 'AI Plus', 'Безлимитный чат с AI', 30, 199,
                0, true, 10, 'ai'
            WHERE NOT EXISTS (SELECT 1 FROM plans WHERE slug = 'ai_plus')
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM plans WHERE slug = 'ai_plus'"))
    op.drop_table("ai_daily_usage")
    op.drop_constraint("ck_subscriptions_device_limit", "subscriptions", type_="check")
    op.drop_constraint("ck_plans_device_limit", "plans", type_="check")
    op.drop_column("plans", "product_type")
    op.create_check_constraint(
        "ck_plans_device_limit",
        "plans",
        "device_limit BETWEEN 1 AND 3",
    )
    op.create_check_constraint(
        "ck_subscriptions_device_limit",
        "subscriptions",
        "device_limit BETWEEN 1 AND 3",
    )
