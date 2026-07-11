"""
PerformanceService
Advanced performance metrics and benchmarking
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.services.base_service import BaseService
from app.models import (
    DailyMetrics,
    MonthlyMetrics,
    Reservation,
    ReservationStatus,
    Guest,
    Stay,
    Charge,
    HousekeepingTask,
    TaskStatus,
    MaintenanceRequest,
)


class PerformanceService(BaseService):
    """Service for performance metrics"""

    def get_performance_scorecard(self, property_id: int, target_date: date) -> Dict:
        """Get overall performance scorecard"""
        metrics = (
            self.db.query(DailyMetrics)
            .filter(
                DailyMetrics.property_id == property_id,
                DailyMetrics.business_date == target_date,
            )
            .first()
        )

        if not metrics:
            return {"error": "No metrics available"}

        occupancy_score = min(float(metrics.occupancy_rate), 100)
        target_revpar = 10000
        revenue_score = min(
            (metrics.revpar / target_revpar * 100) if metrics.revpar else 0, 100
        )

        if metrics.occupied_rooms > 0:
            housekeeping_score = min(
                (metrics.rooms_cleaned / metrics.occupied_rooms * 100), 100
            )
        else:
            housekeeping_score = 100

        if metrics.arrivals > 0:
            no_show_rate = metrics.no_shows / metrics.arrivals * 100
            no_show_score = max(100 - (no_show_rate * 10), 0)
        else:
            no_show_score = 100

        overall_score = (
            occupancy_score * 0.35
            + revenue_score * 0.35
            + housekeeping_score * 0.20
            + no_show_score * 0.10
        )

        return {
            "date": str(target_date),
            "overall_score": round(overall_score, 1),
            "scores": {
                "occupancy": {
                    "score": round(occupancy_score, 1),
                    "value": float(metrics.occupancy_rate),
                    "status": self._get_status(occupancy_score),
                },
                "revenue": {
                    "score": round(revenue_score, 1),
                    "value": (metrics.revpar / 100) if metrics.revpar else 0,
                    "status": self._get_status(revenue_score),
                },
                "housekeeping": {
                    "score": round(housekeeping_score, 1),
                    "value": metrics.rooms_cleaned,
                    "status": self._get_status(housekeeping_score),
                },
                "no_shows": {
                    "score": round(no_show_score, 1),
                    "value": metrics.no_shows,
                    "status": self._get_status(no_show_score),
                },
            },
            "status": self._get_status(overall_score),
        }

    def _get_status(self, score: float) -> str:
        """Get status from score"""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        else:
            return "needs_improvement"

    def get_staff_performance(
        self, property_id: int, start_date: date, end_date: date
    ) -> Dict:
        """Get staff performance metrics"""
        tasks = (
            self.db.query(HousekeepingTask)
            .filter(
                HousekeepingTask.property_id == property_id,
                HousekeepingTask.scheduled_date >= start_date,
                HousekeepingTask.scheduled_date <= end_date,
            )
            .all()
        )

        total_tasks = len(tasks)
        completed_tasks = len(
            [
                t
                for t in tasks
                if t.status in [TaskStatus.COMPLETED, TaskStatus.INSPECTED]
            ]
        )
        on_time_tasks = len(
            [
                t
                for t in tasks
                if t.completed_at and t.scheduled_date >= t.completed_at.date()
            ]
        )
        completed_with_time = [t for t in tasks if t.actual_duration]
        avg_completion_time = (
            sum(t.actual_duration for t in completed_with_time)
            / len(completed_with_time)
            if completed_with_time
            else 0
        )
        inspected_tasks = [t for t in tasks if t.status == TaskStatus.INSPECTED]
        passed_inspections = len([t for t in inspected_tasks if t.inspection_passed])
        inspection_pass_rate = (
            (passed_inspections / len(inspected_tasks) * 100) if inspected_tasks else 0
        )

        maintenance_requests = (
            self.db.query(MaintenanceRequest)
            .filter(
                MaintenanceRequest.property_id == property_id,
                MaintenanceRequest.created_at
                >= datetime.combine(start_date, datetime.min.time()),
                MaintenanceRequest.created_at
                <= datetime.combine(end_date, datetime.max.time()),
            )
            .all()
        )

        total_requests = len(maintenance_requests)
        completed_requests = len(
            [r for r in maintenance_requests if r.status in ["completed", "closed"]]
        )
        completed_with_time = [
            r for r in maintenance_requests if r.completed_at and r.created_at
        ]
        avg_resolution_hours = (
            sum(
                (r.completed_at - r.created_at).total_seconds() / 3600
                for r in completed_with_time
            )
            / len(completed_with_time)
            if completed_with_time
            else 0
        )

        return {
            "period": {"start": str(start_date), "end": str(end_date)},
            "housekeeping": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": round(
                    (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1
                ),
                "on_time_rate": round(
                    (on_time_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1
                ),
                "avg_completion_time": round(avg_completion_time, 1),
                "inspection_pass_rate": round(inspection_pass_rate, 1),
            },
            "maintenance": {
                "total_requests": total_requests,
                "completed_requests": completed_requests,
                "completion_rate": round(
                    (completed_requests / total_requests * 100)
                    if total_requests > 0
                    else 0,
                    1,
                ),
                "avg_resolution_hours": round(avg_resolution_hours, 1),
            },
        }

    def get_efficiency_metrics(
        self, property_id: int, start_date: date, end_date: date
    ) -> Dict:
        """Get operational efficiency metrics"""
        daily_metrics = (
            self.db.query(DailyMetrics)
            .filter(
                DailyMetrics.property_id == property_id,
                DailyMetrics.business_date >= start_date,
                DailyMetrics.business_date <= end_date,
            )
            .all()
        )

        if not daily_metrics:
            return {"error": "No data available"}

        avg_occupancy = sum(float(m.occupancy_rate) for m in daily_metrics) / len(
            daily_metrics
        )
        avg_adr = sum((m.adr or 0) for m in daily_metrics) / len(daily_metrics) / 100
        avg_revpar = (
            sum((m.revpar or 0) for m in daily_metrics) / len(daily_metrics) / 100
        )

        total_room_rev = sum(m.room_revenue for m in daily_metrics)
        total_fb_rev = sum(m.food_beverage_revenue for m in daily_metrics)
        total_other_rev = sum(m.other_revenue for m in daily_metrics)
        total_rev = total_room_rev + total_fb_rev + total_other_rev

        revenue_mix = {
            "room": round(
                (total_room_rev / total_rev * 100) if total_rev > 0 else 0, 1
            ),
            "fb": round((total_fb_rev / total_rev * 100) if total_rev > 0 else 0, 1),
            "other": round(
                (total_other_rev / total_rev * 100) if total_rev > 0 else 0, 1
            ),
        }

        total_arrivals = sum(m.arrivals for m in daily_metrics)
        total_no_shows = sum(m.no_shows for m in daily_metrics)
        no_show_rate = (
            (total_no_shows / total_arrivals * 100) if total_arrivals > 0 else 0
        )

        total_reservations = sum(m.reservations_made for m in daily_metrics)
        total_cancellations = sum(m.reservations_cancelled for m in daily_metrics)
        cancellation_rate = (
            (total_cancellations / total_reservations * 100)
            if total_reservations > 0
            else 0
        )

        total_cleaned = sum(m.rooms_cleaned for m in daily_metrics)
        total_occupied = sum(m.occupied_rooms for m in daily_metrics)
        cleaning_efficiency = (
            (total_cleaned / total_occupied * 100) if total_occupied > 0 else 0
        )

        return {
            "period": {
                "start": str(start_date),
                "end": str(end_date),
                "days": len(daily_metrics),
            },
            "occupancy": {
                "avg_occupancy_rate": round(avg_occupancy, 1),
                "avg_adr": round(avg_adr, 2),
                "avg_revpar": round(avg_revpar, 2),
            },
            "revenue_mix": revenue_mix,
            "conversion": {
                "no_show_rate": round(no_show_rate, 1),
                "cancellation_rate": round(cancellation_rate, 1),
            },
            "operations": {
                "cleaning_efficiency": round(cleaning_efficiency, 1),
                "total_rooms_cleaned": total_cleaned,
            },
        }

    def get_forecast(self, property_id: int, forecast_days: int = 30) -> Dict:
        """Get simple revenue forecast"""
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        historical_metrics = (
            self.db.query(DailyMetrics)
            .filter(
                DailyMetrics.property_id == property_id,
                DailyMetrics.business_date >= start_date,
                DailyMetrics.business_date <= end_date,
            )
            .order_by(DailyMetrics.business_date)
            .all()
        )

        if not historical_metrics or len(historical_metrics) < 7:
            return {"error": "Insufficient historical data"}

        avg_revenue = sum(m.total_revenue for m in historical_metrics) / len(
            historical_metrics
        )
        avg_occupancy = sum(float(m.occupancy_rate) for m in historical_metrics) / len(
            historical_metrics
        )

        first_week = historical_metrics[:7]
        last_week = historical_metrics[-7:]
        first_week_avg = sum(m.total_revenue for m in first_week) / len(first_week)
        last_week_avg = sum(m.total_revenue for m in last_week) / len(last_week)
        daily_trend = (last_week_avg - first_week_avg) / 30

        forecast_data = []
        for i in range(1, forecast_days + 1):
            forecast_date = end_date + timedelta(days=i)
            forecasted_revenue = avg_revenue + (daily_trend * i)
            forecast_data.append(
                {
                    "date": str(forecast_date),
                    "forecasted_revenue": round(forecasted_revenue / 100, 2),
                    "forecasted_occupancy": round(avg_occupancy, 1),
                    "confidence": "medium",
                }
            )

        return {
            "forecast_start": str(end_date + timedelta(days=1)),
            "forecast_end": str(end_date + timedelta(days=forecast_days)),
            "historical_avg_revenue": round(avg_revenue / 100, 2),
            "historical_avg_occupancy": round(avg_occupancy, 1),
            "trend": "increasing" if daily_trend > 0 else "decreasing",
            "forecast": forecast_data,
        }
