import asyncio
import json
import logging
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from shared.config import settings, validate_prod
from shared.redis_client import get_redis_client
from services.cart.router import router

# ── Logging ──
class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "service": "cart",
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
logger = logging.getLogger("cart")

# ── App ──
app = FastAPI(title="ShopCloud Cart Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.on_event("startup")
async def startup():
    validate_prod()


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


@app.get("/health")
async def health():
    try:
        r = get_redis_client()
        await r.ping()
        await r.aclose()
        return {"status": "healthy", "service": "cart"}
    except Exception:
        raise HTTPException(status_code=503, detail="Redis unreachable")


app.include_router(router)
