from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Dict
from datetime import date
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Note: Now requiring auth as per PRD.
from app.services.analytics.queries import AnalyticsQueryService
from app.api.dependencies import get_db, get_current_user
from app.services.performance_service import PerformanceService

router = APIRouter(
    prefix="/analytics", tags=["analytics"], dependencies=[Depends(get_current_user)]
)
query_service = AnalyticsQueryService()

# ========== Response Models ==========


class OccupancyData(BaseModel):
    date: date
    occupancy_percent: float
    rooms_occupied: int
    rooms_available: int


class RevenueData(BaseModel):
    date: date
    total_revenue: float = 0.0
    room_revenue: float = 0.0
    food_revenue: float = 0.0
    beverage_revenue: float = 0.0
    spa_revenue: float = 0.0
    other_revenue: float = 0.0


class KPIData(BaseModel):
    date: date
    adr: float
    revpar: float
    occupancy_percent: float


class ChannelData(BaseModel):
    channel: str
    bookings_count: int
    revenue: float
    avg_booking_value: float
    cancellation_rate: float


class BookingPatternData(BaseModel):
    day_of_week: int
    check_ins: int
    avg_lead_time: float


class KPISummary(BaseModel):
    revenue: float
    occupancy: float
    adr: float
    revpar: float
    trends: Dict[str, List[float]]


# ========== Endpoints ==========


@router.get("/occupancy", response_model=List[OccupancyData])
async def get_occupancy(
    property_id: int,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
):
    """
    # Get occupancy data for date range.
    """
    if end_date < start_date:
        raise HTTPException(400, "end_date must be after start_date")

    if (end_date - start_date).days > 365:
        raise HTTPException(400, "Date range cannot exceed 365 days")

    data = query_service.get_occupancy_data(property_id, start_date, end_date)
    return data


@router.get("/revenue", response_model=List[RevenueData])
async def get_revenue(
    property_id: int,
    start_date: date,
    end_date: date,
    granularity: str = Query("daily", regex="^(daily|weekly|monthly)$"),
):
    """
    # Get revenue data for date range.
    Granularity options: daily, weekly, monthly
    """
    if end_date < start_date:
        raise HTTPException(400, "end_date must be after start_date")

    data = query_service.get_revenue_data(
        property_id, start_date, end_date, granularity
    )
    return data


@router.get("/kpis", response_model=List[KPIData])
async def get_kpis(property_id: int, start_date: date, end_date: date):
    """
    Get key performance indicators (ADR, RevPAR, Occupancy).
    """
    if end_date < start_date:
        raise HTTPException(400, "end_date must be after start_date")

    data = query_service.get_kpi_data(property_id, start_date, end_date)
    return data


@router.get("/channels", response_model=List[ChannelData])
async def get_channel_performance(property_id: int, start_date: date, end_date: date):
    """
    # Get booking channel performance comparison.
    """
    if end_date < start_date:
        raise HTTPException(400, "end_date must be after start_date")

    data = query_service.get_channel_performance(property_id, start_date, end_date)
    # Filter out anything with no channel
    return [d for d in data if d.get("channel") is not None]


@router.get("/bookings/patterns", response_model=List[BookingPatternData])
async def get_booking_patterns(
    property_id: int, lookback_days: int = Query(90, ge=7, le=365)
):
    """
    Get booking patterns (day of week, lead time distribution).
    """
    data = query_service.get_booking_patterns(property_id, lookback_days)
    return data

    # Import performance service
    from app.services.performance_service import PerformanceService


# === Performance ===
@router.get("/performance/scorecard", summary="Get performance scorecard")
async def get_performance_scorecard(
    property_id: int = Query(...),
    target_date: date = Query(..., alias="date"),
    db: Session = Depends(get_db),
):
    """Get overall performance scorecard"""
    service = PerformanceService(db)
    scorecard = service.get_performance_scorecard(property_id, target_date)
    return scorecard


@router.get("/performance/staff", summary="Get staff performance")
async def get_staff_performance(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    """Get staff performance metrics"""
    service = PerformanceService(db)
    performance = service.get_staff_performance(property_id, start_date, end_date)
    return performance


@router.get("/performance/efficiency", summary="Get efficiency metrics")
async def get_efficiency_metrics(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    """Get operational efficiency metrics"""
    service = PerformanceService(db)
    efficiency = service.get_efficiency_metrics(property_id, start_date, end_date)
    return efficiency


@router.get("/forecast", summary="Get revenue forecast")
async def get_forecast(
    property_id: int = Query(...),
    forecast_days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """Get revenue forecast"""
    service = PerformanceService(db)
    forecast = service.get_forecast(property_id, forecast_days)
    return forecast


@router.get("/kpi-summary", response_model=KPISummary)
async def get_kpi_summary(
    property_id: int = Query(...),
    target_date: date = Query(None, alias="date")
):
    """
    Get a summary of KPIs for a specific date (defaults to today).
    Used by the main analytics dashboard.
    """
    if not target_date:
        target_date = date.today()

    data = query_service.get_kpi_summary(property_id, target_date)
    return data
