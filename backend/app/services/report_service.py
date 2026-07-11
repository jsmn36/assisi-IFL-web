"""
Report Generation Service
Generate various reports and exports
"""
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional
import csv
import io
from sqlalchemy import func


class ReportService:
    """
    Service for generating reports

    Supports:
    - Revenue reports
    - Occupancy reports
    - Guest reports
    - Financial summaries
    - CSV/PDF exports
    """

    def __init__(self, db: Session):
        self.db = db

    def generate_revenue_report(self, start_date: date, end_date: date) -> Dict:
        from app.models import Payment, Reservation

        total_revenue = (
            self.db.query(func.sum(Payment.amount))
            .filter(
                Payment.created_at >= start_date,
                Payment.created_at <= end_date,
                Payment.status == "completed",
            )
            .scalar()
            or 0
        )

        revenue_by_method = (
            self.db.query(
                Payment.payment_method, func.sum(Payment.amount).label("total")
            )
            .filter(
                Payment.created_at >= start_date,
                Payment.created_at <= end_date,
                Payment.status == "completed",
            )
            .group_by(Payment.payment_method)
            .all()
        )

        transaction_count = (
            self.db.query(func.count(Payment.id))
            .filter(
                Payment.created_at >= start_date,
                Payment.created_at <= end_date,
                Payment.status == "completed",
            )
            .scalar()
            or 0
        )

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "total_revenue": float(total_revenue),
            "transaction_count": transaction_count,
            "average_transaction": float(total_revenue / transaction_count)
            if transaction_count > 0
            else 0,
            "revenue_by_method": [
                {"method": method, "amount": float(amount)}
                for method, amount in revenue_by_method
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def generate_occupancy_report(self, start_date: date, end_date: date) -> Dict:
        from app.models import Reservation, Room

        total_rooms = self.db.query(func.count(Room.id)).scalar() or 1
        days = (end_date - start_date).days + 1
        occupancy_data = []

        for i in range(days):
            current_date = start_date + timedelta(days=i)

            occupied = (
                self.db.query(func.count(Reservation.id))
                .filter(
                    Reservation.check_in_date <= current_date,
                    Reservation.check_out_date > current_date,
                    Reservation.status.in_(["confirmed", "checked_in"]),
                )
                .scalar()
                or 0
            )

            occupancy_rate = (occupied / total_rooms) * 100
            occupancy_data.append(
                {
                    "date": current_date.isoformat(),
                    "occupied_rooms": occupied,
                    "occupancy_rate": round(occupancy_rate, 2),
                }
            )

        avg_occupancy = (
            sum(d["occupancy_rate"] for d in occupancy_data) / days if days > 0 else 0
        )

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "total_rooms": total_rooms,
            "average_occupancy": round(avg_occupancy, 2),
            "daily_occupancy": occupancy_data,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def generate_guest_report(self, start_date: date, end_date: date) -> Dict:
        from app.models import Guest, Reservation

        new_guests = (
            self.db.query(func.count(Guest.id))
            .filter(Guest.created_at >= start_date, Guest.created_at <= end_date)
            .scalar()
            or 0
        )

        total_reservations = (
            self.db.query(func.count(Reservation.id))
            .filter(
                Reservation.check_in_date >= start_date,
                Reservation.check_in_date <= end_date,
            )
            .scalar()
            or 0
        )

        avg_guests = (
            self.db.query(func.avg(Reservation.number_of_guests))
            .filter(
                Reservation.check_in_date >= start_date,
                Reservation.check_in_date <= end_date,
            )
            .scalar()
            or 0
        )

        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "new_guests": new_guests,
            "total_reservations": total_reservations,
            "average_guests_per_reservation": round(float(avg_guests), 2),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def export_to_csv(self, data: List[Dict], filename: str) -> str:
        if not data:
            return ""

        output = io.StringIO()
        fieldnames = list(data[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

        return output.getvalue()
