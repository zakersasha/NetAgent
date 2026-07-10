"""Point vpn_nodes at Yandex entry relay (not Lithuania exit)

Revision ID: 013
Revises: 012
"""

import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENTRY_HOST = "51.250.112.128"
LT1_PORT = 2053
FI1_PORT = 2096
LT1_AGENT = f"https://{ENTRY_HOST}:8443"
FI1_AGENT = f"https://{ENTRY_HOST}:8444"
LITHUANIA_AGENT = "https://45.93.137.80:8443"


def upgrade() -> None:
    pbk = os.environ.get("REALITY_PUBLIC_KEY", "").strip()
    bind = op.get_bind()

    lt1_kwargs: dict[str, object] = {
        "public_host": ENTRY_HOST,
        "public_port": LT1_PORT,
        "agent_url": LT1_AGENT,
        "name": "Entry relay (Литва)",
    }
    if pbk:
        lt1_kwargs["reality_public_key"] = pbk

    bind.execute(
        sa.text(
            """
            UPDATE vpn_nodes SET
                public_host = :public_host,
                public_port = :public_port,
                agent_url = :agent_url,
                name = :name
                """
            + (", reality_public_key = :reality_public_key" if pbk else "")
            + """
            WHERE slug = 'lt1'
              AND agent_url = :old_agent_url
            """
        ),
        {**lt1_kwargs, "old_agent_url": LITHUANIA_AGENT},
    )

    fi1_pbk = pbk or (
        bind.execute(
            sa.text("SELECT reality_public_key FROM vpn_nodes WHERE slug = 'lt1' LIMIT 1")
        ).scalar()
        or ""
    )

    bind.execute(
        sa.text(
            """
            INSERT INTO vpn_nodes (
                slug, name, public_host, public_port, agent_url,
                reality_public_key, reality_short_id, reality_sni,
                max_users, is_active, sort_order
            ) VALUES (
                'fi1',
                'Entry relay (Exit #2)',
                :public_host,
                :public_port,
                :agent_url,
                :reality_public_key,
                '6ba85179e30d4fc2',
                'www.wikipedia.org',
                50,
                true,
                2
            )
            ON CONFLICT (slug) DO UPDATE SET
                public_host = EXCLUDED.public_host,
                public_port = EXCLUDED.public_port,
                agent_url = EXCLUDED.agent_url,
                reality_public_key = EXCLUDED.reality_public_key,
                reality_short_id = EXCLUDED.reality_short_id,
                reality_sni = EXCLUDED.reality_sni,
                name = EXCLUDED.name,
                is_active = EXCLUDED.is_active,
                sort_order = EXCLUDED.sort_order
            """
        ),
        {
            "public_host": ENTRY_HOST,
            "public_port": FI1_PORT,
            "agent_url": FI1_AGENT,
            "reality_public_key": fi1_pbk,
        },
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE vpn_nodes SET
                public_host = '45.93.137.80',
                public_port = 443,
                agent_url = :agent_url,
                name = 'Литва #1'
            WHERE slug = 'lt1'
            """
        ),
        {"agent_url": LITHUANIA_AGENT},
    )
    bind.execute(sa.text("DELETE FROM vpn_nodes WHERE slug = 'fi1'"))
