import json
import logging
import math

import boto3
import redis.asyncio as aioredis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shared.config import settings
from shared.coupons import calculate_discount, find_active_coupon, _is_coupon_valid
from shared.models import Coupon, Customer, Order, OrderItem, Product
from shared.redis_client import delete_cart, get_cart

logger = logging.getLogger(__name__)

# SQS client (lazy init)
_sqs_client = None


def _get_sqs():
    global _sqs_client
    if _sqs_client is None:
        _sqs_client = boto3.client("sqs", region_name=settings.aws_region)
    return _sqs_client


async def _get_or_create_customer(
    db: AsyncSession, cognito_sub: str, email: str
) -> Customer:
    result = await db.execute(
        select(Customer).where(Customer.cognito_sub == cognito_sub)
    )
    customer = result.scalars().first()
    if customer:
        return customer

    customer = Customer(cognito_sub=cognito_sub, email=email)
    db.add(customer)
    await db.flush()
    return customer


def publish_invoice_message(message: dict) -> None:
    """
    Background-task entrypoint: pushes the invoice job onto SQS *after* the
    /api/checkout HTTP response has already been sent. This is the seam that
    makes invoice generation truly fire-and-forget from the client's POV —
    the customer gets \"Order Confirmed!\" the instant the DB commit lands;
    the SQS round-trip + Lambda + S3 + SES all happen in the background.

    Runs in FastAPI's threadpool (BackgroundTasks executes sync funcs there),
    so the blocking boto3 call doesn't pin the asyncio event loop.

    Hard-fail in prod if SQS isn't configured: the order is already committed
    to RDS, so a missing queue URL means an order with no invoice. Better a
    loud server-side log + raise than a silent gap. Failure here cannot leak
    back to the customer (response already sent), so RDS is the source of
    truth and we rely on logs/CloudWatch alerts to surface drops.
    """
    if settings.sqs_queue_url:
        _get_sqs().send_message(
            QueueUrl=settings.sqs_queue_url,
            MessageBody=json.dumps(message),
        )
        logger.info(f"Published order {message['order_id']} to SQS (background)")
    elif settings.environment == "prod":
        logger.error(
            f"SQS_QUEUE_URL empty in prod — order {message['order_id']} "
            "saved but invoice pipeline cannot be notified"
        )
        raise RuntimeError("SQS_QUEUE_URL empty in prod")
    else:
        logger.info(f"[LOCAL] Would publish to SQS: order_id={message['order_id']}")


async def process_checkout(
    db: AsyncSession,
    r: aioredis.Redis,
    cognito_sub: str,
    email: str,
    coupon_code: str | None = None,
) -> tuple[dict, dict]:
    # 1. Read cart
    cart = await get_cart(r, cognito_sub)
    if not cart["items"]:
        raise ValueError("Cart is empty")

    # 2. Validate stock for each item (SELECT FOR UPDATE)
    subtotal = 0
    validated_items = []

    for cart_item in cart["items"]:
        result = await db.execute(
            select(Product)
            .where(Product.id == cart_item["product_id"])
            .with_for_update()
        )
        product = result.scalars().first()

        if not product or not product.is_active:
            raise ValueError(f"Product '{cart_item['name']}' is no longer available")

        if product.stock_quantity < cart_item["quantity"]:
            raise ValueError(
                f"Product '{product.name}' has only {product.stock_quantity} units in stock, "
                f"requested {cart_item['quantity']}"
            )

        item_total = float(product.price) * cart_item["quantity"]
        subtotal += item_total
        validated_items.append(
            {
                "product": product,
                "quantity": cart_item["quantity"],
                "unit_price": float(product.price),
                "product_name": product.name,
            }
        )

    subtotal = round(subtotal, 2)

    # 3. Apply coupon if provided
    discount_amount = 0.0
    applied_code: str | None = None
    coupon_row: Coupon | None = None
    if coupon_code:
        coupon_row = await find_active_coupon(db, coupon_code)
        if not coupon_row:
            raise ValueError(f"Invalid coupon code: {coupon_code}")
        ok, reason = _is_coupon_valid(coupon_row, subtotal)
        if not ok:
            raise ValueError(reason)
        discount_amount = calculate_discount(coupon_row, subtotal)
        applied_code = coupon_row.code

    total_amount = round(subtotal - discount_amount, 2)

    # 4. Get or create customer
    customer = await _get_or_create_customer(db, cognito_sub, email)
    email_suppressed = bool(getattr(customer, "email_suppressed", False))

    # 5. Create order
    order = Order(
        customer_id=customer.id,
        status="confirmed",
        subtotal=subtotal,
        discount_amount=discount_amount,
        coupon_code=applied_code,
        total_amount=total_amount,
    )
    db.add(order)
    await db.flush()

    # 6. Create order items + decrement stock
    for item_data in validated_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product"].id,
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
        )
        db.add(order_item)
        item_data["product"].stock_quantity -= item_data["quantity"]

    # 7. Increment coupon usage
    if coupon_row is not None:
        coupon_row.times_used = (coupon_row.times_used or 0) + 1

    await db.commit()

    # 8. Build the SQS message — but DON'T publish it here. The router will
    #    schedule publish_invoice_message() as a FastAPI BackgroundTask so it
    #    runs *after* the HTTP response is sent. This is what makes invoice
    #    generation asynchronous from the customer's POV: \"Order Confirmed!\"
    #    appears the instant cart-delete returns; the SQS roundtrip + Lambda +
    #    S3 + SES all happen out of band.
    sqs_message = {
        "order_id": order.id,
        "customer_id": customer.id,
        "customer_email": email,
        "suppressed": email_suppressed,
        "items": [
            {
                "product_name": item["product_name"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
            }
            for item in validated_items
        ],
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "coupon_code": applied_code,
        "total_amount": float(order.total_amount),
        "created_at": order.created_at.isoformat() if order.created_at else "",
    }

    # 9. Clear cart (sync — user must see empty cart in the very next response)
    await delete_cart(r, cognito_sub)

    response = {
        "order_id": order.id,
        "status": order.status,
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "coupon_code": applied_code,
        "total_amount": float(order.total_amount),
        "message": (
            "Order confirmed — your invoice is being generated. "
            "Download it from your order confirmation page."
            if email_suppressed
            else "Order confirmed — your invoice is being generated and will arrive by email shortly."
        ),
    }
    return response, sqs_message


async def reorder(
    db: AsyncSession,
    r: aioredis.Redis,
    cognito_sub: str,
    order_id: int,
) -> dict:
    from shared.redis_client import set_cart

    customer_result = await db.execute(
        select(Customer).where(Customer.cognito_sub == cognito_sub)
    )
    customer = customer_result.scalars().first()
    if not customer:
        raise ValueError("Customer not found")

    order_result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.customer_id == customer.id)
        .options(joinedload(Order.items))
    )
    order = order_result.unique().scalars().first()
    if not order:
        raise ValueError("Order not found")

    cart = await get_cart(r, cognito_sub)
    existing_ids = {item["product_id"] for item in cart["items"]}

    items_added = 0
    items_skipped = 0

    for order_item in order.items:
        prod_result = await db.execute(
            select(Product).where(
                Product.id == order_item.product_id,
                Product.is_active,
            )
        )
        product = prod_result.scalars().first()
        if not product or product.stock_quantity < order_item.quantity:
            items_skipped += 1
            continue

        if order_item.product_id in existing_ids:
            for ci in cart["items"]:
                if ci["product_id"] == order_item.product_id:
                    ci["quantity"] += order_item.quantity
                    break
        else:
            cart["items"].append(
                {
                    "product_id": order_item.product_id,
                    "name": product.name,
                    "price": float(product.price),
                    "quantity": order_item.quantity,
                }
            )
            existing_ids.add(order_item.product_id)

        items_added += 1

    await set_cart(r, cognito_sub, cart)

    return {
        "items_added": items_added,
        "items_skipped": items_skipped,
        "cart_item_count": len(cart["items"]),
        "message": (
            f"Added {items_added} item(s) to your cart"
            if items_added
            else "No items could be re-added (out of stock or unavailable)"
        ),
    }


async def list_orders(
    db: AsyncSession,
    cognito_sub: str,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    # Get customer
    result = await db.execute(
        select(Customer).where(Customer.cognito_sub == cognito_sub)
    )
    customer = result.scalars().first()
    if not customer:
        return {"items": [], "total": 0, "page": page, "per_page": per_page, "pages": 0}

    # Count
    count_q = select(func.count()).select_from(
        select(Order.id).where(Order.customer_id == customer.id)
    )
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch
    query = (
        select(Order)
        .where(Order.customer_id == customer.id)
        .options(joinedload(Order.items))
        .order_by(Order.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    orders = result.unique().scalars().all()

    return {
        "items": orders,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page > 0 else 0,
    }


async def get_order(db: AsyncSession, cognito_sub: str, order_id: int) -> Order | None:
    result = await db.execute(
        select(Customer).where(Customer.cognito_sub == cognito_sub)
    )
    customer = result.scalars().first()
    if not customer:
        return None

    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.customer_id == customer.id)
        .options(joinedload(Order.items))
    )
    return result.unique().scalars().first()


async def cancel_order(db: AsyncSession, cognito_sub: str, order_id: int) -> Order:
    result = await db.execute(
        select(Customer).where(Customer.cognito_sub == cognito_sub)
    )
    customer = result.scalars().first()
    if not customer:
        raise ValueError("Customer not found")

    # Lock the order row
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.customer_id == customer.id)
        .with_for_update()
    )
    order = result.scalars().first()
    if not order:
        raise ValueError("Order not found")

    if order.status != "confirmed":
        raise ValueError(f"Cannot cancel order with status '{order.status}'")

    # Load items separately
    result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    items = result.scalars().all()

    # Restore stock for each item
    for item in items:
        prod_result = await db.execute(
            select(Product).where(Product.id == item.product_id).with_for_update()
        )
        product = prod_result.scalars().first()
        if product:
            product.stock_quantity += item.quantity

    order.status = "cancelled"
    await db.commit()

    # Reload with items for response
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(joinedload(Order.items))
    )
    order = result.unique().scalars().first()

    logger.info(f"Order {order_id} cancelled, stock restored")
    return order
