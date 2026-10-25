"""Dukaan Assistant FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db
from app.routes import admin, ai, auth, billing, dashboard, invoices, products, reorders, shop, uploads
from app.schemas import HealthOut

logger = logging.getLogger("dukaan")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    settings.require_jwt_secret()
    init_db()
    from app.seed import bootstrap

    bootstrap()
    yield


app = FastAPI(
    title="Dukaan Assistant API",
    description="Hackathon MVP for small-retail inventory, billing, reorders, and AI advice.",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Authorization"],
)


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > get_settings().max_request_bytes:
                return JSONResponse({"detail": "Request body too large"}, status_code=413)
        except ValueError:
            return JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)
    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def validation_handler(_request: Request, exc: RequestValidationError):
    messages = []
    for error in exc.errors():
        loc = " → ".join(str(part) for part in error.get("loc", []) if part != "body")
        messages.append(f"{loc}: {error.get('msg')}" if loc else error.get("msg", "Invalid input"))
    return JSONResponse({"detail": messages[0] if len(messages) == 1 else messages}, status_code=422)


@app.exception_handler(Exception)
async def unhandled_handler(_request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    logger.exception("Unhandled server error")
    detail = str(exc) if get_settings().debug else "An unexpected error occurred. Please try again."
    return JSONResponse({"detail": detail}, status_code=500)


@app.get("/api/health", response_model=HealthOut, tags=["health"])
def health() -> HealthOut:
    return HealthOut(status="ok", service="dukaan-assistant")


app.include_router(auth.router)
app.include_router(shop.router)
app.include_router(products.router)
app.include_router(dashboard.router)
app.include_router(invoices.router)
app.include_router(reorders.router)
app.include_router(ai.router)
app.include_router(uploads.router)
app.include_router(billing.router)
app.include_router(admin.router)
