"""Initial schema - all tables, indexes, triggers

Revision ID: 001
Revises:
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Categories ──
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── Products ──
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="SET NULL")),
        sa.Column("image_url", sa.String(500)),
        sa.Column("attributes", postgresql.JSONB(), server_default="{}"),
        sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("search_vector", postgresql.TSVECTOR()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("price >= 0", name="ck_products_price_positive"),
        sa.CheckConstraint("stock_quantity >= 0", name="ck_products_stock_positive"),
    )
    op.create_index("idx_products_search", "products", ["search_vector"], postgresql_using="gin")
    op.create_index("idx_products_category", "products", ["category_id"])
    op.create_index(
        "idx_products_active",
        "products",
        ["is_active"],
        postgresql_where=sa.text("is_active = true"),
    )

    # Full-text search trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION update_product_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english',
                COALESCE(NEW.name, '') || ' ' || COALESCE(NEW.description, '')
            );
            NEW.updated_at := NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_product_search_update
            BEFORE INSERT OR UPDATE ON products
            FOR EACH ROW EXECUTE FUNCTION update_product_search_vector();
    """)

    # ── Customers ──
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cognito_sub", sa.String(255), unique=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_customers_cognito", "customers", ["cognito_sub"])

    # ── Orders ──
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="confirmed"),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("invoice_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "status IN ('confirmed', 'processing', 'shipped', 'delivered', 'cancelled')",
            name="ck_orders_status_valid",
        ),
        sa.CheckConstraint("total_amount >= 0", name="ck_orders_total_positive"),
    )
    op.create_index("idx_orders_customer", "orders", ["customer_id"])
    op.create_index("idx_orders_status", "orders", ["status"])

    # ── Order Items ──
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_order_items_price_positive"),
    )
    op.create_index("idx_order_items_order", "order_items", ["order_id"])


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_product_search_update ON products")
    op.execute("DROP FUNCTION IF EXISTS update_product_search_vector()")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("customers")
    op.drop_table("products")
    op.drop_table("categories")
