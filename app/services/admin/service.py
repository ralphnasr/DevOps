import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shared.models import (
    AuditLog,
    Category,
    Coupon,
    Order,
    OrderItem,
    Product,
)


async def get_dashboard_stats(db: AsyncSession) -> dict:
    total_orders = (await db.execute(select(func.count(Order.id)))).scalar() or 0

    # Revenue excludes cancelled orders (refunded / never fulfilled)
    total_revenue = (
        await db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.status != "cancelled"
            )
        )
    ).scalar()

    # "Active" = listed AND in stock — out-of-stock items can't be sold
    total_products = (
        await db.execute(
            select(func.count(Product.id)).where(
                Product.is_active, Product.stock_quantity > 0
            )
        )
    ).scalar() or 0

    low_stock_count = (
        await db.execute(
            select(func.count(Product.id)).where(
                Product.is_active, Product.stock_quantity < 10
            )
        )
    ).scalar() or 0

    # Recent orders for dashboard table
    recent_result = await db.execute(
        select(Order)
        .options(joinedload(Order.items))
        .order_by(Order.created_at.desc())
        .limit(10)
    )
    recent_orders = recent_result.unique().scalars().all()

    return {
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "total_products": total_products,
        "low_stock_count": low_stock_count,
        "recent_orders": recent_orders,
    }


async def list_products_admin(
    db: AsyncSession, search: str | None = None, page: int = 1, per_page: int = 20
) -> dict:
    base = select(Product).options(joinedload(Product.category))

    if search:
        base = base.where(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
            )
        )

    # Count
    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch
    query = (
        base.order_by(Product.id.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    result = await db.execute(query)
    products = result.unique().scalars().all()

    return {
        "items": products,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page > 0 else 0,
    }


async def get_product(db: AsyncSession, product_id: int) -> Product | None:
    result = await db.execute(
        select(Product)
        .options(joinedload(Product.category))
        .where(Product.id == product_id)
    )
    return result.unique().scalars().first()


async def create_product(db: AsyncSession, data: dict) -> Product:
    product = Product(**data)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def update_product(
    db: AsyncSession, product_id: int, data: dict
) -> Product | None:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        return None

    for key, value in data.items():
        if value is not None:
            setattr(product, key, value)

    await db.commit()
    await db.refresh(product)
    return product


async def deactivate_product(db: AsyncSession, product_id: int) -> bool:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        return False

    product.is_active = False
    await db.commit()
    return True


async def update_stock(
    db: AsyncSession, product_id: int, quantity: int
) -> Product | None:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        return None

    product.stock_quantity = quantity
    await db.commit()
    await db.refresh(product)
    return product


async def list_orders_admin(
    db: AsyncSession,
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    base = select(Order).options(joinedload(Order.items))

    if status:
        base = base.where(Order.status == status)

    count_q = select(func.count()).select_from(
        select(Order.id).where(Order.status == status).subquery()
        if status
        else select(Order.id).subquery()
    )
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        base.order_by(Order.created_at.desc())
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


async def update_order_status(
    db: AsyncSession, order_id: int, new_status: str
) -> Order | None:
    valid_statuses = {"confirmed", "processing", "shipped", "delivered", "cancelled"}
    if new_status not in valid_statuses:
        raise ValueError(
            f"Invalid status: {new_status}. Must be one of {valid_statuses}"
        )

    result = await db.execute(
        select(Order).where(Order.id == order_id).options(joinedload(Order.items))
    )
    order = result.unique().scalars().first()
    if not order:
        return None

    order.status = new_status
    await db.commit()
    await db.refresh(order)
    return order


async def list_categories(db: AsyncSession) -> list:
    result = await db.execute(select(Category).order_by(Category.name))
    return result.scalars().all()


# ── Audit Log ──


async def log_audit(
    db: AsyncSession,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str | int | None = None,
    details: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            details=details or {},
        )
    )
    await db.commit()


async def list_audit_logs(
    db: AsyncSession,
    actor: str | None = None,
    entity_type: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> dict:
    filters = []
    if actor:
        filters.append(AuditLog.actor.ilike(f"%{actor}%"))
    if entity_type:
        filters.append(AuditLog.entity_type == entity_type)

    base = select(AuditLog)
    if filters:
        base = base.where(*filters)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        base.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "items": logs,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page > 0 else 0,
    }


# ── Coupons ──


async def list_coupons(db: AsyncSession, page: int = 1, per_page: int = 50) -> dict:
    count_q = select(func.count(Coupon.id))
    total = (await db.execute(count_q)).scalar() or 0

    query = (
        select(Coupon)
        .order_by(Coupon.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    coupons = result.scalars().all()

    return {
        "items": coupons,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page > 0 else 0,
    }


async def create_coupon(db: AsyncSession, data: dict) -> Coupon:
    data["code"] = data["code"].strip().upper()
    coupon = Coupon(**data)
    db.add(coupon)
    await db.commit()
    await db.refresh(coupon)
    return coupon


async def update_coupon(db: AsyncSession, coupon_id: int, data: dict) -> Coupon | None:
    result = await db.execute(select(Coupon).where(Coupon.id == coupon_id))
    coupon = result.scalars().first()
    if not coupon:
        return None
    for k, v in data.items():
        if v is not None:
            setattr(coupon, k, v)
    await db.commit()
    await db.refresh(coupon)
    return coupon


async def delete_coupon(db: AsyncSession, coupon_id: int) -> bool:
    result = await db.execute(select(Coupon).where(Coupon.id == coupon_id))
    coupon = result.scalars().first()
    if not coupon:
        return False
    coupon.is_active = False
    await db.commit()
    return True


# ── Analytics ──


async def get_analytics(db: AsyncSession, days: int = 30) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    daily_q = (
        select(
            func.date(Order.created_at).label("day"),
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
            func.count(Order.id).label("orders"),
        )
        .where(Order.created_at >= cutoff, Order.status != "cancelled")
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
    )
    daily_rows = (await db.execute(daily_q)).all()
    daily_revenue = [
        {"date": str(r.day), "revenue": float(r.revenue), "orders": int(r.orders)}
        for r in daily_rows
    ]

    top_q = (
        select(
            OrderItem.product_id,
            Product.name,
            func.sum(OrderItem.quantity).label("units"),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("revenue"),
        )
        .join(Product, Product.id == OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.created_at >= cutoff, Order.status != "cancelled")
        .group_by(OrderItem.product_id, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
    )
    top_rows = (await db.execute(top_q)).all()
    top_products = [
        {
            "product_id": r.product_id,
            "name": r.name,
            "units_sold": int(r.units),
            "revenue": float(r.revenue),
        }
        for r in top_rows
    ]

    status_q = (
        select(Order.status, func.count(Order.id).label("count"))
        .where(Order.created_at >= cutoff)
        .group_by(Order.status)
    )
    status_rows = (await db.execute(status_q)).all()
    orders_by_status = [
        {"status": r.status, "count": int(r.count)} for r in status_rows
    ]

    totals_q = select(
        func.coalesce(func.sum(Order.total_amount), 0),
        func.count(Order.id),
    ).where(Order.created_at >= cutoff, Order.status != "cancelled")
    totals_row = (await db.execute(totals_q)).first()
    total_revenue = float(totals_row[0] or 0)
    total_orders = int(totals_row[1] or 0)
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders else 0.0

    return {
        "daily_revenue": daily_revenue,
        "top_products": top_products,
        "orders_by_status": orders_by_status,
        "total_revenue_30d": round(total_revenue, 2),
        "total_orders_30d": total_orders,
        "avg_order_value": avg_order_value,
    }
