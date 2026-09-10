"""
Main FastAPI Application
# Enhanced with security features
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_logger import RequestLoggerMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.audit import AuditMiddleware
from app.middleware.tenant import TenantMiddleware
from app.database import engine, Base, init_db, get_db_info
from app.config import settings
from app.core.logging_config import configure_logging
from app.core.observability import init_observability

# Configure structured logging at module-import time so even startup
# log lines (engine init, scheduler bring-up) come through as JSON.
configure_logging()
init_observability()

# Import all routers
from app.api.v1 import (
    auth,
    institutions,
    posts,
    media,
    admin,
    system,
    social_api,
    stories_api,
    chat_api,
    groups_api,
)

# Create tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    pass


# Create FastAPI app
app = FastAPI(
    title="Assisi Social",
    description="Assisi Social community platform",
    version="1.0.0",
    lifespan=lifespan,
)

from app.middleware.cache import CacheMiddleware

app.add_middleware(CacheMiddleware)

# Exception handlers
from fastapi.exceptions import RequestValidationError
from app.services.base_service import ServiceError
from app.api.error_handlers import (
    service_error_handler,
    validation_error_handler,
    unhandled_exception_handler,
)

app.add_exception_handler(ServiceError, service_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# CORS middleware (origins come from CORS_ORIGINS env var, comma-separated)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware (add order is LIFO — last added wraps the rest).
# Outermost wins, so RequestIdMiddleware goes last to wrap everything.
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(TenantMiddleware)  # must be outside Audit so context is set before audit writes
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(RequestIdMiddleware)  # outermost — every log/audit/error gets a correlation id

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(institutions.router, prefix="/api/v1")
app.include_router(posts.router, prefix="/api/v1")
app.include_router(media.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(social_api.router, prefix="/api/v1")
app.include_router(stories_api.router, prefix="/api/v1")
app.include_router(chat_api.router, prefix="/api/v1")
app.include_router(groups_api.router, prefix="/api/v1")

# Mount Static Files folder for media streaming
from fastapi.staticfiles import StaticFiles
import os

os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    db_info = get_db_info()
    return {
        "name": "Assisi Social API",
        "version": "1.0.0",
        "status": "running",
        "database": db_info.get("database_type", "unknown"),
    }


@app.get("/health")
async def health_check():
    """Combined readiness probe — same payload as /ready but always 200."""
    from app.core.health import collect_health

    return await collect_health()


@app.get("/live", include_in_schema=False)
async def liveness():
    """K8s-style liveness probe — process is alive, no external deps."""
    return {"status": "alive"}


@app.get("/ready", include_in_schema=False)
async def readiness():
    """K8s-style readiness probe.

    Returns 503 with the failing component(s) if any required dep (DB) is
    down so a load balancer pulls us out of rotation. Optional deps
    (Redis, Celery) report a degraded state but do not flip the gate.
    """
    from fastapi.responses import JSONResponse

    from app.core.health import collect_health

    payload = await collect_health()
    if payload.get("status") == "unhealthy":
        return JSONResponse(status_code=503, content=payload)
    return payload


@app.get("/database/info")
async def database_info():
    return get_db_info()


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import Response

    return Response(status_code=204)


# Import permissions router
from app.api.v1 import permissions


# Legacy routes deleted for social platform transition

# Mount Prometheus metrics endpoint if available
try:
    from prometheus_client import make_asgi_app
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
except ImportError:
    pass

if __name__ == "__main__":
    import os
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=os.getenv("API_RELOAD", "true").lower() == "true",
    )
