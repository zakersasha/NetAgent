"""Traffic limits and single-key subscriptions

Revision ID: 006
Revises: 005
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PLAN_TRAFFIC = [
    ("connect", 50, "Стабильное подключение · 50 ГБ/мес"),
    ("connect_plus", 100, "Стабильное подключение · 100 ГБ/мес"),
    ("combo", 80, "Подключение 80 ГБ + AI без лимита"),
    ("combo_max", 200, "Подключение 200 ГБ + AI без лимита · для семьи"),
]


def upgrade() -> None:
    op.add_column("plans", sa.Column("traffic_limit_gb", sa.Integer(), nullable=True))
    op.add_column(
        "subscriptions",
        sa.Column("traffic_used_bytes", sa.BigInteger(), server_default="0", nullable=False),
    )
    op.add_column(
        "subscriptions",
        sa.Column(
            "traffic_xray_snapshot_bytes",
            sa.BigInteger(),
            server_default="0",
            nullable=False,
        ),
    )

    for slug, gb, desc in PLAN_TRAFFIC:
        op.execute(
            sa.text(
                "UPDATE plans SET traffic_limit_gb = :gb, device_limit = 1, description = :desc "
                "WHERE slug = :slug"
            ).bindparams(gb=gb, desc=desc, slug=slug)
        )


def downgrade() -> None:
    op.drop_column("subscriptions", "traffic_xray_snapshot_bytes")
    op.drop_column("subscriptions", "traffic_used_bytes")
    op.drop_column("plans", "traffic_limit_gb")
