"""Guest LTV API."""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.services.guest_ltv_service import GuestLTVService

router = APIRouter(prefix="/guest-ltv", tags=["Guest LTV"])


def _serialize(g) -> dict:
    return {
        "guest_id": g.guest_id,
        "name": g.name,
        "email": g.email,
        "total_stays": g.total_stays,
        "total_revenue": g.total_revenue,
        "avg_revenue_per_stay": g.avg_revenue_per_stay,
        "first_stay_date": g.first_stay_date,
        "last_stay_date": g.last_stay_date,
        "direct_stays": g.direct_stays,
        "ota_stays": g.ota_stays,
        "primary_channel": g.primary_channel,
        "cohort": g.cohort,
    }


@router.get("")
def list_ltv(
    cohort: Optional[str] = Query(None),
    min_stays: int = Query(1, ge=1, le=100),
    limit: int = Query(200, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows, total = GuestLTVService(db).compute_all(
        limit=limit, offset=offset, min_stays=min_stays, cohort=cohort
    )
    return {
        "items": [_serialize(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/top")
def top_guests(
    n: int = Query(50, ge=1, le=500),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = GuestLTVService(db).top_n(n=n)
    return {"items": [_serialize(r) for r in rows]}


@router.get("/cohorts")
def cohort_summary(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return GuestLTVService(db).cohort_summary()


@router.get("/export.csv")
def export_csv(
    cohort: Optional[str] = Query(None),
    min_stays: int = Query(1, ge=1, le=100),
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    rows, _total = GuestLTVService(db).compute_all(
        limit=100_000, min_stays=min_stays, cohort=cohort
    )
    csv = GuestLTVService(db).export_csv(rows)
    return Response(
        content=csv,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="guest_ltv.csv"'},
    )
