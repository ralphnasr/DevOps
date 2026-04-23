"""Add email suppression columns to customers (for SES bounce auto-suppression)

Revision ID: 005
Revises: 004
Create Date: 2026-04-22
"""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column(
            "email_suppressed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column(
        "customers",
        sa.Column("suppressed_reason", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "customers",
        sa.Column("suppressed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "idx_customers_email",
        "customers",
        ["email"],
    )


def downgrade() -> None:
    op.drop_index("idx_customers_email", table_name="customers")
    op.drop_column("customers", "suppressed_at")
    op.drop_column("customers", "suppressed_reason")
    op.drop_column("customers", "email_suppressed")
