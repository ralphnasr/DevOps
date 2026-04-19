"""Add coupons, audit logs, and order discount fields

Revision ID: 002
Revises: 001
Create Date: 2026-04-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Coupons ──
    op.create_table(
        "coupons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("description", sa.String(255)),
        sa.Column("discount_type", sa.String(20), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("min_order_amount", sa.Numeric(10, 2), server_default="0"),
        sa.Column("max_uses", sa.Integer()),
        sa.Column("times_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "discount_type IN ('percent', 'fixed')",
            name="ck_coupons_discount_type_valid",
        ),
        sa.CheckConstraint(
            "discount_value > 0", name="ck_coupons_discount_value_positive"
        ),
    )
    op.create_index("idx_coupons_code", "coupons", ["code"])
    op.create_index("idx_coupons_active", "coupons", ["is_active"])

    # ── Audit Logs ──
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(50)),
        sa.Column("details", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_audit_logs_actor", "audit_logs", ["actor"])
    op.create_index("idx_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("idx_audit_logs_created", "audit_logs", ["created_at"])

    # ── Order discount fields ──
    op.add_column(
        "orders", sa.Column("subtotal", sa.Numeric(10, 2), server_default="0")
    )
    op.add_column(
        "orders", sa.Column("discount_amount", sa.Numeric(10, 2), server_default="0")
    )
    op.add_column("orders", sa.Column("coupon_code", sa.String(50)))


def downgrade() -> None:
    op.drop_column("orders", "coupon_code")
    op.drop_column("orders", "discount_amount")
    op.drop_column("orders", "subtotal")
    op.drop_index("idx_audit_logs_created", table_name="audit_logs")
    op.drop_index("idx_audit_logs_entity", table_name="audit_logs")
    op.drop_index("idx_audit_logs_actor", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("idx_coupons_active", table_name="coupons")
    op.drop_index("idx_coupons_code", table_name="coupons")
    op.drop_table("coupons")
