from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import date, timezone
from typing import List, Optional
from pydantic import BaseModel, UUID4
from datetime import datetime
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.room_type import RoomType
from app.models.rate_plan import RatePlan

router = APIRouter()


class RateSnapshot(BaseModel):
    date: date
    amount: float
    currency: str
    rate_plan_id: int
    rate_plan_name: str


class RatesQueryResponse(BaseModel):
    property_id: str
    room_type_id: int
    rates: List[RateSnapshot]
    version: str
    generated_at: datetime


@router.get("/query", response_model=RatesQueryResponse)
async def query_rates(
    property_id: str, room_type_id: int, date: date, db: Session = Depends(get_db)
):
    """
    Sovereign Source of Truth.
    Queries the core PMS DB for pricing limits.
    Serves as the basis for CM Projection Publish requests.
    """
    room_type = db.query(RoomType).filter(RoomType.id == room_type_id).first()
    if not room_type:
        raise HTTPException(status_code=404, detail="Room type not found")

    rate_plan = (
        db.query(RatePlan)
        .filter(
            RatePlan.property_id == (int(property_id) if property_id.isdigit() else 1)
        )
        .first()
    )

    amount = float(room_type.base_price) if room_type.base_price else 100.00
    plan_id = rate_plan.id if rate_plan else 1
    plan_name = rate_plan.name if rate_plan else "Standard Rate"

    snapshot = RateSnapshot(
        date=date,
        amount=amount,
        currency="USD",
        rate_plan_id=plan_id,
        rate_plan_name=plan_name,
    )

    return RatesQueryResponse(
        property_id=property_id,
        room_type_id=room_type_id,
        rates=[snapshot],
        version=f"v{datetime.now(timezone.utc).strftime('%Y%m%d%H')}",
        generated_at=datetime.now(timezone.utc),
    )
