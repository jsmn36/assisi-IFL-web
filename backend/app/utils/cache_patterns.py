import hashlib
import json
import logging
from functools import wraps
from typing import Callable, List, Optional

from app.core.cache import cache

logger = logging.getLogger(__name__)


def cache_result(
    ttl: int = 300,
    namespace: str = "default",
    key_prefix: str = "",
    exclude_params: Optional[List[str]] = None,
):
    """
    Advanced cache decorator with parameter control
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Ensure exclude_params is always a list
                excluded = exclude_params or []

                # Build cache key safely
                cache_data = {
                    "func": func.__name__,
                    "args": args,
                    "kwargs": {k: v for k, v in kwargs.items() if k not in excluded},
                }

                # Convert to JSON-safe string
                key_str = json.dumps(cache_data, sort_keys=True, default=str)
                key_hash = hashlib.md5(key_str.encode()).hexdigest()

                cache_key = f"{key_prefix}:{key_hash}" if key_prefix else key_hash

                # Try cache
                cached = cache.get(cache_key, namespace=namespace, deserialize="pickle")
                if cached is not None:
                    return cached

                # Execute function
                result = func(*args, **kwargs)

                # Store in cache
                cache.set(
                    cache_key, result, namespace=namespace, ttl=ttl, serialize="pickle"
                )

                return result

            except Exception:
                logger.exception(
                    "Cache wrapper failed for %s; falling back to uncached call",
                    func.__name__,
                )
                return func(*args, **kwargs)

        return wrapper

    return decorator


def invalidate_cache_pattern(pattern: str, namespace: str = "default"):
    """
    Invalidate cache by pattern
    """
    try:
        cache.delete_pattern(pattern, namespace=namespace)
    except Exception:
        logger.warning(
            "Cache pattern invalidation failed for %s in namespace %s",
            pattern,
            namespace,
            exc_info=True,
        )


def warm_cache(
    data_loader: Callable, cache_key: str, namespace: str = "default", ttl: int = 3600
):
    """
    Pre-warm cache with data
    """
    try:
        data = data_loader()
        cache.set(cache_key, data, namespace=namespace, ttl=ttl, serialize="pickle")
        return data
    except Exception:
        logger.warning("Cache warm failed for key %s", cache_key, exc_info=True)
        return None


class CacheWarmer:
    """
    Cache warming utility for frequently accessed data
    """

    @staticmethod
    def warm_dashboard_data(db):
        """Pre-warm dashboard data"""
        from app.services.cached_dashboard_service import CachedDashboardService

        service = CachedDashboardService(db)

        try:
            service.get_dashboard_stats()
            service.get_recent_reservations(10)
        except Exception:
            logger.warning("Dashboard cache warm failed", exc_info=True)

    @staticmethod
    def warm_frequently_accessed(db):
        """Warm frequently accessed data"""
        from app.models import Room
        from sqlalchemy import func

        try:
            # Cache available rooms
            available_rooms = db.query(Room).filter(Room.status == "available").all()

            cache.set(
                "available_rooms",
                available_rooms,
                namespace="rooms",
                ttl=300,
                serialize="pickle",
            )

            # Cache room count
            total_rooms = db.query(func.count(Room.id)).scalar()

            cache.set("total_rooms", total_rooms, namespace="rooms", ttl=3600)

        except Exception:
            logger.warning("Frequently-accessed cache warm failed", exc_info=True)
