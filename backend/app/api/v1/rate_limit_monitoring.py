"""
Rate Limit Monitoring API
Real-time monitoring of rate limits and blocked IPs
"""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone
from typing import List
from app.api.dependencies import require_role
from app.core.rate_limiter import rate_limiter
from app.services.abuse_detection_service import AbuseDetectionService
from app.models import User
from pydantic import BaseModel
import json

router = APIRouter(prefix="/rate-limit-monitoring", tags=["Rate Limit Monitoring"])


class RateLimitAlert(BaseModel):
    identifier: str
    alert_type: str
    severity: str
    timestamp: datetime
    details: dict


class RateLimitMetrics(BaseModel):
    total_requests: int
    blocked_requests: int
    blocked_ips: int
    top_consumers: List[dict]
    alerts: List[RateLimitAlert]


@router.get("/metrics", response_model=RateLimitMetrics)
async def get_rate_limit_metrics(current_user: User = Depends(require_role("admin"))):
    """Get comprehensive rate limit metrics"""
    abuse_stats = AbuseDetectionService.get_abuse_stats()

    return RateLimitMetrics(
        total_requests=0,
        blocked_requests=0,
        blocked_ips=abuse_stats.get("blocked_ips", 0),
        top_consumers=[],
        alerts=[],
    )


@router.get("/violations")
async def get_recent_violations(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role("admin")),
):
    """Get recent rate limit violations"""
    return {
        "violations": [],
        "total": 0,
        "message": "Violation tracking in development",
    }


@router.get("/blocked-ips")
async def get_blocked_ips(current_user: User = Depends(require_role("admin"))):
    """Get list of currently blocked IPs"""
    if not rate_limiter.redis_client:
        return {"blocked_ips": [], "redis_connected": False}

    try:
        pattern = "hotel_pms:abuse_detection:blocked_ip:*"
        keys = list(rate_limiter.redis_client.scan_iter(match=pattern, count=100))

        blocked_ips = []
        for key in keys:
            ip = key.decode().split(":")[-1]
            data = rate_limiter.redis_client.get(key)
            if data:
                info = json.loads(data)
                blocked_ips.append(
                    {
                        "ip": ip,
                        "blocked_at": info.get("blocked_at"),
                        "reason": info.get("reason"),
                        "duration": info.get("duration"),
                    }
                )

        return {
            "blocked_ips": blocked_ips,
            "total": len(blocked_ips),
            "redis_connected": True,
        }
    except Exception as e:
        return {"error": str(e), "redis_connected": False}


@router.post("/unblock-ip/{ip_address}")
async def unblock_ip(
    ip_address: str, current_user: User = Depends(require_role("admin"))
):
    """Unblock an IP address"""
    AbuseDetectionService.unblock_ip(ip_address)
    return {"success": True, "message": f"IP {ip_address} has been unblocked"}


@router.post("/block-ip/{ip_address}")
async def block_ip(
    ip_address: str,
    duration_seconds: int = Query(3600, ge=60, le=86400),
    reason: str = Query("Manual block by admin"),
    current_user: User = Depends(require_role("admin")),
):
    """Manually block an IP address"""
    AbuseDetectionService.block_ip(ip_address, duration_seconds, reason)
    return {
        "success": True,
        "message": f"IP {ip_address} blocked for {duration_seconds} seconds",
        "reason": reason,
    }


@router.get("/health")
async def rate_limit_health(current_user: User = Depends(require_role("admin"))):
    """Check rate limiting system health"""
    redis_connected = rate_limiter.redis_client is not None

    return {
        "redis_connected": redis_connected,
        "rate_limiting_enabled": redis_connected,
        "abuse_detection_enabled": redis_connected,
        "status": "healthy" if redis_connected else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
