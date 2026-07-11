from datetime import datetime, timezone
from typing import Dict
from app.core.cache import cache


class AbuseDetectionService:
    """
    Service for detecting API abuse patterns

    Detections:
    - Rapid repeated requests
    - Failed authentication attempts
    - Suspicious patterns
    - IP reputation
    """

    @staticmethod
    def track_failed_auth(identifier: str, max_failures: int = 5) -> bool:
        """
        Track failed authentication attempts

        Returns:
            True if should block, False otherwise
        """
        key = f"failed_auth:{identifier}"

        # Safely get count
        count = cache.get(key, namespace="abuse_detection")
        count = int(count) if count is not None else 0

        count += 1

        # Store with TTL (1 hour)
        cache.set(key, count, namespace="abuse_detection", ttl=3600)

        return count >= max_failures

    @staticmethod
    def reset_failed_auth(identifier: str):
        """Reset failed authentication counter"""
        key = f"failed_auth:{identifier}"
        cache.delete(key, namespace="abuse_detection")

    @staticmethod
    def is_ip_blocked(ip_address: str) -> bool:
        """Check if IP is blocked"""
        key = f"blocked_ip:{ip_address}"
        blocked = cache.get(key, namespace="abuse_detection")

        # Explicit check (safer)
        return blocked is not None

    @staticmethod
    def block_ip(ip_address: str, duration_seconds: int = 3600, reason: str = ""):
        """Block IP address"""
        key = f"blocked_ip:{ip_address}"

        data = {
            "blocked_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
            "duration": duration_seconds,
        }

        cache.set(
            key,
            data,
            namespace="abuse_detection",
            ttl=duration_seconds,
        )

    @staticmethod
    def unblock_ip(ip_address: str):
        """Unblock IP address"""
        key = f"blocked_ip:{ip_address}"
        cache.delete(key, namespace="abuse_detection")

    @staticmethod
    def track_suspicious_pattern(
        identifier: str,
        pattern: str,
        threshold: int = 10,
    ) -> bool:
        """
        Track suspicious patterns

        Args:
            identifier: IP or user ID
            pattern: Pattern type (e.g., "rapid_requests")
            threshold: Threshold before flagging

        Returns:
            True if threshold exceeded
        """
        key = f"pattern:{pattern}:{identifier}"

        try:
            count = cache.incr(key, namespace="abuse_detection")
        except Exception:
            # Fallback (safe recovery)
            count = cache.get(key, namespace="abuse_detection")
            count = int(count) if count else 0
            count += 1
            cache.set(key, count, namespace="abuse_detection", ttl=300)

        # Set expiry only if first time
        if count == 1:
            cache.expire(key, namespace="abuse_detection", ttl=300)

        return count >= threshold

    @staticmethod
    def get_abuse_stats() -> Dict:
        """Get abuse detection statistics (placeholder)"""
        return {
            "blocked_ips": 0,
            "failed_auth_attempts": 0,
            "suspicious_patterns": 0,
        }
