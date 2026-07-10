"""Fix Reality public key for Yandex entry relay nodes

Revision ID: 014
Revises: 013
"""

import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENTRY_HOST = "51.250.112.128"
# pbk outbound Литвы из seed 012 — в ссылках entry его быть не должно
LITHUANIA_EXIT_PBK = "YTQ_dIa_739_d6x7OUAd3XjMbpX6UOnWBMkGVtEhi18"
DEFAULT_ENTRY_PBK = "j-iuguAzBEJ4-u76nVncqDxBipKnsPgGkBOunpoYBXA"


def upgrade() -> None:
    pbk = os.environ.get("REALITY_PUBLIC_KEY", "").strip() or DEFAULT_ENTRY_PBK
    bind = op.get_bind()

    bind.execute(
        sa.text(
            """
            UPDATE vpn_nodes SET
                reality_public_key = :pbk,
                public_host = :entry_host,
                public_port = CASE slug WHEN 'fi1' THEN 2096 ELSE 2053 END
            WHERE agent_url LIKE :host_pattern
               OR reality_public_key = :lithuania_pbk
            """
        ),
        {
            "pbk": pbk,
            "entry_host": ENTRY_HOST,
            "host_pattern": f"%{ENTRY_HOST}%",
            "lithuania_pbk": LITHUANIA_EXIT_PBK,
        },
    )


def downgrade() -> None:
    pass
