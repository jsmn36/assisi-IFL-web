"""
System Health Check API
Comprehensive system health monitoring
"""
from fastapi import APIRouter, Depends
from app.api.dependencies import require_role
from app.core.cache import cache
from app.core.rate_limiter import rate_limiter
from app.database import SessionLocal
from app.models import User
import psutil
from datetime import datetime, timezone

router = APIRouter(prefix="/system-health", tags=["System Health"])


@router.get("")
async def get_system_health(current_user: User = Depends(require_role("admin"))):
    """
    Comprehensive system health check

    Checks:
    - Database connectivity
    - Redis connectivity
    - Celery workers
    - System resources
    """
    health = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": "healthy",
        "components": {},
    }

    # Database
    try:
        from sqlalchemy import text

        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health["components"]["database"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        health["components"]["database"] = {"status": "unhealthy", "message": str(e)}
        health["overall_status"] = "degraded"

    # Redis Cache
    cache_stats = cache.get_stats()
    if cache_stats.get("backend") == "redis":
        health["components"]["redis_cache"] = {
            "status": "healthy",
            "message": "Connected",
            "hit_rate": cache_stats.get("hit_rate", 0),
        }
    else:
        health["components"]["redis_cache"] = {
            "status": "warning",
            "message": "Using in-memory fallback",
            "hit_rate": cache_stats.get("hit_rate", 0),
        }

    # Rate Limiter
    if rate_limiter.redis_client:
        try:
            rate_limiter.redis_client.ping()
            health["components"]["rate_limiter"] = {
                "status": "healthy",
                "message": "Connected",
            }
        except Exception:
            health["components"]["rate_limiter"] = {
                "status": "unhealthy",
                "message": "Redis not responding",
            }
            health["overall_status"] = "degraded"
    else:
        health["components"]["rate_limiter"] = {
            "status": "warning",
            "message": "Redis not available — rate limiting disabled",
        }

    # Celery Workers
    try:
        from app.config import settings

        if not settings.is_postgresql_mode:
            raise Exception("PostgreSQL mode disabled")
        from app.core.celery_config import celery_app

        inspect = celery_app.control.inspect(timeout=2)
        active_workers = inspect.active()

        if active_workers and len(active_workers) > 0:
            health["components"]["celery"] = {
                "status": "healthy",
                "message": f"{len(active_workers)} worker(s) active",
                "workers": list(active_workers.keys()),
            }
        else:
            health["components"]["celery"] = {
                "status": "warning",
                "message": "No active workers",
            }
    except Exception as e:
        health["components"]["celery"] = {
            "status": "warning",
            "message": "Cannot connect to Celery",
        }

    # System Resources
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    resource_status = "healthy"
    if cpu_percent > 80 or memory.percent > 80 or disk.percent > 80:
        resource_status = "warning"

    health["components"]["system_resources"] = {
        "status": resource_status,
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
    }

    # Set overall status
    unhealthy_count = sum(
        1 for c in health["components"].values() if c["status"] == "unhealthy"
    )

    if unhealthy_count > 0:
        health["overall_status"] = "unhealthy"
    elif any(c["status"] == "warning" for c in health["components"].values()):
        if health["overall_status"] == "healthy":
            health["overall_status"] = "warning"

    return health


@router.get("/quick")
async def quick_health_check():
    """Quick health check for load balancers — no auth required"""
    try:
        from sqlalchemy import text

        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception:
        return {"status": "error", "timestamp": datetime.now(timezone.utc).isoformat()}
