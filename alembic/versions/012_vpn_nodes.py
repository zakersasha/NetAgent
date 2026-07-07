"""VPN nodes and device assignment

Revision ID: 012
Revises: 011
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vpn_nodes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("public_host", sa.String(length=255), nullable=False),
        sa.Column("public_port", sa.Integer(), nullable=False, server_default="443"),
        sa.Column("agent_url", sa.String(length=512), nullable=False),
        sa.Column("reality_public_key", sa.String(length=255), nullable=False),
        sa.Column("reality_short_id", sa.String(length=32), nullable=False),
        sa.Column("reality_sni", sa.String(length=255), nullable=False, server_default="www.wikipedia.org"),
        sa.Column("max_users", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.add_column("devices", sa.Column("vpn_node_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_devices_vpn_node_id",
        "devices",
        "vpn_nodes",
        ["vpn_node_id"],
        ["id"],
    )
    op.create_index("ix_devices_vpn_node_id", "devices", ["vpn_node_id"])

    op.get_bind().execute(
        sa.text(
            """
            INSERT INTO vpn_nodes (
                slug, name, public_host, public_port, agent_url,
                reality_public_key, reality_short_id, reality_sni,
                max_users, is_active, sort_order
            ) VALUES (
                'lt1',
                'Литва #1',
                '45.93.137.80',
                443,
                'https://45.93.137.80:8443',
                'YTQ_dIa_739_d6x7OUAd3XjMbpX6UOnWBMkGVtEhi18',
                '6ba85179e30d4fc3',
                'www.wikipedia.org',
                50,
                true,
                1
            )
            ON CONFLICT (slug) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_devices_vpn_node_id", table_name="devices")
    op.drop_constraint("fk_devices_vpn_node_id", "devices", type_="foreignkey")
    op.drop_column("devices", "vpn_node_id")
    op.drop_table("vpn_nodes")
