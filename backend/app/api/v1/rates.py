"""
# Rate Management API Endpoints
"""
from fastapi import APIRouter, Depends, Query, status
from typing import Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.services import RatePlanService, SeasonalRateService, DiscountCodeService
from app.services.audit_helper import write_audit
from app.services.pricing_engine import PricingEngine
from app.models import RatePlanType, SeasonType

router = APIRouter(prefix="/rates", tags=["Rate Management"])


class RatePlanCreate(BaseModel):
    property_id: int
    name: str
    code: str
    base_rate: Decimal
    room_type_id: Optional[int] = None
    type: Optional[str] = "standard"
    plan_type: Optional[str] = None
    description: Optional[str] = None
    meal_plan: Optional[str] = None
    min_nights: int = 1
    adjustment_type: Optional[str] = None
    adjustment_value: Optional[Decimal] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None


class RatePlanUpdate(BaseModel):
    name: Optional[str] = None
    base_rate: Optional[Decimal] = None
    plan_type: Optional[str] = None
    min_nights: Optional[int] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DiscountCodeCreate(BaseModel):
    property_id: int
    code: str
    description: str
    discount_type: str
    discount_value: Decimal
    min_nights: int = 1
    min_amount: Optional[Decimal] = None
    max_uses: Optional[int] = None
    max_uses_per_guest: int = 1
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None


# === Rate Plans ===
@router.post("/plans", status_code=status.HTTP_201_CREATED, summary="Create rate plan")
async def create_rate_plan(
    data: RatePlanCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create new rate plan"""
    type_str = data.plan_type or data.type or "standard"
    try:
        plan_type = RatePlanType(type_str)
    except (ValueError, KeyError):
        plan_type = list(RatePlanType)[0]

    created_by = str(current_user.id) if hasattr(current_user, "id") else "system"
    service = RatePlanService(db)
    rate_plan = service.create_rate_plan(
        property_id=data.property_id,
        room_type_id=data.room_type_id,
        code=data.code,
        name=data.name,
        type=plan_type,
        base_rate=data.base_rate,
        description=data.description,
        adjustment_type=data.adjustment_type,
        adjustment_value=data.adjustment_value,
        min_nights=data.min_nights,
        created_by=created_by,
    )
    # Set valid_from / valid_to if provided
    if data.valid_from:
        rate_plan.valid_from = data.valid_from
    if data.valid_until:
        rate_plan.valid_to = data.valid_until
    if data.valid_from or data.valid_until:
        db.commit()
        db.refresh(rate_plan)

    write_audit(db, "create_rate_plan", "rate_plan", current_user=current_user, resource_id=rate_plan.id,
                details=f"{rate_plan.name} ({rate_plan.code})")
    return {
        "id": rate_plan.id,
        "property_id": rate_plan.property_id,
        "code": rate_plan.code,
        "name": rate_plan.name,
        "base_rate": float(rate_plan.base_rate) if rate_plan.base_rate else 0,
        "plan_type": rate_plan.plan_type.value if rate_plan.plan_type else "standard",
        "is_active": rate_plan.is_active,
        "version": rate_plan.version,
        "min_length_of_stay": rate_plan.min_length_of_stay,
        "valid_from": str(rate_plan.valid_from) if rate_plan.valid_from else None,
        "valid_to": str(rate_plan.valid_to) if rate_plan.valid_to else None,
        "created_at": rate_plan.created_at.isoformat() if rate_plan.created_at else None,
    }


@router.get("/plans", summary="Get rate plans")
async def get_rate_plans(
    property_id: int = Query(...),
    room_type_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Get rate plans for property"""
    service = RatePlanService(db)
    plans = service.get_rate_plans(property_id, room_type_id, active_only)
    return {"rate_plans": plans, "total": len(plans)}


@router.patch("/plans/{rate_plan_id}", summary="Update rate plan")
async def update_rate_plan(
    rate_plan_id: int,
    data: RatePlanUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an existing rate plan"""
    from app.models import RatePlan
    from fastapi import HTTPException
    plan = db.query(RatePlan).filter(RatePlan.id == rate_plan_id).first()
    if not plan:
        raise HTTPException(404, "Rate plan not found")
    if data.name is not None:
        plan.name = data.name
    if data.base_rate is not None:
        plan.base_rate = data.base_rate
    if data.plan_type is not None:
        try:
            plan.plan_type = RatePlanType(data.plan_type)
        except (ValueError, KeyError):
            pass
    if data.min_nights is not None:
        plan.min_length_of_stay = data.min_nights
    if data.valid_from is not None:
        plan.valid_from = data.valid_from
    if data.valid_until is not None:
        plan.valid_to = data.valid_until
    if data.description is not None:
        plan.description = data.description
    if data.is_active is not None:
        plan.is_active = data.is_active
    db.commit()
    db.refresh(plan)
    write_audit(db, "update_rate_plan", "rate_plan", current_user=current_user, resource_id=rate_plan_id,
                details=plan.name)
    return {
        "id": plan.id, "name": plan.name,
        "base_rate": float(plan.base_rate) if plan.base_rate else 0,
        "plan_type": plan.plan_type.value if plan.plan_type else "standard",
        "is_active": plan.is_active, "version": plan.version,
        "min_length_of_stay": plan.min_length_of_stay,
        "valid_from": str(plan.valid_from) if plan.valid_from else None,
        "valid_to": str(plan.valid_to) if plan.valid_to else None,
    }


@router.delete("/plans/{rate_plan_id}", status_code=204, summary="Delete rate plan")
async def delete_rate_plan(
    rate_plan_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a rate plan"""
    from app.models import RatePlan
    from fastapi import HTTPException
    plan = db.query(RatePlan).filter(RatePlan.id == rate_plan_id).first()
    if not plan:
        raise HTTPException(404, "Rate plan not found")
    plan_name = plan.name
    db.delete(plan)
    db.commit()
    write_audit(db, "delete_rate_plan", "rate_plan", current_user=current_user, resource_id=rate_plan_id,
                details=plan_name)


@router.post("/plans/{rate_plan_id}/calculate", summary="Calculate rate for dates")
async def calculate_rate(
    rate_plan_id: int,
    check_in_date: date,
    check_out_date: date,
    apply_seasonal: bool = True,
    apply_dynamic: bool = True,
    db: Session = Depends(get_db),
):
    """Calculate rate for specific date range"""
    service = RatePlanService(db)
    pricing = service.calculate_rate(
        rate_plan_id, check_in_date, check_out_date, apply_seasonal, apply_dynamic
    )
    return pricing


@router.get("/plans/available", summary="Get available rate plans")
async def get_available_rate_plans(
    property_id: int = Query(...),
    room_type_id: int = Query(...),
    check_in_date: date = Query(...),
    check_out_date: date = Query(...),
    db: Session = Depends(get_db),
):
    """Get available rate plans for dates"""
    service = RatePlanService(db)
    num_nights = (check_out_date - check_in_date).days
    plans = service.get_available_rate_plans(
        property_id, room_type_id, check_in_date, check_out_date, num_nights
    )
    return {"available_plans": plans, "total": len(plans)}


# === Seasonal Rates ===
class SeasonalRateCreate(BaseModel):
    property_id: int
    name: str
    season_type: SeasonType
    start_date: date
    end_date: date
    adjustment_type: str
    adjustment_value: Decimal
    room_type_id: Optional[int] = None
    priority: int = 0


@router.post(
    "/seasonal", status_code=status.HTTP_201_CREATED, summary="Create seasonal rate"
)
async def create_seasonal_rate(
    data: SeasonalRateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create seasonal rate"""
    created_by = str(current_user.id) if hasattr(current_user, "id") else "system"
    service = SeasonalRateService(db)
    seasonal = service.create_seasonal_rate(
        property_id=data.property_id,
        name=data.name,
        season_type=data.season_type,
        start_date=data.start_date,
        end_date=data.end_date,
        adjustment_type=data.adjustment_type,
        adjustment_value=data.adjustment_value,
        room_type_id=data.room_type_id,
        priority=data.priority,
        created_by=created_by,
    )
    return {
        "id": seasonal.id,
        "property_id": seasonal.property_id,
        "name": seasonal.name,
        "season_type": seasonal.season_type.value if seasonal.season_type else None,
        "start_date": str(seasonal.start_date) if seasonal.start_date else None,
        "end_date": str(seasonal.end_date) if seasonal.end_date else None,
        "adjustment_type": seasonal.adjustment_type,
        "adjustment_value": float(seasonal.adjustment_value)
        if seasonal.adjustment_value
        else 0,
        "is_active": seasonal.is_active,
    }


@router.get("/seasonal", summary="Get seasonal rates")
async def get_seasonal_rates(
    property_id: int = Query(...),
    room_type_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Get seasonal rates"""
    service = SeasonalRateService(db)
    rates = service.get_seasonal_rates(property_id, room_type_id, active_only)
    return {"seasonal_rates": rates, "total": len(rates)}


# === Discount Codes ===


@router.post(
    "/discounts", status_code=status.HTTP_201_CREATED, summary="Create discount code"
)
async def create_discount_code(
    data: DiscountCodeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create discount code"""
    created_by = (
        str(current_user.id) if hasattr(current_user, "id") else str(current_user)
    )
    service = DiscountCodeService(db)
    discount = service.create_discount_code(
        property_id=data.property_id,
        code=data.code,
        description=data.description,
        discount_type=data.discount_type,
        discount_value=data.discount_value,
        min_nights=data.min_nights,
        min_amount=data.min_amount,
        max_uses=data.max_uses,
        max_uses_per_guest=data.max_uses_per_guest,
        valid_from=data.valid_from,
        valid_until=data.valid_until,
        created_by=created_by,
    )
    write_audit(db, "create_discount_code", "discount_code", current_user=current_user,
                resource_id=discount.id, details=discount.code)
    return {
        "id": discount.id,
        "property_id": discount.property_id,
        "code": discount.code,
        "description": discount.description,
        "discount_type": discount.discount_type,
        "discount_value": float(discount.discount_value)
        if discount.discount_value
        else 0,
        "min_nights": discount.min_nights,
        "max_uses": discount.max_uses,
        "uses_count": discount.uses_count,
        "max_uses_per_guest": discount.max_uses_per_guest,
        "valid_from": str(discount.valid_from) if discount.valid_from else None,
        "valid_until": str(discount.valid_until) if discount.valid_until else None,
        "is_active": discount.is_active,
        "created_by": discount.created_by,
        "created_at": discount.created_at.isoformat() if discount.created_at else None,
    }


@router.post("/discounts/validate", summary="Validate discount code")
async def validate_discount_code(
    property_id: int,
    code: str,
    booking_amount: Decimal,
    num_nights: int,
    guest_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Validate discount code"""
    service = DiscountCodeService(db)
    result = service.validate_discount_code(
        property_id, code, booking_amount, num_nights, guest_id
    )
    return result


@router.get("/discounts", summary="Get discount codes")
async def get_discount_codes(
    property_id: int = Query(...),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Get all discount codes"""
    service = DiscountCodeService(db)
    codes = service.get_discount_codes(property_id, active_only)
    return {"discount_codes": codes, "total": len(codes)}


@router.post("/discounts/{discount_id}/deactivate", summary="Deactivate discount code")
async def deactivate_discount_code(
    discount_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Deactivate discount code"""
    deactivated_by = (
        str(current_user.id) if hasattr(current_user, "id") else str(current_user)
    )
    service = DiscountCodeService(db)
    code = service.deactivate_code(discount_id, deactivated_by)
    return code


@router.patch("/discounts/{discount_id}", summary="Update discount code")
async def update_discount_code(
    discount_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a discount code"""
    from app.models import DiscountCode as DiscountCodeModel
    from fastapi import HTTPException
    from decimal import Decimal as D
    dc = db.query(DiscountCodeModel).filter(DiscountCodeModel.id == discount_id).first()
    if not dc:
        raise HTTPException(404, "Discount code not found")
    if "description" in data:
        dc.description = data["description"]
    if "discount_type" in data:
        dc.discount_type = data["discount_type"]
    if "discount_value" in data:
        dc.discount_value = D(str(data["discount_value"]))
    if "min_nights" in data:
        dc.min_nights = int(data["min_nights"])
    if "valid_from" in data:
        dc.valid_from = data["valid_from"]
    if "valid_until" in data:
        dc.valid_until = data["valid_until"]
    db.commit()
    db.refresh(dc)
    write_audit(db, "update_discount_code", "discount_code", current_user=current_user,
                resource_id=discount_id, details=dc.code)
    return {
        "id": dc.id, "code": dc.code, "description": dc.description,
        "discount_type": dc.discount_type,
        "discount_value": float(dc.discount_value) if dc.discount_value else 0,
        "min_nights": dc.min_nights, "uses_count": dc.uses_count,
        "max_uses": dc.max_uses, "is_active": dc.is_active,
        "valid_from": str(dc.valid_from) if dc.valid_from else None,
        "valid_until": str(dc.valid_until) if dc.valid_until else None,
    }


@router.delete("/discounts/{discount_id}", status_code=204, summary="Delete discount code")
async def delete_discount_code(
    discount_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a discount code"""
    from app.models import DiscountCode as DiscountCodeModel
    from fastapi import HTTPException
    dc = db.query(DiscountCodeModel).filter(DiscountCodeModel.id == discount_id).first()
    if not dc:
        raise HTTPException(404, "Discount code not found")
    dc_code = dc.code
    db.delete(dc)
    db.commit()
    write_audit(db, "delete_discount_code", "discount_code", current_user=current_user,
                resource_id=discount_id, details=dc_code)


# === Pricing Engine ===
@router.post("/best-rate", summary="Calculate best available rate")
async def calculate_best_rate(
    property_id: int,
    room_type_id: int,
    check_in_date: date,
    check_out_date: date,
    num_adults: int,
    discount_code: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Calculate best available rate"""
    engine = PricingEngine(db)
    result = engine.calculate_best_rate(
        property_id,
        room_type_id,
        check_in_date,
        check_out_date,
        num_adults,
        discount_code,
    )
    return result


@router.get("/occupancy", summary="Get occupancy rate")
async def get_occupancy_rate(
    property_id: int = Query(...),
    target_date: date = Query(...),
    db: Session = Depends(get_db),
):
    """Get occupancy rate for date"""
    engine = PricingEngine(db)
    occupancy = engine.calculate_occupancy_rate(property_id, target_date)
    return occupancy


@router.post("/suggest-price", summary="Suggest optimal price")
async def suggest_optimal_price(
    property_id: int,
    room_type_id: int,
    target_date: date,
    base_rate: Decimal,
    db: Session = Depends(get_db),
):
    """Suggest optimal price based on demand"""
    engine = PricingEngine(db)
    suggestion = engine.suggest_optimal_price(
        property_id, room_type_id, target_date, base_rate
    )
    return suggestion


@router.get("/calendar", summary="Get rate calendar")
async def get_rate_calendar(
    property_id: int = Query(...),
    room_type_id: int = Query(...),
    start_date: date = Query(...),
    num_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get rate calendar for date range"""
    engine = PricingEngine(db)
    calendar = engine.get_rate_calendar(property_id, room_type_id, start_date, num_days)
    return {"calendar": calendar, "total_days": len(calendar)}
