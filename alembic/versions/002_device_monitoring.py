"""device monitoring fields

Revision ID: 002
Revises: 001
Create Date: 2026-06-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("devices", sa.Column("device_id", sa.String(length=64), nullable=True))
    op.add_column(
        "devices",
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
    )
    op.add_column("devices", sa.Column("last_ip", sa.String(length=45), nullable=True))
    op.add_column("devices", sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True))
    op.add_column("devices", sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("devices", sa.Column("suspended_reason", sa.String(length=255), nullable=True))

    op.execute(
        """
        UPDATE devices
        SET device_id = md5(uuid || ':' || device_slug || ':' || user_id::text),
            status = 'active'
        WHERE device_id IS NULL
        """
    )
    op.alter_column("devices", "device_id", nullable=False)
    op.create_index("ix_devices_device_id", "devices", ["device_id"], unique=True)
    op.create_index("ix_devices_status", "devices", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_devices_status", table_name="devices")
    op.drop_index("ix_devices_device_id", table_name="devices")
    op.drop_column("devices", "suspended_reason")
    op.drop_column("devices", "suspended_at")
    op.drop_column("devices", "last_seen")
    op.drop_column("devices", "last_ip")
    op.drop_column("devices", "status")
    op.drop_column("devices", "device_id")
