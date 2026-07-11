from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, require_role, get_current_user
from app.core.rate_limiter import rate_limiter
from app.core.rate_limit_config import RateLimitConfig
from app.models import User
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/rate-limits", tags=["Rate Limits"])


# ✅ FIX: Proper indentation
class RateLimitStatus(BaseModel):
    identifier: str
    limit: int
    remaining: int
    reset: int
    current_count: int


@router.get("/status")
async def get_rate_limit_status(
    request: Request, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current rate limit status for authenticated user"""

    # ✅ Safe tier fetch
    tier = RateLimitConfig.get_user_tier(current_user.role)

    if tier not in RateLimitConfig.USER_LIMITS:
        raise HTTPException(status_code=500, detail="Invalid user tier configuration")

    limits = RateLimitConfig.USER_LIMITS[tier]

    # ✅ Build key
    user_key = f"user:{current_user.id}"

    # ✅ Get current status safely
    status = rate_limiter.get_limit_status(
        user_key, limits["per_minute"][0], limits["per_minute"][1]
    )

    return {
        "tier": tier.value,
        "limits": {
            "per_minute": limits["per_minute"][0],
            "per_hour": limits["per_hour"][0],
            "per_day": limits["per_day"][0],
        },
        "current_status": status,
    }


@router.get("/config")
async def get_rate_limit_config(
    current_user: User = Depends(require_role("admin")),
) -> Dict[str, Any]:
    """Get rate limit configuration (Admin only)"""

    return {
        "default_limits": RateLimitConfig.DEFAULT_LIMITS,
        "user_tiers": {
            tier.value: limits for tier, limits in RateLimitConfig.USER_LIMITS.items()
        },
        "endpoint_limits": RateLimitConfig.ENDPOINT_LIMITS,
        "burst_multiplier": RateLimitConfig.BURST_MULTIPLIER,
    }


@router.post("/reset/{user_id}")
async def reset_user_rate_limit(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
) -> Dict[str, Any]:
    """Reset rate limit for user (Admin only)"""

    key = f"user:{user_id}"

    try:
        success = rate_limiter.reset_limit(key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "success": success,
        "message": f"Rate limit reset for user {user_id}"
        if success
        else "Failed to reset",
    }


@router.get("/violations")
async def get_rate_limit_violations(
    limit: int = 100,
    current_user: User = Depends(require_role("admin")),
) -> Dict[str, Any]:
    """Get recent rate-limit violations (Admin only).

    Violations are persisted in a Redis sorted set by RateLimiter.record_violation
    when a request is blocked by the rate-limit middleware. Returns up to `limit`
    entries ordered newest-first.
    """
    limit = max(1, min(limit, 1000))
    violations = rate_limiter.get_violations(limit=limit)
    return {
        "violations": violations,
        "count": len(violations),
        "redis_connected": bool(rate_limiter.redis_client),
    }


@router.get("/stats")
async def get_rate_limit_stats(
    current_user: User = Depends(require_role("admin")),
) -> Dict[str, Any]:
    """Get rate limit statistics (Admin only)"""

    if not rate_limiter.redis_client:
        return {"redis_connected": False}

    try:
        # ⚠️ WARNING: scan_iter can be expensive in production
        pattern = "hotel_pms:rate_limit:*"
        count = 0

        for _ in rate_limiter.redis_client.scan_iter(match=pattern, count=100):
            count += 1
            if count > 1000:  # ✅ safety cap
                break

        return {
            "total_tracked_keys": count,
            "redis_connected": True,
        }

    except Exception as e:
        return {
            "error": str(e),
            "redis_connected": False,
        }
