"""
AnalyticsService
Trend analysis and comparative analytics
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.services.base_service import BaseService
from app.models import DailyMetrics, MonthlyMetrics


class AnalyticsService(BaseService):
    """Service for analytics and trend analysis"""

    def get_occupancy_trends(
        self,
        property_id: int,
        start_date: date,
        end_date: date,
        granularity: str = "daily",
    ) -> Dict:
        """Get occupancy trends for date range"""
        daily_metrics = (
            self.db.query(DailyMetrics)
            .filter(
                DailyMetrics.property_id == property_id,
                DailyMetrics.business_date >= start_date,
                DailyMetrics.business_date <= end_date,
            )
            .order_by(DailyMetrics.business_date)
            .all()
        )

        trend_data = [
            {
                "date": str(m.business_date),
                "occupancy_rate": float(m.occupancy_rate),
                "occupied_rooms": m.occupied_rooms,
                "available_rooms": m.available_rooms,
            }
            for m in daily_metrics
        ]

        if trend_data:
            avg_occupancy = sum(d["occupancy_rate"] for d in trend_data) / len(
                trend_data
            )
            max_occupancy = max(d["occupancy_rate"] for d in trend_data)
            min_occupancy = min(d["occupancy_rate"] for d in trend_data)
        else:
            avg_occupancy = max_occupancy = min_occupancy = 0

        return {
            "period": {
                "start": str(start_date),
                "end": str(end_date),
                "granularity": granularity,
            },
            "trend_data": trend_data,
            "statistics": {
                "avg_occupancy": round(avg_occupancy, 1),
                "max_occupancy": round(max_occupancy, 1),
                "min_occupancy": round(min_occupancy, 1),
            },
        }

    def get_revenue_trends(
        self,
        property_id: int,
        start_date: date,
        end_date: date,
        breakdown: bool = False,
    ) -> Dict:
        """Get revenue trends for date range"""
        daily_metrics = (
            self.db.query(DailyMetrics)
            .filter(
                DailyMetrics.property_id == property_id,
                DailyMetrics.business_date >= start_date,
                DailyMetrics.business_date <= end_date,
            )
            .order_by(DailyMetrics.business_date)
            .all()
        )

        trend_data = []
        for m in daily_metrics:
            entry = {
                "date": str(m.business_date),
                "total_revenue": m.total_revenue / 100,
            }
            if breakdown:
                entry["room_revenue"] = m.room_revenue / 100
                entry["fb_revenue"] = m.food_beverage_revenue / 100
                entry["other_revenue"] = m.other_revenue / 100
            trend_data.append(entry)

        totals = {
            "total_revenue": sum(m.total_revenue for m in daily_metrics) / 100,
            "room_revenue": sum(m.room_revenue for m in daily_metrics) / 100,
            "fb_revenue": sum(m.food_beverage_revenue for m in daily_metrics) / 100,
            "other_revenue": sum(m.other_revenue for m in daily_metrics) / 100,
        }

        return {
            "period": {"start": str(start_date), "end": str(end_date)},
            "trend_data": trend_data,
            "totals": totals,
        }

    def get_comparative_analysis(
        self,
        property_id: int,
        period1_start: date,
        period1_end: date,
        period2_start: date,
        period2_end: date,
    ) -> Dict:
        """Compare two periods"""

        def get_period_summary(start, end):
            metrics = (
                self.db.query(DailyMetrics)
                .filter(
                    DailyMetrics.property_id == property_id,
                    DailyMetrics.business_date >= start,
                    DailyMetrics.business_date <= end,
                )
                .all()
            )
            if not metrics:
                return {"avg_occupancy": 0, "total_revenue": 0, "avg_adr": 0}
            return {
                "avg_occupancy": round(
                    sum(float(m.occupancy_rate) for m in metrics) / len(metrics), 1
                ),
                "total_revenue": sum(m.total_revenue for m in metrics) / 100,
                "avg_adr": round(
                    sum((m.adr or 0) for m in metrics) / len(metrics) / 100, 2
                ),
            }

        p1 = get_period_summary(period1_start, period1_end)
        p2 = get_period_summary(period2_start, period2_end)

        def pct_change(old, new):
            if old == 0:
                return 0
            return round((new - old) / old * 100, 1)

        return {
            "period1": {"start": str(period1_start), "end": str(period1_end), **p1},
            "period2": {"start": str(period2_start), "end": str(period2_end), **p2},
            "changes": {
                "occupancy_change": pct_change(
                    p1["avg_occupancy"], p2["avg_occupancy"]
                ),
                "revenue_change": pct_change(p1["total_revenue"], p2["total_revenue"]),
                "adr_change": pct_change(p1["avg_adr"], p2["avg_adr"]),
            },
        }
