import json

import redis.asyncio as redis

from shared.config import settings

redis_pool = redis.ConnectionPool.from_url(settings.redis_url, decode_responses=True)


def get_redis_client() -> redis.Redis:
    return redis.Redis(connection_pool=redis_pool)


async def get_redis():
    client = get_redis_client()
    try:
        yield client
    finally:
        await client.aclose()


# ── Cart helpers ──

CART_TTL = 86400  # 24 hours


async def get_cart(r: redis.Redis, user_id: str) -> dict:
    data = await r.get(f"cart:{user_id}")
    if data:
        return json.loads(data)
    return {"items": [], "updated_at": None}


async def set_cart(r: redis.Redis, user_id: str, cart_data: dict) -> None:
    from datetime import datetime, timezone

    cart_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await r.set(f"cart:{user_id}", json.dumps(cart_data), ex=CART_TTL)


async def delete_cart(r: redis.Redis, user_id: str) -> None:
    await r.delete(f"cart:{user_id}")
