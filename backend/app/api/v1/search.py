"""
Search API Endpoints
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.dependencies import get_db, get_current_user
from app.services.search_service import SearchService
from app.services.filter_service import FilterService
from app.models import User

router = APIRouter(prefix="/search", tags=["Search"])


# Request Models
class SavedSearchRequest(BaseModel):
    name: str
    entity_type: str
    search_params: dict
    description: Optional[str] = None
    is_default: bool = False
    is_public: bool = False


class FilterRequest(BaseModel):
    field: str
    operator: str
    value: str


# === Global Search ===
@router.get("/global", summary="Global search")
async def global_search(
    q: str = Query(..., min_length=2),
    entities: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Global search across all entities"""
    service = SearchService(db)
    entity_list = entities.split(",") if entities else None
    results = service.global_search(
        query=q, user_id=current_user.id, entities=entity_list, limit=limit
    )
    return results


# === Entity-specific Search ===
@router.get("/reservations", summary="Search reservations")
async def search_reservations(
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search reservations"""
    service = SearchService(db)
    results = service.search_reservations(
        query=q or "",
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    if q:
        service.track_search(
            user_id=current_user.id,
            entity_type="reservation",
            search_term=q,
            result_count=len(results),
        )
    return {
        "results": [
            {
                "id": r.id,
                "confirmation_code": r.confirmation_code,
                "guest_name": r.guest_name,
                "guest_email": r.guest_email,
                "room_number": r.room_number,
                "status": r.status,
                "check_in_date": r.check_in_date.isoformat()
                if r.check_in_date
                else None,
                "check_out_date": r.check_out_date.isoformat()
                if r.check_out_date
                else None,
            }
            for r in results
        ],
        "total": len(results),
    }


@router.get("/guests", summary="Search guests")
async def search_guests(
    q: Optional[str] = Query(None),
    guest_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search guests"""
    service = SearchService(db)
    results = service.search_guests(query=q or "", guest_type=guest_type, limit=limit)
    return {
        "results": [
            {
                "id": g.id,
                "first_name": g.first_name,
                "last_name": g.last_name,
                "email": g.email,
                "phone": g.phone,
                "guest_type": g.guest_type,
            }
            for g in results
        ],
        "total": len(results),
    }


# === Saved Searches ===
@router.post("/saved", summary="Save search")
async def save_search(
    search_data: SavedSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save search configuration"""
    service = SearchService(db)
    saved = service.save_search(
        user_id=current_user.id,
        name=search_data.name,
        entity_type=search_data.entity_type,
        search_params=search_data.search_params,
        description=search_data.description,
        is_default=search_data.is_default,
        is_public=search_data.is_public,
    )
    return {
        "id": saved.id,
        "name": saved.name,
        "entity_type": saved.entity_type,
        "is_default": saved.is_default,
    }


@router.get("/saved", summary="Get saved searches")
async def get_saved_searches(
    entity_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's saved searches"""
    service = SearchService(db)
    searches = service.get_saved_searches(
        user_id=current_user.id, entity_type=entity_type
    )
    return {
        "searches": [
            {
                "id": s.id,
                "name": s.name,
                "entity_type": s.entity_type,
                "search_params": s.search_params,
                "description": s.description,
                "is_default": s.is_default,
                "is_public": s.is_public,
                "use_count": s.use_count,
                "last_used": s.last_used.isoformat() if s.last_used else None,
            }
            for s in searches
        ]
    }


@router.post("/saved/{search_id}/use", summary="Use saved search")
async def use_saved_search(
    search_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Use saved search"""
    service = SearchService(db)
    search = service.use_saved_search(search_id, current_user.id)
    if not search:
        return {"error": "Search not found"}
    return {"id": search.id, "name": search.name, "search_params": search.search_params}


@router.delete("/saved/{search_id}", summary="Delete saved search")
async def delete_saved_search(
    search_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete saved search"""
    service = SearchService(db)
    deleted = service.delete_saved_search(search_id, current_user.id)
    return {"success": deleted}


# === Search History ===
@router.get("/history", summary="Get search history")
async def get_search_history(
    entity_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's search history"""
    service = SearchService(db)
    history = service.get_search_history(
        user_id=current_user.id, entity_type=entity_type, limit=limit
    )
    return {
        "history": [
            {
                "id": h.id,
                "entity_type": h.entity_type,
                "search_term": h.search_term,
                "result_count": h.result_count,
                "created_at": h.created_at.isoformat(),
            }
            for h in history
        ]
    }


# === Suggestions ===
@router.get("/suggestions", summary="Get search suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2),
    entity_type: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get search suggestions"""
    service = SearchService(db)
    suggestions = service.get_search_suggestions(
        user_id=current_user.id, entity_type=entity_type, partial_query=q
    )
    return {"suggestions": suggestions}


# === Quick Filters ===
@router.get("/quick-filters", summary="Get quick filters")
async def get_quick_filters(
    entity_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get quick filters"""
    service = SearchService(db)
    filters = service.get_quick_filters(
        entity_type=entity_type, user_role=current_user.role
    )
    return {
        "filters": [
            {
                "id": f.id,
                "name": f.name,
                "entity_type": f.entity_type,
                "filter_config": f.filter_config,
                "icon": f.icon,
                "color": f.color,
            }
            for f in filters
        ]
    }


# === Filter Metadata ===
@router.get("/filter/operators", summary="Get filter operators")
async def get_filter_operators(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get available filter operators"""
    service = FilterService(db)
    return {"operators": service.get_filter_operators()}


@router.get("/filter/fields/{entity_type}", summary="Get filterable fields")
async def get_filterable_fields(
    entity_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get filterable fields for entity"""
    service = FilterService(db)
    return {"fields": service.get_filterable_fields(entity_type)}

# === Search Analytics ===
@router.get("/analytics/summary", summary="Search analytics summary")
async def search_analytics_summary(
    since_days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SearchService(db)
    return service.analytics_summary(since_days=since_days)


@router.get("/analytics/top-queries", summary="Top searched terms")
async def search_analytics_top_queries(
    since_days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    entity_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SearchService(db)
    return {"queries": service.top_queries(since_days=since_days, limit=limit, entity_type=entity_type)}


@router.get("/analytics/zero-result", summary="Zero-result searches")
async def search_analytics_zero_result(
    since_days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=200),
    min_hits: int = Query(2, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SearchService(db)
    return {"queries": service.zero_result_queries(since_days=since_days, limit=limit, min_hits=min_hits)}


@router.get("/analytics/volume-by-hour", summary="Search volume by hour-of-day")
async def search_analytics_volume(
    since_days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SearchService(db)
    return {"buckets": service.search_volume_by_hour(since_days=since_days)}


@router.get("/analytics/user-patterns", summary="Per-user search patterns")
async def search_analytics_user_patterns(
    since_days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SearchService(db)
    return {"users": service.user_search_patterns(since_days=since_days, limit=limit)}


@router.get("/analytics/saved-filter-usage", summary="Saved filter usage")
async def search_analytics_saved_filter_usage(
    since_days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = SearchService(db)
    return {"filters": service.saved_filter_usage(since_days=since_days, limit=limit)}

