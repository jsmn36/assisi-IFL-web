from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import psutil

from app.api.dependencies import get_db, require_role
from app.core.cache import cache
from app.database import get_connection_pool_status, engine
from app.models import User
from app.utils.db_optimization import get_pool_status

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/metrics")
async def get_metrics(
    current_user: User = Depends(require_role("admin")), db: Session = Depends(get_db)
):
    """Get comprehensive system performance metrics"""

    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    # Cache metrics
    cache_stats = cache.get_stats()

    # Database metrics
    try:
        db_pool = get_connection_pool_status(engine)
    except Exception:
        db_pool = {"error": "Pool status unavailable"}

    # API metrics (placeholder)
    api_metrics = {
        "total_requests": "N/A",
        "avg_response_time": "N/A",
        "error_rate": "N/A",
    }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "disk_percent": disk.percent,
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
        },
        "cache": cache_stats,
        "database": db_pool,
        "api": api_metrics,
    }


@router.get("/performance/summary")
async def get_performance_summary(
    current_user: User = Depends(require_role("admin", "manager")),
):
    """Get high-level performance summary with scoring"""

    cache_stats = cache.get_stats()

    # Calculate performance score (0-100)
    hit_rate = cache_stats.get("hit_rate", 0)

    # Simple scoring
    cache_score = min(hit_rate, 100)

    status = (
        "excellent"
        if cache_score >= 80
        else "good"
        if cache_score >= 60
        else "needs_improvement"
    )

    return {
        "overall_score": cache_score,
        "status": status,
        "cache_hit_rate": hit_rate,
        "recommendations": [
            "Cache hit rate is good"
            if hit_rate >= 70
            else "Consider increasing cache TTL",
            "System is performing well" if cache_score >= 80 else "Review slow queries",
        ],
    }


@router.get("/cache/performance")
async def get_cache_performance(
    current_user: User = Depends(require_role("admin")),
):
    """Get detailed cache performance metrics with grading"""

    cache_stats = cache.get_stats()

    hit_rate = cache_stats.get("hit_rate", 0)
    used_memory = cache_stats.get("used_memory_bytes", 0)

    # Performance grading (A/B/C scale)
    if hit_rate >= 70:
        grade = "A"
    elif hit_rate >= 50:
        grade = "B"
    else:
        grade = "C"

    # Detailed recommendations
    recommendations = [
        "Cache hit rate is good"
        if hit_rate >= 70
        else "Consider increasing TTL values",
        "Monitor memory usage"
        if used_memory > 100 * 1024 * 1024
        else "Memory usage is healthy",
    ]

    return {
        "current_stats": cache_stats,
        "performance_grade": grade,
        "recommendations": recommendations,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/database/performance")
async def get_database_performance(
    current_user: User = Depends(require_role("admin")),
):
    """Get detailed database performance metrics with health status"""

    pool_status = get_pool_status(engine)

    total_connections = pool_status.get("total_connections", 0)
    checked_out = pool_status.get("checked_out", 0)
    pool_size = pool_status.get("size", 0)

    # Safe utilization calculation
    utilization = (
        (checked_out / total_connections * 100) if total_connections > 0 else 0
    )

    # Health status classification
    if utilization < 80:
        health = "healthy"
    elif utilization < 95:
        health = "warning"
    else:
        health = "critical"

    # DB-specific recommendations
    recommendations = [
        "Pool utilization is normal"
        if utilization < 80
        else "Consider increasing pool size",
        "Monitor for connection leaks"
        if checked_out > pool_size
        else "Connection usage is normal",
    ]

    return {
        "pool_status": pool_status,
        "utilization_percent": round(utilization, 2),
        "health": health,
        "recommendations": recommendations,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/cache/clear")
async def clear_cache(
    namespace: str = "all",
    current_user: User = Depends(require_role("admin")),
):
    """Clear cache by namespace or all caches (admin only)"""

    if namespace == "all":
        from app.services.cache_invalidation_service import CacheInvalidationService

        CacheInvalidationService.invalidate_all()
        return {"message": "All caches cleared"}
    else:
        cache.clear_namespace(namespace)
        return {"message": f"Cache namespace '{namespace}' cleared"}
