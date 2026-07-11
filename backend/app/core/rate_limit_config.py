from enum import Enum
from typing import Optional, Tuple


class RateLimitTier(str, Enum):
    """Rate limit tiers"""

    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ADMIN = "admin"


class RateLimitConfig:
    """
    Rate limit configuration

    Format: (max_requests, window_seconds)
    """

    # Default limits (per IP)
    DEFAULT_LIMITS = {
        "per_minute": (60, 60),  # 60 requests per minute
        "per_hour": (1000, 3600),  # 1000 requests per hour
        "per_day": (10000, 86400),  # 10000 requests per day
    }

    # Authenticated user limits (more generous)
    USER_LIMITS = {
        RateLimitTier.FREE: {
            "per_minute": (100, 60),
            "per_hour": (2000, 3600),
            "per_day": (20000, 86400),
        },
        RateLimitTier.BASIC: {
            "per_minute": (200, 60),
            "per_hour": (5000, 3600),
            "per_day": (50000, 86400),
        },
        RateLimitTier.PREMIUM: {
            "per_minute": (500, 60),
            "per_hour": (10000, 3600),
            "per_day": (100000, 86400),
        },
        RateLimitTier.ADMIN: {
            "per_minute": (1000, 60),
            "per_hour": (50000, 3600),
            "per_day": (500000, 86400),
        },
    }

    # Endpoint-specific limits (stricter for expensive operations)
    ENDPOINT_LIMITS = {
        # Authentication endpoints
        "/api/v1/auth/login": (5, 60),
        "/api/v1/auth/register": (3, 3600),
        "/api/v1/auth/reset-password": (3, 3600),
        # Search endpoints
        "/api/v1/search/global": (30, 60),
        "/api/v1/search/reservations": (60, 60),
        # Export endpoints
        "/api/v1/reports/export": (5, 300),
        "/api/v1/analytics/export": (5, 300),
        "/api/v1/audit/logs/export": (3, 300),
        # Write operations
        "/api/v1/reservations": (30, 60),
        "/api/v1/guests": (30, 60),
        # Bulk operations
        "/api/v1/reservations/bulk": (5, 60),
    }

    # Burst allowance
    BURST_MULTIPLIER = 1.5

    @classmethod
    def get_user_tier(cls, user_role: str) -> RateLimitTier:
        """Get rate limit tier from user role"""
        role_to_tier = {
            "admin": RateLimitTier.ADMIN,
            "manager": RateLimitTier.PREMIUM,
            "front_desk": RateLimitTier.BASIC,
            "accountant": RateLimitTier.BASIC,
            "housekeeper": RateLimitTier.FREE,
            "maintenance": RateLimitTier.FREE,
            "staff": RateLimitTier.FREE,
        }
        return role_to_tier.get(user_role, RateLimitTier.FREE)

    @classmethod
    def get_endpoint_limit(cls, path: str, method: str) -> Optional[Tuple[int, int]]:
        """Get specific limit for endpoint"""
        # Exact match
        if path in cls.ENDPOINT_LIMITS:
            return cls.ENDPOINT_LIMITS[path]

        # Prefix match
        for endpoint_pattern, limit in cls.ENDPOINT_LIMITS.items():
            if path.startswith(endpoint_pattern):
                return limit

        return None
