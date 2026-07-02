"""Rename combo plan to Стандарт

Revision ID: 009
Revises: 008
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.get_bind().execute(
        sa.text(
            """
            UPDATE plans SET
                name = 'Стандарт',
                description = 'до 3 устройств · канал и AI-помощник'
            WHERE slug = 'combo'
            """
        )
    )


def downgrade() -> None:
    op.get_bind().execute(
        sa.text(
            """
            UPDATE plans SET
                name = 'Команда + AI',
                description = 'до 3 устройств · канал и AI-помощник'
            WHERE slug = 'combo'
            """
        )
    )
