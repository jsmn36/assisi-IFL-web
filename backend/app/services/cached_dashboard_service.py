"""
Cached Dashboard Service
"""
import logging
from typing import Any
from sqlalchemy.orm import Session
from app.core.cache import cache

logger = logging.getLogger(__name__)
DASHBOARD_STATS_KEY = "dashboard:stats:global"
DASHBOARD_STATS_TTL = 60


class CachedDashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_stats(self) -> dict[str, Any]:
        cached = cache.get(DASHBOARD_STATS_KEY)
        if cached is not None:
            logger.debug("Dashboard stats: cache HIT")
            return cached
        logger.debug("Dashboard stats: cache MISS")
        stats = self._query_stats()
        cache.set(DASHBOARD_STATS_KEY, stats, ttl=DASHBOARD_STATS_TTL)
        return stats

    def _query_stats(self) -> dict[str, Any]:
        try:
            from app.models import User

            total_users = self.db.query(User).count()
        except Exception:
            total_users = 0
        return {"total_users": total_users}
