from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Pagination ──


class PaginatedResponse(BaseModel):
    items: list[Any] = []
    total: int = 0
    page: int = 1
    per_page: int = 20
    pages: int = 0


# ── Category ──


class CategoryOut(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


# ── Product ──


class ProductOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: float
    category_id: int | None = None
    category: CategoryOut | None = None
    image_url: str | None = None
    images: list[str] = []
    attributes: dict = {}
    stock_quantity: int = 0
    is_active: bool = True
    avg_rating: float = 0
    review_count: int = 0
    sales_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ProductList(PaginatedResponse):
    items: list[ProductOut] = []


# ── Cart ──


class CartItem(BaseModel):
    product_id: int
    name: str = ""
    price: float = 0
    quantity: int = 1


class CartResponse(BaseModel):
    items: list[CartItem] = []
    updated_at: str | None = None


class AddToCartRequest(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)


class UpdateCartRequest(BaseModel):
    quantity: int = Field(ge=0)


# ── Checkout / Orders ──


class CheckoutRequest(BaseModel):
    coupon_code: str | None = None


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    customer_id: int
    status: str
    subtotal: float = 0
    discount_amount: float = 0
    coupon_code: str | None = None
    total_amount: float
    invoice_url: str | None = None
    items: list[OrderItemOut] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class OrderList(PaginatedResponse):
    items: list[OrderOut] = []


class CheckoutResponse(BaseModel):
    order_id: int
    status: str
    subtotal: float = 0
    discount_amount: float = 0
    total_amount: float
    coupon_code: str | None = None
    message: str = "Order confirmed"


class CouponValidateRequest(BaseModel):
    code: str
    cart_total: float = Field(ge=0)


class CouponValidateResponse(BaseModel):
    valid: bool
    code: str | None = None
    discount_amount: float = 0
    new_total: float = 0
    message: str = ""


class ReorderResponse(BaseModel):
    items_added: int
    items_skipped: int
    cart_item_count: int
    message: str = "Items added to cart"


# ── Admin ──


class AdminProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float = Field(ge=0)
    category_id: int | None = None
    image_url: str | None = None
    attributes: dict = {}
    stock_quantity: int = Field(default=0, ge=0)


class AdminProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    category_id: int | None = None
    image_url: str | None = None
    attributes: dict | None = None
    stock_quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class AdminInventoryUpdate(BaseModel):
    stock_quantity: int = Field(ge=0)


class AdminOrderStatusUpdate(BaseModel):
    status: str


# ── Health ──


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = ""


# ── Dashboard ──


class DashboardStats(BaseModel):
    total_orders: int = 0
    total_revenue: float = 0
    total_products: int = 0
    low_stock_count: int = 0


# ── Coupons (admin) ──


class AdminCouponCreate(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    description: str | None = None
    discount_type: str = Field(pattern="^(percent|fixed)$")
    discount_value: float = Field(gt=0)
    min_order_amount: float = Field(default=0, ge=0)
    max_uses: int | None = Field(default=None, ge=1)
    valid_until: datetime | None = None
    is_active: bool = True


class AdminCouponUpdate(BaseModel):
    description: str | None = None
    discount_value: float | None = Field(default=None, gt=0)
    min_order_amount: float | None = Field(default=None, ge=0)
    max_uses: int | None = Field(default=None, ge=1)
    valid_until: datetime | None = None
    is_active: bool | None = None


class CouponOut(BaseModel):
    id: int
    code: str
    description: str | None = None
    discount_type: str
    discount_value: float
    min_order_amount: float = 0
    max_uses: int | None = None
    times_used: int = 0
    valid_until: datetime | None = None
    is_active: bool = True
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Reviews ──


class ReviewOut(BaseModel):
    id: int
    product_id: int
    author_name: str
    rating: int
    title: str | None = None
    body: str | None = None
    verified_purchase: bool = False
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    title: str | None = Field(default=None, max_length=255)
    body: str | None = Field(default=None, max_length=2000)
    author_name: str | None = Field(default=None, max_length=120)


class ReviewSummary(BaseModel):
    avg_rating: float = 0
    review_count: int = 0
    rating_breakdown: dict[int, int] = {}
    reviews: list[ReviewOut] = []


# ── Promotions / Testimonials ──


class PromotionOut(BaseModel):
    id: int
    slot: str
    headline: str
    subheadline: str | None = None
    cta_text: str | None = None
    cta_url: str | None = None
    image_path: str | None = None
    accent_color: str | None = None
    ends_at: datetime | None = None
    sort_order: int = 0

    model_config = {"from_attributes": True}


class TestimonialOut(BaseModel):
    id: int
    author_name: str
    author_title: str | None = None
    avatar_initials: str | None = None
    quote: str
    rating: int = 5

    model_config = {"from_attributes": True}


# ── Analytics ──


class DailyRevenuePoint(BaseModel):
    date: str
    revenue: float
    orders: int


class TopProduct(BaseModel):
    product_id: int
    name: str
    units_sold: int
    revenue: float


class StatusCount(BaseModel):
    status: str
    count: int


class AnalyticsResponse(BaseModel):
    daily_revenue: list[DailyRevenuePoint] = []
    top_products: list[TopProduct] = []
    orders_by_status: list[StatusCount] = []
    total_revenue_30d: float = 0
    total_orders_30d: int = 0
    avg_order_value: float = 0
