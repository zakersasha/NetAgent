"""Align lt1 Reality short_id with entry Xray config (fc2 not fc3)

Revision ID: 015
Revises: 014
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENTRY_SHORT_ID = "6ba85179e30d4fc2"
OLD_LT1_SHORT_ID = "6ba85179e30d4fc3"


def upgrade() -> None:
    op.get_bind().execute(
        sa.text(
            """
            UPDATE vpn_nodes SET
                reality_short_id = :entry_short_id
            WHERE slug = 'lt1'
              AND reality_short_id = :old_short_id
            """
        ),
        {"entry_short_id": ENTRY_SHORT_ID, "old_short_id": OLD_LT1_SHORT_ID},
    )


def downgrade() -> None:
    op.get_bind().execute(
        sa.text(
            """
            UPDATE vpn_nodes SET
                reality_short_id = :old_short_id
            WHERE slug = 'lt1'
              AND reality_short_id = :entry_short_id
            """
        ),
        {"entry_short_id": ENTRY_SHORT_ID, "old_short_id": OLD_LT1_SHORT_ID},
    )
