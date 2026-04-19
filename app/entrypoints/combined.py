import asyncio
import json
import logging
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from shared.config import settings, validate_prod
from shared.database import engine
from shared.redis_client import get_redis_client
from services.catalog.router import router as catalog_router, storefront_router
from services.cart.router import router as cart_router
from services.checkout.router import router as checkout_router

# -- Logging --
class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "service": "combined",
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "method": getattr(record, "method", None),
            "path": getattr(record, "path", None),
            "status_code": getattr(record, "status_code", None),
            "duration_ms": getattr(record, "duration_ms", None),
        })

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(logging.INFO)
logger = logging.getLogger("combined")

# -- App --
app = FastAPI(title="ShopCloud Combined (Dev)", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)
    logger.info(
        "request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.on_event("startup")
async def startup():
    validate_prod()
    for attempt in range(5):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connected")
            break
        except Exception:
            logger.warning(f"DB not ready, retry {attempt + 1}/5...")
            await asyncio.sleep(3)
    else:
        raise RuntimeError("Cannot connect to database after 5 attempts")

    try:
        r = get_redis_client()
        await r.ping()
        await r.aclose()
        logger.info("Redis connected")
    except Exception:
        logger.warning("Redis not available — cart features will fail")


@app.get("/health")
async def health():
    status = {"service": "combined", "postgres": "unknown", "redis": "unknown"}
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        status["postgres"] = "healthy"
    except Exception:
        status["postgres"] = "unhealthy"

    try:
        r = get_redis_client()
        await r.ping()
        await r.aclose()
        status["redis"] = "healthy"
    except Exception:
        status["redis"] = "unhealthy"

    overall = "healthy" if status["postgres"] == "healthy" and status["redis"] == "healthy" else "degraded"
    status["status"] = overall

    if overall != "healthy":
        raise HTTPException(status_code=503, detail=status)
    return status


# Mount all service routers
app.include_router(catalog_router)
app.include_router(storefront_router)
app.include_router(cart_router)
app.include_router(checkout_router)
