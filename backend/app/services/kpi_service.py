"""
KPIService
Calculates and stores KPI metrics
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.services.base_service import BaseService
from app.models import (
    DailyMetrics,
    MonthlyMetrics,
    Room,
    RoomStatus,
    Stay,
    StayStatus,
    Reservation,
    ReservationStatus,
    Charge,
    ChargeType,
    HousekeepingTask,
    TaskStatus,
    Property,
)


def _safe_decimal(value) -> Decimal:
    return Decimal(value or 0)


class KPIService(BaseService):
    """Service for KPI calculations"""

    def calculate_daily_metrics(
        self, property_id: int, business_date: date
    ) -> DailyMetrics:
        """Calculate and store daily metrics"""
        existing = (
            self.db.query(DailyMetrics)
            .filter(
                DailyMetrics.property_id == property_id,
                DailyMetrics.business_date == business_date,
            )
            .first()
        )

        total_rooms = (
            self.db.query(Room)
            .filter(Room.property_id == property_id, Room.is_active.is_(True))
            .count()
        )

        occupied_rooms = (
            self.db.query(Stay)
            .filter(
                Stay.property_id == property_id,
                Stay.check_in_date <= business_date,
                Stay.check_out_date > business_date,
                Stay.status == StayStatus.CHECKED_IN,
            )
            .count()
        )

        out_of_order = (
            self.db.query(Room)
            .filter(
                Room.property_id == property_id, Room.status == RoomStatus.OUT_OF_ORDER
            )
            .count()
        )

        available_rooms = max(total_rooms - occupied_rooms - out_of_order, 0)
        occupancy_rate = (
            Decimal(occupied_rooms) / Decimal(total_rooms) * 100
            if total_rooms > 0
            else Decimal("0.00")
        )

        revenue_data = (
            self.db.query(
                func.coalesce(func.sum(Charge.total_amount), 0), Charge.charge_type
            )
            .filter(
                Charge.property_id == property_id, Charge.charge_date == business_date
            )
            .group_by(Charge.charge_type)
            .all()
        )

        room_revenue = Decimal(0)
        fb_revenue = Decimal(0)
        other_revenue = Decimal(0)

        for amount, charge_type in revenue_data:
            amount = _safe_decimal(amount)
            if charge_type == ChargeType.ROOM:
                room_revenue += amount
            elif charge_type in [ChargeType.FOOD, ChargeType.BEVERAGE]:
                fb_revenue += amount
            else:
                other_revenue += amount

        total_revenue = room_revenue + fb_revenue + other_revenue
        adr = int(room_revenue / occupied_rooms) if occupied_rooms > 0 else 0
        revpar = int(room_revenue / total_rooms) if total_rooms > 0 else 0

        arrivals = (
            self.db.query(Stay)
            .filter(
                Stay.property_id == property_id, Stay.check_in_date == business_date
            )
            .count()
        )

        departures = (
            self.db.query(Stay)
            .filter(
                Stay.property_id == property_id, Stay.check_out_date == business_date
            )
            .count()
        )

        stayovers = max(occupied_rooms - arrivals, 0)

        no_shows = (
            self.db.query(Reservation)
            .filter(
                Reservation.property_id == property_id,
                Reservation.check_in_date == business_date,
                Reservation.status == ReservationStatus.NO_SHOW,
            )
            .count()
        )

        reservations_made = (
            self.db.query(Reservation)
            .filter(
                Reservation.property_id == property_id,
                func.date(Reservation.created_at) == business_date,
            )
            .count()
        )

        reservations_cancelled = (
            self.db.query(Reservation)
            .filter(
                Reservation.property_id == property_id,
                Reservation.status == ReservationStatus.CANCELLED,
                func.date(Reservation.updated_at) == business_date,
            )
            .count()
        )

        rooms_cleaned = (
            self.db.query(HousekeepingTask)
            .filter(
                HousekeepingTask.property_id == property_id,
                HousekeepingTask.scheduled_date == business_date,
                HousekeepingTask.status.in_(
                    [TaskStatus.COMPLETED, TaskStatus.INSPECTED]
                ),
            )
            .count()
        )

        rooms_inspected = (
            self.db.query(HousekeepingTask)
            .filter(
                HousekeepingTask.property_id == property_id,
                HousekeepingTask.scheduled_date == business_date,
                HousekeepingTask.status == TaskStatus.INSPECTED,
            )
            .count()
        )

        data = dict(
            total_rooms=total_rooms,
            occupied_rooms=occupied_rooms,
            available_rooms=available_rooms,
            out_of_order_rooms=out_of_order,
            occupancy_rate=occupancy_rate.quantize(Decimal("0.01")),
            room_revenue=int(room_revenue),
            food_beverage_revenue=int(fb_revenue),
            other_revenue=int(other_revenue),
            total_revenue=int(total_revenue),
            adr=adr,
            revpar=revpar,
            arrivals=arrivals,
            departures=departures,
            stayovers=stayovers,
            no_shows=no_shows,
            reservations_made=reservations_made,
            reservations_cancelled=reservations_cancelled,
            rooms_cleaned=rooms_cleaned,
            rooms_inspected=rooms_inspected,
            updated_at=datetime.now(timezone.utc),
        )

        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            self.commit()
            self.refresh(existing)
            return existing

        metrics = DailyMetrics(
            property_id=property_id, business_date=business_date, **data
        )
        self.db.add(metrics)
        self.commit()
        self.refresh(metrics)
        return metrics

    def get_daily_metrics(
        self, property_id: int, start_date: date, end_date: date
    ) -> List[DailyMetrics]:
        """Get daily metrics for date range"""
        return (
            self.db.query(DailyMetrics)
            .filter(
                DailyMetrics.property_id == property_id,
                DailyMetrics.business_date >= start_date,
                DailyMetrics.business_date <= end_date,
            )
            .order_by(DailyMetrics.business_date)
            .all()
        )

    def calculate_monthly_metrics(
        self, property_id: int, year: int, month: int
    ) -> MonthlyMetrics:
        """Calculate monthly metrics from daily data"""
        from calendar import monthrange

        last_day = monthrange(year, month)[1]
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)

        daily = self.get_daily_metrics(property_id, start_date, end_date)
        if not daily:
            return None

        avg_occupancy = sum(float(m.occupancy_rate) for m in daily) / len(daily)
        total_room_nights_sold = sum(m.occupied_rooms for m in daily)
        total_room_nights_available = sum(m.total_rooms for m in daily)
        total_room_revenue = sum(m.room_revenue for m in daily)
        total_fb_revenue = sum(m.food_beverage_revenue for m in daily)
        total_other_revenue = sum(m.other_revenue for m in daily)
        total_revenue = sum(m.total_revenue for m in daily)
        avg_adr = int(sum((m.adr or 0) for m in daily) / len(daily))
        avg_revpar = int(sum((m.revpar or 0) for m in daily) / len(daily))
        total_arrivals = sum(m.arrivals for m in daily)
        total_departures = sum(m.departures for m in daily)
        total_no_shows = sum(m.no_shows for m in daily)
        total_reservations = sum(m.reservations_made for m in daily)
        total_cancellations = sum(m.reservations_cancelled for m in daily)
        cancellation_rate = (
            Decimal(total_cancellations) / Decimal(total_reservations) * 100
            if total_reservations > 0
            else Decimal("0.00")
        )

        existing = (
            self.db.query(MonthlyMetrics)
            .filter(
                MonthlyMetrics.property_id == property_id,
                MonthlyMetrics.year == year,
                MonthlyMetrics.month == month,
            )
            .first()
        )

        data = dict(
            avg_occupancy_rate=Decimal(str(round(avg_occupancy, 2))),
            total_room_nights_sold=total_room_nights_sold,
            total_room_nights_available=total_room_nights_available,
            total_room_revenue=total_room_revenue,
            total_food_beverage_revenue=total_fb_revenue,
            total_other_revenue=total_other_revenue,
            total_revenue=total_revenue,
            avg_adr=avg_adr,
            avg_revpar=avg_revpar,
            total_arrivals=total_arrivals,
            total_departures=total_departures,
            total_no_shows=total_no_shows,
            total_reservations=total_reservations,
            total_cancellations=total_cancellations,
            cancellation_rate=cancellation_rate.quantize(Decimal("0.01")),
            updated_at=datetime.now(timezone.utc),
        )

        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            self.commit()
            self.refresh(existing)
            return existing

        monthly = MonthlyMetrics(
            property_id=property_id, year=year, month=month, **data
        )
        self.db.add(monthly)
        self.commit()
        self.refresh(monthly)
        return monthly

    def get_kpi_summary(self, property_id: int, target_date: date) -> Dict:
        """Get KPI summary for a date"""
        metrics = self.calculate_daily_metrics(property_id, target_date)
        return {
            "date": str(target_date),
            "occupancy": {
                "rate": float(metrics.occupancy_rate),
                "occupied_rooms": metrics.occupied_rooms,
                "available_rooms": metrics.available_rooms,
                "total_rooms": metrics.total_rooms,
            },
            "revenue": {
                "total": metrics.total_revenue / 100,
                "room": metrics.room_revenue / 100,
                "fb": metrics.food_beverage_revenue / 100,
                "other": metrics.other_revenue / 100,
            },
            "adr": {"value": (metrics.adr or 0) / 100},
            "revpar": {"value": (metrics.revpar or 0) / 100},
            "guests": {
                "arrivals": metrics.arrivals,
                "departures": metrics.departures,
                "stayovers": metrics.stayovers,
                "no_shows": metrics.no_shows,
            },
        }
