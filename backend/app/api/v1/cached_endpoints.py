"""
# Cached API Endpoints
"""
import logging
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, get_db, get_if_none_match
from app.services.cache_invalidation_service import CacheInvalidationService
from app.services.cached_dashboard_service import CachedDashboardService
from app.utils.cache_headers import add_cache_headers, check_etag, generate_etag

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cached", tags=["Cached Endpoints"])


@router.get("/dashboard/stats")
async def get_cached_dashboard_stats(
    response: Response,
    if_none_match: str | None = Depends(get_if_none_match),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stats = CachedDashboardService(db).get_dashboard_stats()
    etag = generate_etag(stats)
    if if_none_match and check_etag(etag, if_none_match):
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)
    add_cache_headers(response, max_age=60, public=False, must_revalidate=True)
    response.headers["ETag"] = etag
    return stats


@router.post("/invalidate/dashboard", status_code=status.HTTP_200_OK)
async def invalidate_dashboard_cache(current_user=Depends(get_current_user)):
    removed = CacheInvalidationService.invalidate_analytics()
    return {"message": "Dashboard cache invalidated", "keys_removed": removed}


@router.get("/cache/stats")
async def get_cache_stats(current_user=Depends(get_current_user)):
    from app.core.cache import cache

    return cache.get_stats()
