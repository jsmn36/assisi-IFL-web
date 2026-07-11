"""
Day 26 reporting API.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.services.report_builder_service import ReportBuilderService

router = APIRouter(prefix="/reports", tags=["Reports"])


def _validate_window(start_date: date, end_date: date) -> None:
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")
    if (end_date - start_date).days > 366:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 366 days")


def _run_template(
    template_id: str,
    property_id: int,
    start_date: date,
    end_date: date,
    db: Session,
):
    _validate_window(start_date, end_date)
    service = ReportBuilderService(db)
    try:
        return service.generate_template_report(
            template_id, property_id, start_date, end_date
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/templates")
async def list_report_templates(db: Session = Depends(get_db)):
    service = ReportBuilderService(db)
    return {
        "templates": service.list_templates(),
        "count": len(service.TEMPLATE_CATALOG),
    }


@router.get("/templates/{template_id}")
async def get_template(template_id: str, db: Session = Depends(get_db)):
    service = ReportBuilderService(db)
    try:
        return service.get_template_metadata(template_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/templates/{template_id}/generate")
async def generate_template(
    template_id: str,
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return _run_template(template_id, property_id, start_date, end_date, db)


@router.get("/revenue/summary")
async def revenue_summary(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return _run_template("revenue_summary", property_id, start_date, end_date, db)


@router.get("/revenue/daily")
async def revenue_daily(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return _run_template("revenue_daily_trend", property_id, start_date, end_date, db)


@router.get("/revenue/sources")
async def revenue_by_sources(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return _run_template("revenue_by_source", property_id, start_date, end_date, db)


@router.get("/revenue/room-types")
async def revenue_by_room_types(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return _run_template("revenue_by_room_type", property_id, start_date, end_date, db)


@router.get("/revenue/charges")
async def revenue_by_charge_types(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return _run_template(
        "revenue_by_charge_type", property_id, start_date, end_date, db
    )


@router.get("/occupancy/summary")
async def occupancy_summary(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return _run_template("occupancy_summary", property_id, start_date, end_date, db)


@router.get("/occupancy/daily")
async def occupancy_daily(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return _run_template("occupancy_daily_trend", property_id, start_date, end_date, db)


@router.get("/occupancy/room-types")
async def occupancy_by_room_type(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return _run_template(
        "occupancy_by_room_type", property_id, start_date, end_date, db
    )


@router.get("/guests/summary")
async def guest_summary(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return _run_template("guest_acquisition", property_id, start_date, end_date, db)


@router.get("/reservations/status")
async def reservation_status_mix(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return _run_template(
        "reservation_status_mix", property_id, start_date, end_date, db
    )


@router.get("/operations/flow")
async def operations_flow(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return _run_template("checkin_checkout_flow", property_id, start_date, end_date, db)


@router.get("/financial/outstanding")
async def outstanding_balance(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return _run_template("outstanding_balance", property_id, start_date, end_date, db)


@router.get("/financial/collections")
async def payment_collections(
    property_id: int = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    return _run_template("payment_collection", property_id, start_date, end_date, db)
