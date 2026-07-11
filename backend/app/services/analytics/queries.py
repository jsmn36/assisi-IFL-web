from datetime import date, timedelta
from typing import List, Dict, Any
from sqlalchemy import create_engine, select, text, func, case

from app.analytics_database import get_analytics_db_url
from app.models.analytics import AnalyticsDailyMetrics, ChannelPerformance, FactReservations


class AnalyticsQueryService:
    def __init__(self):
        self.engine = create_engine(get_analytics_db_url())

    def get_occupancy_data(
        self, property_id: int, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            stmt = (
                select(
                    AnalyticsDailyMetrics.metric_date.label("date"),
                    AnalyticsDailyMetrics.occupancy_percent.label("occupancy_percent"),
                    AnalyticsDailyMetrics.rooms_occupied.label("rooms_occupied"),
                    AnalyticsDailyMetrics.rooms_available.label("rooms_available"),
                )
                .where(
                    AnalyticsDailyMetrics.property_id == property_id,
                    AnalyticsDailyMetrics.metric_date >= start_date,
                    AnalyticsDailyMetrics.metric_date <= end_date,
                )
                .order_by(AnalyticsDailyMetrics.metric_date.asc())
            )

            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]

    def get_revenue_data(
        self,
        property_id: int,
        start_date: date,
        end_date: date,
        granularity: str = "daily",
    ) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            if granularity == "monthly":
                stmt = (
                    select(
                        func.date(
                            func.strftime("%Y-%m-01", AnalyticsDailyMetrics.metric_date)
                        ).label("date")
                        if self.engine.dialect.name == "sqlite"
                        else func.date_trunc("month", AnalyticsDailyMetrics.metric_date).label(
                            "date"
                        ),
                        func.sum(AnalyticsDailyMetrics.total_revenue).label("total_revenue"),
                        func.sum(AnalyticsDailyMetrics.room_revenue).label("room_revenue"),
                        func.sum(AnalyticsDailyMetrics.food_revenue).label("food_revenue"),
                        func.sum(AnalyticsDailyMetrics.beverage_revenue).label("beverage_revenue"),
                        func.sum(AnalyticsDailyMetrics.spa_revenue).label("spa_revenue"),
                        func.sum(AnalyticsDailyMetrics.other_revenue).label("other_revenue"),
                    )
                    .where(
                        AnalyticsDailyMetrics.property_id == property_id,
                        AnalyticsDailyMetrics.metric_date >= start_date,
                        AnalyticsDailyMetrics.metric_date <= end_date,
                    )
                    .group_by("date")
                    .order_by("date")
                )
            else:
                stmt = (
                    select(
                        AnalyticsDailyMetrics.metric_date.label("date"),
                        AnalyticsDailyMetrics.total_revenue,
                        AnalyticsDailyMetrics.room_revenue,
                        AnalyticsDailyMetrics.food_revenue,
                        AnalyticsDailyMetrics.beverage_revenue,
                        AnalyticsDailyMetrics.spa_revenue,
                        AnalyticsDailyMetrics.other_revenue,
                    )
                    .where(
                        AnalyticsDailyMetrics.property_id == property_id,
                        AnalyticsDailyMetrics.metric_date >= start_date,
                        AnalyticsDailyMetrics.metric_date <= end_date,
                    )
                    .order_by(AnalyticsDailyMetrics.metric_date.asc())
                )

            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]

    def get_kpi_data(
        self, property_id: int, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            stmt = (
                select(
                    AnalyticsDailyMetrics.metric_date.label("date"),
                    AnalyticsDailyMetrics.adr,
                    AnalyticsDailyMetrics.revpar,
                    AnalyticsDailyMetrics.occupancy_percent.label("occupancy_percent"),
                )
                .where(
                    AnalyticsDailyMetrics.property_id == property_id,
                    AnalyticsDailyMetrics.metric_date >= start_date,
                    AnalyticsDailyMetrics.metric_date <= end_date,
                )
                .order_by(AnalyticsDailyMetrics.metric_date.asc())
            )

            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]

    def get_channel_performance(
        self, property_id: int, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            stmt = (
                select(
                    FactReservations.channel,
                    func.count(FactReservations.reservation_id).label("bookings_count"),
                    func.sum(FactReservations.total_revenue).label("revenue"),
                    (
                        func.sum(FactReservations.total_revenue)
                        / func.count(FactReservations.reservation_id)
                    ).label("avg_booking_value"),
                    (
                        func.sum(
                            case(
                                (func.lower(FactReservations.status) == "cancelled", 1),
                                else_=0,
                            )
                        )
                        * 100.0
                        / func.count(FactReservations.reservation_id)
                    ).label("cancellation_rate"),
                )
                .where(
                    FactReservations.property_id == property_id,
                    FactReservations.check_in_date >= start_date,
                    FactReservations.check_in_date <= end_date,
                    FactReservations.channel != None,
                )
                .group_by(FactReservations.channel)
                .order_by(text("revenue DESC"))
            )

            result = conn.execute(stmt)
            return [dict(row._mapping) for row in result]

    def get_booking_patterns(
        self, property_id: int, lookback_days: int
    ) -> List[Dict[str, Any]]:
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)

        with self.engine.connect() as conn:
            stmt = select(
                FactReservations.check_in_date, FactReservations.lead_time_days
            ).where(
                FactReservations.property_id == property_id,
                FactReservations.check_in_date >= start_date,
                FactReservations.check_in_date <= end_date,
            )

            result = conn.execute(stmt)
            data = [dict(row._mapping) for row in result]

            patterns = {
                i: {"day_of_week": i, "check_ins": 0, "avg_lead_time": 0, "samples": 0}
                for i in range(7)
            }
            for row in data:
                dow = row["check_in_date"].weekday()
                patterns[dow]["check_ins"] += 1
                if row["lead_time_days"] is not None:
                    patterns[dow]["avg_lead_time"] += row["lead_time_days"]
                    patterns[dow]["samples"] += 1

            res = []
            for dow, info in patterns.items():
                if info["samples"] > 0:
                    info["avg_lead_time"] = info["avg_lead_time"] / info["samples"]
                del info["samples"]
                res.append(info)
            return res

    def get_kpi_summary(self, property_id: int, target_date: date) -> Dict[str, Any]:
        with self.engine.connect() as conn:
            stmt = select(AnalyticsDailyMetrics).where(
                AnalyticsDailyMetrics.property_id == property_id,
                AnalyticsDailyMetrics.metric_date <= target_date
            ).order_by(AnalyticsDailyMetrics.metric_date.desc()).limit(1)

            result = conn.execute(stmt).fetchone()
            if not result:
                return {
                    "revenue": 0.0,
                    "occupancy": 0.0,
                    "adr": 0.0,
                    "revpar": 0.0,
                    "trends": {"revenue": [], "occupancy": []}
                }

            trend_stmt = select(
                AnalyticsDailyMetrics.metric_date,
                AnalyticsDailyMetrics.total_revenue,
                AnalyticsDailyMetrics.occupancy_percent,
            ).where(
                AnalyticsDailyMetrics.property_id == property_id,
                AnalyticsDailyMetrics.metric_date <= target_date
            ).order_by(AnalyticsDailyMetrics.metric_date.desc()).limit(7)

            trend_rows = conn.execute(trend_stmt).fetchall()

            return {
                "revenue": float(result.total_revenue) if result.total_revenue else 0.0,
                "occupancy": float(result.occupancy_percent) if result.occupancy_percent else 0.0,
                "adr": float(result.adr) if result.adr else 0.0,
                "revpar": float(result.revpar) if result.revpar else 0.0,
                "trends": {
                    "revenue": [float(row.total_revenue) for row in reversed(trend_rows)],
                    "occupancy": [float(row.occupancy_percent) for row in reversed(trend_rows)]
                }
            }
