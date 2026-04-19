"""Widen orders.invoice_url to TEXT (presigned S3 URLs exceed 500 chars)

Revision ID: 004
Revises: 003
Create Date: 2026-04-19
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "orders",
        "invoice_url",
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "orders",
        "invoice_url",
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
