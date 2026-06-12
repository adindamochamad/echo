import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.database import engine
from app.limiter import limiter
import app.models  # noqa: F401 — registrasi ORM models ke Base.metadata
from app.routers import auth, demo, health, postmortems

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _safe_value(v: object) -> object:
    """Convert a value to a JSON-safe type. Pydantic v2 ctx may contain Exception objects."""
    if isinstance(v, bytes):
        return v.decode("utf-8", errors="replace")
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    if isinstance(v, (list, tuple)):
        return [_safe_value(item) for item in v]
    if isinstance(v, dict):
        return {k: _safe_value(val) for k, val in v.items()}
    return str(v)  # Exception objects, etc.


def _serialkan_error_validasi(daftar_error: list) -> list:
    return [{k: _safe_value(v) for k, v in error.items()} for error in daftar_error]


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("ECHO API berjalan — environment: %s", settings.ENVIRONMENT)
    yield


# Origin unik untuk CORS (dev + production)
daftar_origin = list(
    dict.fromkeys(
        [
            "http://localhost:3000",
            "https://echo-app.vercel.app",
            settings.FRONTEND_URL,
        ]
    )
)

app = FastAPI(title="ECHO API", version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter


@app.exception_handler(Exception)
async def penangan_umum(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(RateLimitExceeded)
async def penangan_rate_limit(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Demo limit reached. Try again in a minute."},
    )


@app.exception_handler(RequestValidationError)
async def penangan_validasi(request: Request, exc: RequestValidationError):
    for error in exc.errors():
        pesan = str(error.get("msg", ""))
        # 413 hanya untuk upload file terlalu besar, bukan validasi panjang teks
        if "file too large" in pesan.lower():
            return JSONResponse(status_code=413, content={"detail": pesan})
    return JSONResponse(status_code=422, content={"detail": _serialkan_error_validasi(exc.errors())})


app.add_middleware(SlowAPIMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=daftar_origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(demo.router, prefix="/api/v1")
app.include_router(postmortems.router, prefix="/api/v1")
