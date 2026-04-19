import redis.asyncio as aioredis
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import CurrentUser
from shared.coupons import validate_and_calculate
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.redis_client import get_cart, get_redis
from shared.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    CouponValidateRequest,
    CouponValidateResponse,
    OrderList,
    OrderOut,
    ReorderResponse,
)

from . import service

router = APIRouter(prefix="/api", tags=["checkout"])


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    background_tasks: BackgroundTasks,
    body: CheckoutRequest | None = None,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    r: aioredis.Redis = Depends(get_redis),
):
    """
    Order finalization is sync (so the response carries the order_id and total),
    but the SQS publish that triggers PDF + S3 + SES runs as a BackgroundTask —
    FastAPI sends the HTTP response first, then executes the task in its
    threadpool. This is what lets the customer immediately click \"Continue
    Shopping\" or \"View My Orders\" while the invoice generates in the background.
    """
    coupon_code = body.coupon_code if body else None
    try:
        response, sqs_message = await service.process_checkout(
            db, r, user.cognito_sub, user.email, coupon_code=coupon_code
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    background_tasks.add_task(service.publish_invoice_message, sqs_message)
    return response


@router.post("/coupons/validate", response_model=CouponValidateResponse)
async def validate_coupon(
    body: CouponValidateRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    r: aioredis.Redis = Depends(get_redis),
):
    cart = await get_cart(r, user.cognito_sub)
    cart_total = sum(i["price"] * i["quantity"] for i in cart["items"]) or body.cart_total
    return await validate_and_calculate(db, body.code, cart_total)


@router.get("/orders", response_model=OrderList)
async def list_orders(
    page: int = 1,
    per_page: int = 20,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_orders(db, user.cognito_sub, page, per_page)


@router.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await service.get_order(db, user.cognito_sub, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/orders/{order_id}/cancel", response_model=OrderOut)
async def cancel_order(
    order_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await service.cancel_order(db, user.cognito_sub, order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orders/{order_id}/reorder", response_model=ReorderResponse)
async def reorder(
    order_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    r: aioredis.Redis = Depends(get_redis),
):
    try:
        return await service.reorder(db, r, user.cognito_sub, order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
