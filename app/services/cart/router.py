import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth import CurrentUser
from shared.database import get_db
from shared.dependencies import get_current_user
from shared.redis_client import get_redis
from shared.schemas import AddToCartRequest, CartResponse, UpdateCartRequest

from . import service

router = APIRouter(prefix="/api/cart", tags=["cart"])


@router.get("", response_model=CartResponse)
async def get_cart(
    user: CurrentUser = Depends(get_current_user),
    r: aioredis.Redis = Depends(get_redis),
):
    return await service.get_user_cart(r, user.cognito_sub)


@router.post("/items", response_model=CartResponse)
async def add_to_cart(
    body: AddToCartRequest,
    user: CurrentUser = Depends(get_current_user),
    r: aioredis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await service.add_item(r, db, user.cognito_sub, body.product_id, body.quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/items/{product_id}", response_model=CartResponse)
async def update_cart_item(
    product_id: int,
    body: UpdateCartRequest,
    user: CurrentUser = Depends(get_current_user),
    r: aioredis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await service.update_item(r, db, user.cognito_sub, product_id, body.quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/items/{product_id}", response_model=CartResponse)
async def remove_cart_item(
    product_id: int,
    user: CurrentUser = Depends(get_current_user),
    r: aioredis.Redis = Depends(get_redis),
):
    return await service.remove_item(r, user.cognito_sub, product_id)


@router.delete("", response_model=CartResponse)
async def clear_cart(
    user: CurrentUser = Depends(get_current_user),
    r: aioredis.Redis = Depends(get_redis),
):
    return await service.clear_user_cart(r, user.cognito_sub)
