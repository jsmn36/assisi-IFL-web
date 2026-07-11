import json
import logging
import time
import uuid
from typing import List, Tuple

from app.core.cache import cache

logger = logging.getLogger(__name__)

VIOLATION_KEY = "hotel_pms:rate_limit:violations"
VIOLATION_RETENTION_SECONDS = 7 * 24 * 3600  # 7 days
VIOLATION_MAX_ENTRIES = 10_000


class RateLimiter:
    """
    Rate limiter using sliding window algorithm (Redis sorted set)

    Features:
    - Sliding window log
    - Redis-based storage
    - Per-IP / user / endpoint limiting
    - Burst handling
    """

    def __init__(self):
        self.redis_client = getattr(cache, "redis_client", None)

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        namespace: str = "rate_limit",
    ) -> Tuple[bool, dict]:
        if not self.redis_client:
            return True, {
                "limit": max_requests,
                "remaining": max_requests,
                "reset": int(time.time() + window_seconds),
            }

        cache_key = f"hotel_pms:{namespace}:{key}"
        current_time = int(time.time())
        window_start = current_time - window_seconds

        try:
            pipe = self.redis_client.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(cache_key, 0, window_start)

            # Count current requests
            pipe.zcard(cache_key)

            # Add current request with UNIQUE ID
            unique_id = f"{current_time}-{uuid.uuid4()}"
            pipe.zadd(cache_key, {unique_id: current_time})

            # Expire key
            pipe.expire(cache_key, window_seconds)

            results = pipe.execute()
            request_count = results[1]

            allowed = request_count < max_requests
            remaining = max(0, max_requests - request_count - 1)

            return allowed, {
                "limit": max_requests,
                "remaining": remaining,
                "reset": current_time + window_seconds,
                "retry_after": window_seconds if not allowed else None,
            }

        except Exception:
            logger.exception("Rate limit check failed for key=%s", key)
            return True, {
                "limit": max_requests,
                "remaining": max_requests,
                "reset": current_time + window_seconds,
            }

    def record_violation(
        self,
        *,
        key: str,
        limit: int,
        window_seconds: int,
        ip: str,
        path: str,
        user_id: str | int | None = None,
    ) -> None:
        """Append a rate-limit violation to the shared sorted set.

        Score is a unix timestamp; payload is a JSON blob. The set is trimmed
        to the retention window + max-entries cap so it never grows unbounded.
        """
        if not self.redis_client:
            return

        now = int(time.time())
        payload = json.dumps(
            {
                "ts": now,
                "key": key,
                "limit": limit,
                "window": window_seconds,
                "ip": ip,
                "path": path,
                "user_id": user_id,
                "id": uuid.uuid4().hex,
            },
            default=str,
        )
        try:
            pipe = self.redis_client.pipeline()
            pipe.zadd(VIOLATION_KEY, {payload: now})
            pipe.zremrangebyscore(VIOLATION_KEY, 0, now - VIOLATION_RETENTION_SECONDS)
            # Trim oldest entries if we blew past the cap (leave the newest N)
            pipe.zremrangebyrank(VIOLATION_KEY, 0, -VIOLATION_MAX_ENTRIES - 1)
            pipe.expire(VIOLATION_KEY, VIOLATION_RETENTION_SECONDS)
            pipe.execute()
        except Exception:
            logger.exception("Failed to record rate-limit violation for key=%s", key)

    def get_violations(self, limit: int = 100) -> List[dict]:
        """Return the most recent N violations (newest first)."""
        if not self.redis_client:
            return []
        try:
            raw = self.redis_client.zrevrange(VIOLATION_KEY, 0, max(0, limit - 1))
        except Exception:
            logger.exception("Failed to read rate-limit violations")
            return []

        out: List[dict] = []
        for entry in raw:
            try:
                out.append(json.loads(entry))
            except (TypeError, ValueError):
                continue
        return out

    def check_multiple_limits(
        self, checks: List[Tuple[str, int, int]]
    ) -> Tuple[bool, dict]:
        all_allowed = True
        strictest_info = None

        for key, max_requests, window_seconds in checks:
            allowed, info = self.check_rate_limit(key, max_requests, window_seconds)

            if not allowed:
                all_allowed = False
                if (
                    strictest_info is None
                    or info["remaining"] < strictest_info["remaining"]
                ):
                    strictest_info = info

        if not all_allowed:
            return False, strictest_info

        # IMPORTANT: Do NOT call again (prevents double counting)
        return True, {
            "limit": checks[0][1],
            "remaining": checks[0][1],
            "reset": int(time.time() + checks[0][2]),
        }

    def reset_limit(self, key: str, namespace: str = "rate_limit") -> bool:
        if not self.redis_client:
            return False

        try:
            cache_key = f"hotel_pms:{namespace}:{key}"
            self.redis_client.delete(cache_key)
            return True
        except Exception:
            logger.exception("Rate limit reset failed for key=%s", key)
            return False

    def get_limit_status(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        namespace: str = "rate_limit",
    ) -> dict:
        if not self.redis_client:
            return {
                "limit": max_requests,
                "remaining": max_requests,
                "reset": int(time.time() + window_seconds),
                "current_count": 0,
            }

        cache_key = f"hotel_pms:{namespace}:{key}"
        current_time = int(time.time())
        window_start = current_time - window_seconds

        try:
            self.redis_client.zremrangebyscore(cache_key, 0, window_start)
            count = self.redis_client.zcard(cache_key)

            return {
                "limit": max_requests,
                "remaining": max(0, max_requests - count),
                "reset": current_time + window_seconds,
                "current_count": count,
            }

        except Exception:
            logger.exception("Rate limit status read failed for key=%s", key)
            return {
                "limit": max_requests,
                "remaining": max_requests,
                "reset": current_time + window_seconds,
                "current_count": 0,
            }


# Global instance
rate_limiter = RateLimiter()
