from fastapi import Depends, Request

from shared.auth import AdminUser, CurrentUser, validate_admin_token, validate_customer_token
from shared.database import get_db
from shared.redis_client import get_redis


async def get_current_user(request: Request) -> CurrentUser:
    return await validate_customer_token(request)


async def get_current_admin(request: Request) -> AdminUser:
    return await validate_admin_token(request)
