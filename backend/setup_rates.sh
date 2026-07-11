#!/bin/bash

cd ~/pms-hotel-desktop/backend

cat > app/api/v1/rates.py << 'EOF'
"""
Rate Management API Endpoints
"""
from fastapi import APIRouter, Depends, Query, status
from typing import Optional
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.services import (
    RatePlanService,
    SeasonalRateService,
    DiscountCodeService
)
from app.services.pricing_engine import PricingEngine
from app.models import RatePlanType, SeasonType

router = APIRouter(prefix="/rates", tags=["Rate Management"])


# === Rate Plans ===

@router.post(
    "/plans",
    status_code=status.HTTP_201_CREATED,
    summary="Create rate plan"
)
async def create_rate_plan(
    property_id: int,
    room_type_id: int,
    code: str,
    name: str,
    type: RatePlanType,
    base_rate: Decimal,
    description: Optional[str] = None,
    adjustment_type: Optional[str] = None,
    adjustment_value: Optional[Decimal] = None,
    min_nights: int = 1,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create new rate plan"""
    service = RatePlanService(db)
    rate_plan = service.create_rate_plan(
        property_id=property_id,
        room_type_id=room_type_id,
        code=code,
        name=name,
        type=type,
        base_rate=base_rate,
        description=description,
        adjustment_type=adjustment_type,
        adjustment_value=adjustment_value,
        min_nights=min_nights,
        created_by=current_user
    )
    return rate_plan


@router.get(
    "/plans",
    summary="Get rate plans"
)
async def get_rate_plans(
    property_id: int = Query(...),
    room_type_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get rate plans for property"""
    service = RatePlanService(db)
    plans = service.get_rate_plans(property_id, room_type_id, active_only)
    return {"rate_plans": plans, "total": len(plans)}


@router.post(
    "/plans/{rate_plan_id}/calculate",
    summary="Calculate rate for dates"
)
async def calculate_rate(
    rate_plan_id: int,
    check_in_date: date,
    check_out_date: date,
    apply_seasonal: bool = True,
    apply_dynamic: bool = True,
    db: Session = Depends(get_db)
):
    """Calculate rate for specific date range"""
    service = RatePlanService(db)
    pricing = service.calculate_rate(
        rate_plan_id,
        check_in_date,
        check_out_date,
        apply_seasonal,
        apply_dynamic
    )
    return pricing


@router.get(
    "/plans/available",
    summary="Get available rate plans"
)
async def get_available_rate_plans(
    property_id: int = Query(...),
    room_type_id: int = Query(...),
    check_in_date: date = Query(...),
    check_out_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """Get available rate plans for dates"""
    service = RatePlanService(db)
    num_nights = (check_out_date - check_in_date).days
    plans = service.get_available_rate_plans(
        property_id,
        room_type_id,
        check_in_date,
        check_out_date,
        num_nights
    )
    return {"available_plans": plans, "total": len(plans)}


# === Seasonal Rates ===

@router.post(
    "/seasonal",
    status_code=status.HTTP_201_CREATED,
    summary="Create seasonal rate"
)
async def create_seasonal_rate(
    property_id: int,
    name: str,
    season_type: SeasonType,
    start_date: date,
    end_date: date,
    adjustment_type: str,
    adjustment_value: Decimal,
    room_type_id: Optional[int] = None,
    priority: int = 0,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create seasonal rate"""
    service = SeasonalRateService(db)
    seasonal = service.create_seasonal_rate(
        property_id=property_id,
        name=name,
        season_type=season_type,
        start_date=start_date,
        end_date=end_date,
        adjustment_type=adjustment_type,
        adjustment_value=adjustment_value,
        room_type_id=room_type_id,
        priority=priority,
        created_by=current_user
    )
    return seasonal


@router.get(
    "/seasonal",
    summary="Get seasonal rates"
)
async def get_seasonal_rates(
    property_id: int = Query(...),
    room_type_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get seasonal rates"""
    service = SeasonalRateService(db)
    rates = service.get_seasonal_rates(property_id, room_type_id, active_only)
    return {"seasonal_rates": rates, "total": len(rates)}


# === Discount Codes ===

@router.post(
    "/discounts",
    status_code=status.HTTP_201_CREATED,
    summary="Create discount code"
)
async def create_discount_code(
    property_id: int,
    code: str,
    description: str,
    discount_type: str,
    discount_value: Decimal,
    min_nights: int = 1,
    min_amount: Optional[Decimal] = None,
    max_uses: Optional[int] = None,
    max_uses_per_guest: int = 1,
    valid_from: Optional[date] = None,
    valid_until: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create discount code"""
    service = DiscountCodeService(db)
    discount = service.create_discount_code(
        property_id=property_id,
        code=code,
        description=description,
        discount_type=discount_type,
        discount_value=discount_value,
        min_nights=min_nights,
        min_amount=min_amount,
        max_uses=max_uses,
        max_uses_per_guest=max_uses_per_guest,
        valid_from=valid_from,
        valid_until=valid_until,
        created_by=current_user
    )
    return discount


@router.post(
    "/discounts/validate",
    summary="Validate discount code"
)
async def validate_discount_code(
    property_id: int,
    code: str,
    booking_amount: Decimal,
    num_nights: int,
    guest_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Validate discount code"""
    service = DiscountCodeService(db)
    result = service.validate_discount_code(
        property_id,
        code,
        booking_amount,
        num_nights,
        guest_id
    )
    return result


@router.get(
    "/discounts",
    summary="Get discount codes"
)
async def get_discount_codes(
    property_id: int = Query(...),
    active_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get all discount codes"""
    service = DiscountCodeService(db)
    codes = service.get_discount_codes(property_id, active_only)
    return {"discount_codes": codes, "total": len(codes)}


@router.post(
    "/discounts/{discount_id}/deactivate",
    summary="Deactivate discount code"
)
async def deactivate_discount_code(
    discount_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Deactivate discount code"""
    service = DiscountCodeService(db)
    code = service.deactivate_code(discount_id, current_user)
    return code


# === Pricing Engine ===

@router.post(
    "/best-rate",
    summary="Calculate best available rate"
)
async def calculate_best_rate(
    property_id: int,
    room_type_id: int,
    check_in_date: date,
    check_out_date: date,
    num_adults: int,
    discount_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Calculate best available rate"""
    engine = PricingEngine(db)
    result = engine.calculate_best_rate(
        property_id,
        room_type_id,
        check_in_date,
        check_out_date,
        num_adults,
        discount_code
    )
    return result


@router.get(
    "/occupancy",
    summary="Get occupancy rate"
)
async def get_occupancy_rate(
    property_id: int = Query(...),
    target_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """Get occupancy rate for date"""
    engine = PricingEngine(db)
    occupancy = engine.calculate_occupancy_rate(property_id, target_date)
    return occupancy


@router.post(
    "/suggest-price",
    summary="Suggest optimal price"
)
async def suggest_optimal_price(
    property_id: int,
    room_type_id: int,
    target_date: date,
    base_rate: Decimal,
    db: Session = Depends(get_db)
):
    """Suggest optimal price based on demand"""
    engine = PricingEngine(db)
    suggestion = engine.suggest_optimal_price(
        property_id,
        room_type_id,
        target_date,
        base_rate
    )
    return suggestion


@router.get(
    "/calendar",
    summary="Get rate calendar"
)
async def get_rate_calendar(
    property_id: int = Query(...),
    room_type_id: int = Query(...),
    start_date: date = Query(...),
    num_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get rate calendar for date range"""
    engine = PricingEngine(db)
    calendar = engine.get_rate_calendar(
        property_id,
        room_type_id,
        start_date,
        num_days
    )
    return {"calendar": calendar, "total_days": len(calendar)}
EOF

# Register router in main.py
cat >> app/main.py << 'EOF'

# Import rates router
from app.api.v1 import rates

# Include rates router
app.include_router(rates.router, prefix="/api/v1")
EOF

echo "✅ Rate management API endpoints created"
