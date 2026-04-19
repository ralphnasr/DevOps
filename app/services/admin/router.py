from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import AdminUser
from shared.database import get_db
from shared.dependencies import get_current_admin
from shared.schemas import (
    AdminCouponCreate,
    AdminProductCreate,
    AdminProductUpdate,
)

from . import service

import os

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Dashboard ──


@router.get("", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    stats = await service.get_dashboard_stats(db)
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "admin": admin,
            **stats,
        },
    )


# ── Products ──


@router.get("/products", response_class=HTMLResponse)
async def list_products(
    request: Request,
    search: str | None = None,
    page: int = 1,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await service.list_products_admin(db, search=search, page=page)
    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "admin": admin,
            "search": search or "",
            **result,
        },
    )


@router.get("/products/new", response_class=HTMLResponse)
async def new_product_form(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    categories = await service.list_categories(db)
    return templates.TemplateResponse(
        "product_form.html",
        {
            "request": request,
            "admin": admin,
            "product": None,
            "categories": categories,
        },
    )


@router.post("/products")
async def create_product(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    data = AdminProductCreate(
        name=form["name"],
        description=form.get("description", ""),
        price=float(form["price"]),
        category_id=int(form["category_id"]) if form.get("category_id") else None,
        image_url=form.get("image_url", ""),
        stock_quantity=int(form.get("stock_quantity", 0)),
    )
    product = await service.create_product(db, data.model_dump(exclude_none=True))
    await service.log_audit(
        db,
        admin.email,
        "product.create",
        "product",
        product.id,
        {"name": product.name, "price": float(product.price)},
    )
    return RedirectResponse(url="/admin/products", status_code=303)


@router.get("/products/{product_id}/edit", response_class=HTMLResponse)
async def edit_product_form(
    request: Request,
    product_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    product = await service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    categories = await service.list_categories(db)
    return templates.TemplateResponse(
        "product_form.html",
        {
            "request": request,
            "admin": admin,
            "product": product,
            "categories": categories,
        },
    )


@router.post("/products/{product_id}")
async def update_product(
    request: Request,
    product_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    data = AdminProductUpdate(
        name=form.get("name"),
        description=form.get("description"),
        price=float(form["price"]) if form.get("price") else None,
        category_id=int(form["category_id"]) if form.get("category_id") else None,
        image_url=form.get("image_url"),
        stock_quantity=int(form["stock_quantity"])
        if form.get("stock_quantity")
        else None,
        is_active=form.get("is_active") == "on",
    )
    payload = data.model_dump(exclude_none=True)
    result = await service.update_product(db, product_id, payload)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    await service.log_audit(
        db,
        admin.email,
        "product.update",
        "product",
        product_id,
        payload,
    )
    return RedirectResponse(url="/admin/products", status_code=303)


@router.post("/products/{product_id}/delete")
async def delete_product(
    product_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    success = await service.deactivate_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    await service.log_audit(
        db,
        admin.email,
        "product.deactivate",
        "product",
        product_id,
    )
    return RedirectResponse(url="/admin/products", status_code=303)


# ── Inventory ──


@router.get("/inventory", response_class=HTMLResponse)
async def inventory(
    request: Request,
    page: int = 1,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await service.list_products_admin(db, page=page)
    return templates.TemplateResponse(
        "inventory.html",
        {
            "request": request,
            "admin": admin,
            **result,
        },
    )


@router.post("/inventory/{product_id}")
async def update_inventory(
    product_id: int,
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    quantity = int(form["stock_quantity"])
    result = await service.update_stock(db, product_id, quantity)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    await service.log_audit(
        db,
        admin.email,
        "inventory.update",
        "product",
        product_id,
        {"new_stock": quantity},
    )
    return RedirectResponse(url="/admin/inventory", status_code=303)


# ── Orders ──


@router.get("/orders", response_class=HTMLResponse)
async def list_orders(
    request: Request,
    status: str | None = None,
    page: int = 1,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await service.list_orders_admin(db, status=status, page=page)
    return templates.TemplateResponse(
        "orders.html",
        {
            "request": request,
            "admin": admin,
            "status_filter": status or "",
            **result,
        },
    )


@router.post("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    new_status = form["status"]
    try:
        result = await service.update_order_status(db, order_id, new_status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="Order not found")
    await service.log_audit(
        db,
        admin.email,
        "order.status_change",
        "order",
        order_id,
        {"new_status": new_status},
    )
    return RedirectResponse(url="/admin/orders", status_code=303)


# ── Coupons ──


@router.get("/coupons", response_class=HTMLResponse)
async def list_coupons(
    request: Request,
    page: int = 1,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await service.list_coupons(db, page=page)
    return templates.TemplateResponse(
        "coupons.html",
        {
            "request": request,
            "admin": admin,
            **result,
        },
    )


@router.post("/coupons")
async def create_coupon(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()
    valid_until = form.get("valid_until") or None
    valid_until_dt = datetime.fromisoformat(valid_until) if valid_until else None
    data = AdminCouponCreate(
        code=form["code"],
        description=form.get("description") or None,
        discount_type=form["discount_type"],
        discount_value=float(form["discount_value"]),
        min_order_amount=float(form.get("min_order_amount") or 0),
        max_uses=int(form["max_uses"]) if form.get("max_uses") else None,
        valid_until=valid_until_dt,
        is_active=form.get("is_active", "on") == "on",
    )
    try:
        coupon = await service.create_coupon(db, data.model_dump(exclude_none=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not create coupon: {e}")
    await service.log_audit(
        db,
        admin.email,
        "coupon.create",
        "coupon",
        coupon.id,
        {"code": coupon.code, "discount": float(coupon.discount_value)},
    )
    return RedirectResponse(url="/admin/coupons", status_code=303)


@router.post("/coupons/{coupon_id}/toggle")
async def toggle_coupon(
    coupon_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    coupons = await service.list_coupons(db, per_page=1000)
    target = next((c for c in coupons["items"] if c.id == coupon_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Coupon not found")
    new_status = not target.is_active
    await service.update_coupon(db, coupon_id, {"is_active": new_status})
    await service.log_audit(
        db,
        admin.email,
        "coupon.toggle",
        "coupon",
        coupon_id,
        {"is_active": new_status},
    )
    return RedirectResponse(url="/admin/coupons", status_code=303)


# ── Audit Log ──


@router.get("/audit", response_class=HTMLResponse)
async def audit_log(
    request: Request,
    actor: str | None = None,
    entity_type: str | None = None,
    page: int = 1,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await service.list_audit_logs(
        db, actor=actor, entity_type=entity_type, page=page
    )
    return templates.TemplateResponse(
        "audit.html",
        {
            "request": request,
            "admin": admin,
            "actor_filter": actor or "",
            "entity_type_filter": entity_type or "",
            **result,
        },
    )


# ── Analytics ──


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(
    request: Request,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    data = await service.get_analytics(db)
    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "admin": admin,
            **data,
        },
    )


@router.get("/api/analytics")
async def analytics_api(
    days: int = 30,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    data = await service.get_analytics(db, days=days)
    return JSONResponse(data)
