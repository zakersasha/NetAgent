"""Payment audit fields and webhook log

Revision ID: 011
Revises: 010
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("source", sa.String(length=20), nullable=True))
    op.add_column("payments", sa.Column("description", sa.String(length=255), nullable=True))
    op.add_column("payments", sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("payments", sa.Column("payment_method_type", sa.String(length=50), nullable=True))
    op.add_column("payments", sa.Column("payment_method_title", sa.String(length=255), nullable=True))
    op.add_column(
        "payments",
        sa.Column("receipt_fiscal_document_number", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("receipt_fiscal_storage_number", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("receipt_fiscal_attribute", sa.String(length=64), nullable=True),
    )
    op.add_column("payments", sa.Column("receipt_registered_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("payments", sa.Column("provider_payload", sa.Text(), nullable=True))

    op.create_table(
        "payment_webhook_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("payment_id", sa.BigInteger(), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_payment_webhook_events_payment_id",
        "payment_webhook_events",
        ["payment_id"],
    )
    op.create_index(
        "ix_payment_webhook_events_external_id",
        "payment_webhook_events",
        ["external_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_payment_webhook_events_external_id", table_name="payment_webhook_events")
    op.drop_index("ix_payment_webhook_events_payment_id", table_name="payment_webhook_events")
    op.drop_table("payment_webhook_events")
    op.drop_column("payments", "provider_payload")
    op.drop_column("payments", "receipt_registered_at")
    op.drop_column("payments", "receipt_fiscal_attribute")
    op.drop_column("payments", "receipt_fiscal_storage_number")
    op.drop_column("payments", "receipt_fiscal_document_number")
    op.drop_column("payments", "payment_method_title")
    op.drop_column("payments", "payment_method_type")
    op.drop_column("payments", "paid_at")
    op.drop_column("payments", "description")
    op.drop_column("payments", "source")
