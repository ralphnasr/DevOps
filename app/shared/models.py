from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    image_url = Column(String(500))
    images = Column(JSONB, server_default="[]")
    attributes = Column(JSONB, server_default="{}")
    stock_quantity = Column(Integer, nullable=False, server_default="0")
    is_active = Column(Boolean, server_default="true")
    avg_rating = Column(Numeric(3, 2), server_default="0")
    review_count = Column(Integer, server_default="0", nullable=False)
    sales_count = Column(Integer, server_default="0", nullable=False)
    search_vector = Column(TSVECTOR)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    reviews = relationship(
        "Review", back_populates="product", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_products_price_positive"),
        CheckConstraint("stock_quantity >= 0", name="ck_products_stock_positive"),
        Index("idx_products_search", "search_vector", postgresql_using="gin"),
        Index("idx_products_category", "category_id"),
        Index("idx_products_active", "is_active", postgresql_where=Column("is_active")),
    )


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    cognito_sub = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), nullable=False)
    full_name = Column(String(255))
    email_suppressed = Column(Boolean, server_default="false", nullable=False)
    suppressed_reason = Column(String(50))
    suppressed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    orders = relationship("Order", back_populates="customer")

    __table_args__ = (
        Index("idx_customers_cognito", "cognito_sub"),
        Index("idx_customers_email", "email"),
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(
        String(50),
        nullable=False,
        server_default="confirmed",
    )
    subtotal = Column(Numeric(10, 2), server_default="0")
    discount_amount = Column(Numeric(10, 2), server_default="0")
    coupon_code = Column(String(50))
    total_amount = Column(Numeric(10, 2), nullable=False)
    invoice_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    customer = relationship("Customer", back_populates="orders")
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('confirmed', 'processing', 'shipped', 'delivered', 'cancelled')",
            name="ck_orders_status_valid",
        ),
        CheckConstraint("total_amount >= 0", name="ck_orders_total_positive"),
        Index("idx_orders_customer", "customer_id"),
        Index("idx_orders_status", "status"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_price_positive"),
        Index("idx_order_items_order", "order_id"),
    )


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    discount_type = Column(String(20), nullable=False)  # 'percent' or 'fixed'
    discount_value = Column(Numeric(10, 2), nullable=False)
    min_order_amount = Column(Numeric(10, 2), server_default="0")
    max_uses = Column(Integer)
    times_used = Column(Integer, server_default="0", nullable=False)
    valid_until = Column(DateTime(timezone=True))
    is_active = Column(Boolean, server_default="true", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "discount_type IN ('percent', 'fixed')",
            name="ck_coupons_discount_type_valid",
        ),
        CheckConstraint(
            "discount_value > 0", name="ck_coupons_discount_value_positive"
        ),
        Index("idx_coupons_code", "code"),
        Index("idx_coupons_active", "is_active"),
    )


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    author_name = Column(String(120), nullable=False)
    rating = Column(Integer, nullable=False)
    title = Column(String(255))
    body = Column(Text)
    verified_purchase = Column(Boolean, server_default="false", nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product = relationship("Product", back_populates="reviews")

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
        Index("idx_reviews_product", "product_id"),
        Index("idx_reviews_created", "created_at"),
    )


class Promotion(Base):
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True)
    slot = Column(String(50), nullable=False)
    headline = Column(String(255), nullable=False)
    subheadline = Column(String(500))
    cta_text = Column(String(100))
    cta_url = Column(String(500))
    image_path = Column(String(500))
    accent_color = Column(String(20))
    starts_at = Column(DateTime(timezone=True))
    ends_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, server_default="true", nullable=False)
    sort_order = Column(Integer, server_default="0", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("idx_promotions_slot_active", "slot", "is_active"),)


class Testimonial(Base):
    __tablename__ = "testimonials"

    id = Column(Integer, primary_key=True)
    author_name = Column(String(120), nullable=False)
    author_title = Column(String(120))
    avatar_initials = Column(String(4))
    quote = Column(Text, nullable=False)
    rating = Column(Integer, server_default="5", nullable=False)
    sort_order = Column(Integer, server_default="0", nullable=False)
    is_active = Column(Boolean, server_default="true", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "rating >= 1 AND rating <= 5", name="ck_testimonials_rating_range"
        ),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    actor = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(50))
    details = Column(JSONB, server_default="{}")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_audit_logs_actor", "actor"),
        Index("idx_audit_logs_entity", "entity_type", "entity_id"),
        Index("idx_audit_logs_created", "created_at"),
    )
