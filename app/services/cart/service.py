import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Product
from shared.redis_client import delete_cart, get_cart, set_cart


async def get_user_cart(r: aioredis.Redis, user_id: str) -> dict:
    return await get_cart(r, user_id)


async def add_item(
    r: aioredis.Redis,
    db: AsyncSession,
    user_id: str,
    product_id: int,
    quantity: int,
) -> dict:
    # Validate product exists and is active
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.is_active)
    )
    product = result.scalars().first()
    if not product:
        raise ValueError(f"Product {product_id} not found or inactive")

    if product.stock_quantity is None or product.stock_quantity <= 0:
        raise ValueError(f"{product.name} is out of stock")

    cart = await get_cart(r, user_id)

    # Check if product already in cart
    for item in cart["items"]:
        if item["product_id"] == product_id:
            new_qty = item["quantity"] + quantity
            if new_qty > product.stock_quantity:
                raise ValueError(
                    f"Only {product.stock_quantity} of {product.name} in stock"
                )
            item["quantity"] = new_qty
            await set_cart(r, user_id, cart)
            return cart

    if quantity > product.stock_quantity:
        raise ValueError(f"Only {product.stock_quantity} of {product.name} in stock")

    # Add new item
    cart["items"].append(
        {
            "product_id": product_id,
            "name": product.name,
            "price": float(product.price),
            "quantity": quantity,
        }
    )
    await set_cart(r, user_id, cart)
    return cart


async def update_item(
    r: aioredis.Redis,
    db: AsyncSession,
    user_id: str,
    product_id: int,
    quantity: int,
) -> dict:
    cart = await get_cart(r, user_id)

    for i, item in enumerate(cart["items"]):
        if item["product_id"] == product_id:
            if quantity <= 0:
                cart["items"].pop(i)
            else:
                result = await db.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = result.scalars().first()
                if not product or not product.is_active:
                    raise ValueError(f"Product {product_id} no longer available")
                if product.stock_quantity <= 0:
                    raise ValueError(f"{product.name} is out of stock")
                if quantity > product.stock_quantity:
                    raise ValueError(
                        f"Only {product.stock_quantity} of {product.name} in stock"
                    )
                item["quantity"] = quantity
            await set_cart(r, user_id, cart)
            return cart

    raise ValueError(f"Product {product_id} not in cart")


async def remove_item(r: aioredis.Redis, user_id: str, product_id: int) -> dict:
    cart = await get_cart(r, user_id)
    cart["items"] = [item for item in cart["items"] if item["product_id"] != product_id]
    await set_cart(r, user_id, cart)
    return cart


async def clear_user_cart(r: aioredis.Redis, user_id: str) -> dict:
    await delete_cart(r, user_id)
    return {"items": [], "updated_at": None}
