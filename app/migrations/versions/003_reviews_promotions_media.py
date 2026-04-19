"""Add reviews, promotions, testimonials, and product media/rating columns

Revision ID: 003
Revises: 002
Create Date: 2026-04-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Product gallery + rating + sales counters ──
    op.add_column(
        "products", sa.Column("images", postgresql.JSONB(), server_default="[]")
    )
    op.add_column(
        "products", sa.Column("avg_rating", sa.Numeric(3, 2), server_default="0")
    )
    op.add_column(
        "products",
        sa.Column("review_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "products",
        sa.Column("sales_count", sa.Integer(), server_default="0", nullable=False),
    )

    # ── Reviews ──
    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id")),
        sa.Column("author_name", sa.String(120), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255)),
        sa.Column("body", sa.Text()),
        sa.Column(
            "verified_purchase",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"
        ),
    )
    op.create_index("idx_reviews_product", "reviews", ["product_id"])
    op.create_index("idx_reviews_created", "reviews", ["created_at"])

    # ── Promotions (hero slides, seasonal banners, flash sales) ──
    op.create_table(
        "promotions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slot", sa.String(50), nullable=False),
        sa.Column("headline", sa.String(255), nullable=False),
        sa.Column("subheadline", sa.String(500)),
        sa.Column("cta_text", sa.String(100)),
        sa.Column("cta_url", sa.String(500)),
        sa.Column("image_path", sa.String(500)),
        sa.Column("accent_color", sa.String(20)),
        sa.Column("starts_at", sa.DateTime(timezone=True)),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index("idx_promotions_slot_active", "promotions", ["slot", "is_active"])

    # ── Testimonials ──
    op.create_table(
        "testimonials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("author_name", sa.String(120), nullable=False),
        sa.Column("author_title", sa.String(120)),
        sa.Column("avatar_initials", sa.String(4)),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column("rating", sa.Integer(), server_default="5", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_testimonials_rating_range",
        ),
    )


def downgrade() -> None:
    op.drop_table("testimonials")
    op.drop_index("idx_promotions_slot_active", table_name="promotions")
    op.drop_table("promotions")
    op.drop_index("idx_reviews_created", table_name="reviews")
    op.drop_index("idx_reviews_product", table_name="reviews")
    op.drop_table("reviews")
    op.drop_column("products", "sales_count")
    op.drop_column("products", "review_count")
    op.drop_column("products", "avg_rating")
    op.drop_column("products", "images")
