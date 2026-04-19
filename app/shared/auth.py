import logging
from dataclasses import dataclass

import httpx
from fastapi import HTTPException, Request
from jose import JWTError, jwt

from shared.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CurrentUser:
    cognito_sub: str
    email: str


@dataclass
class AdminUser:
    cognito_sub: str
    email: str


# Cognito JWKS cache
_jwks: dict | None = None
_admin_jwks: dict | None = None


async def _fetch_jwks(pool_id: str, region: str) -> dict:
    url = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


def _get_public_key(token: str, jwks: dict) -> dict:
    headers = jwt.get_unverified_headers(token)
    kid = headers.get("kid")
    for key in jwks.get("keys", []):
        if key["kid"] == kid:
            return key
    raise HTTPException(status_code=401, detail="Token key not found")


async def validate_customer_token(request: Request) -> CurrentUser:
    if not settings.cognito_user_pool_id:
        # Hard-fail in prod: an unset pool ID in a production deploy means
        # the SSM → ECS env-injection chain broke. Silently bypassing auth
        # would let anyone impersonate any user. Dev-bypass stays for local.
        if settings.environment == "prod":
            raise HTTPException(
                status_code=503,
                detail="Auth misconfigured: COGNITO_USER_POOL_ID empty in prod",
            )
        return CurrentUser(cognito_sub="local-dev-user", email="dev@localhost")

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    global _jwks
    if _jwks is None:
        _jwks = await _fetch_jwks(
            settings.cognito_user_pool_id, settings.cognito_region
        )

    try:
        key = _get_public_key(token, _jwks)
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.cognito_app_client_id,
            issuer=f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/{settings.cognito_user_pool_id}",
        )
        return CurrentUser(cognito_sub=payload["sub"], email=payload.get("email", ""))
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


async def validate_admin_token(request: Request) -> AdminUser:
    if not settings.cognito_admin_pool_id:
        if settings.environment == "prod":
            raise HTTPException(
                status_code=503,
                detail="Auth misconfigured: COGNITO_ADMIN_POOL_ID empty in prod",
            )
        return AdminUser(cognito_sub="local-admin-user", email="admin@localhost")

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    global _admin_jwks
    if _admin_jwks is None:
        _admin_jwks = await _fetch_jwks(
            settings.cognito_admin_pool_id, settings.cognito_region
        )

    try:
        key = _get_public_key(token, _admin_jwks)
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=settings.cognito_admin_client_id,
            issuer=f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/{settings.cognito_admin_pool_id}",
        )
        return AdminUser(cognito_sub=payload["sub"], email=payload.get("email", ""))
    except JWTError as e:
        logger.warning(f"Admin JWT validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid admin token")
