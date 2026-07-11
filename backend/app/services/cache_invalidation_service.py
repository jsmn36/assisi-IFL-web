"""
Cache Invalidation Service
"""
import logging
from typing import Optional
from app.core.cache import cache

logger = logging.getLogger(__name__)
NS_ANALYTICS = "analytics:"
NS_DASHBOARD = "dashboard:"
NS_USER = "user:"


class CacheInvalidationService:
    @staticmethod
    def invalidate_analytics() -> int:
        removed = cache.delete_pattern(f"{NS_ANALYTICS}*")
        removed += cache.delete_pattern(f"{NS_DASHBOARD}*")
        logger.info("Invalidated analytics+dashboard (%d keys)", removed)
        return removed

    @staticmethod
    def invalidate_user(user_id: Optional[int] = None) -> int:
        pattern = f"{NS_USER}{user_id}:*" if user_id else f"{NS_USER}*"
        removed = cache.delete_pattern(pattern)
        logger.info("Invalidated user cache pattern=%s (%d keys)", pattern, removed)
        return removed

    @staticmethod
    def invalidate_key(key: str) -> bool:
        return cache.delete(key)
