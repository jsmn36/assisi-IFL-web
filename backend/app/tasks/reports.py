"""
Report Generation Background Tasks
Async report generation — requires PostgreSQL mode (Celery).
"""
from app.config import settings

if not settings.is_postgresql_mode:
    raise ImportError(
        "Celery tasks require PostgreSQL mode. Set DATABASE_URL to enable."
    )

from celery import shared_task
from app.tasks.base import DatabaseTask, CachedTask
from app.services.report_service import ReportService
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import func
import logging
from sqlalchemy import func  # ✅ FIX: missing import

logger = logging.getLogger(__name__)  # ✅ FIX: __name__ instead of name


@shared_task(bind=True, base=DatabaseTask, queue="reports")
def generate_revenue_report_task(
    self, start_date: str, end_date: str, export_format: str = "json"
):
    """Generate revenue report. export_format: 'json' or 'csv'"""
    logger.info(f"Generating revenue report: {start_date} to {end_date}")
    try:
        report_service = ReportService(self.db)
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        report = report_service.generate_revenue_report(start, end)

        if export_format == "csv":
            csv_data = report_service.export_to_csv(
                [report], f"revenue_report_{start_date}_{end_date}.csv"
            )
            return {
                "format": "csv",
                "data": csv_data,
                "filename": f"revenue_report_{start_date}_{end_date}.csv",
            }

        return {"format": "json", "data": report}

    except Exception as e:
        logger.error(f"Error generating revenue report: {e}")
        raise


@shared_task(bind=True, base=DatabaseTask, queue="reports")
def generate_occupancy_report_task(self, start_date: str, end_date: str):
    """Generate occupancy report."""
    logger.info(f"Generating occupancy report: {start_date} to {end_date}")
    try:
        report_service = ReportService(self.db)
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        return report_service.generate_occupancy_report(start, end)

    except Exception as e:
        logger.error(f"Error generating occupancy report: {e}")
        raise


@shared_task(bind=True, base=CachedTask, queue="reports")
def generate_daily_report(self):
    """Scheduled task — runs every day at 6 AM to generate daily summary."""
    logger.info("Generating daily report")

    from app.database import SessionLocal

    db = SessionLocal()
    try:
        report_service = ReportService(db)
        yesterday = date.today() - timedelta(days=1)

        revenue = report_service.generate_revenue_report(yesterday, yesterday)
        occupancy = report_service.generate_occupancy_report(yesterday, yesterday)
        guests = report_service.generate_guest_report(yesterday, yesterday)

        daily_report = {
            "date": yesterday.isoformat(),
            "revenue": revenue,
            "occupancy": occupancy,
            "guests": guests,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        from app.core.cache import cache

        cache.set(
            f"daily_report:{yesterday.isoformat()}",
            daily_report,
            namespace="reports",
            ttl=86400 * 7,
        )

        logger.info(f"Daily report generated for {yesterday}")
        return daily_report

    finally:
        db.close()


@shared_task(bind=True, base=DatabaseTask, queue="reports")
def export_reservations_task(
    self, start_date: str, end_date: str, export_format: str = "csv"
):
    """Export reservations to CSV. Runs in background for large datasets."""
    from app.models import Reservation

    logger.info(f"Exporting reservations: {start_date} to {end_date}")

    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)

        reservations = (
            self.db.query(Reservation)
            .filter(
                Reservation.check_in_date >= start, Reservation.check_in_date <= end
            )
            .all()
        )

        data = [
            {
                "confirmation_code": r.confirmation_code,
                "guest_name": r.guest_name,
                "guest_email": r.guest_email,
                "check_in_date": r.check_in_date.isoformat()
                if r.check_in_date
                else None,
                "check_out_date": r.check_out_date.isoformat()
                if r.check_out_date
                else None,
                "room_number": r.room_number,
                "status": r.status,
                "total_amount": float(r.total_amount) if r.total_amount else 0,
                "number_of_guests": r.number_of_guests,
            }
            for r in reservations
        ]

        if export_format == "csv":
            report_service = ReportService(self.db)
            csv_data = report_service.export_to_csv(
                data, f"reservations_{start_date}_{end_date}.csv"
            )
            return {
                "format": "csv",
                "data": csv_data,
                "filename": f"reservations_{start_date}_{end_date}.csv",
                "count": len(data),
            }

        return {"format": "json", "data": data, "count": len(data)}

    except Exception as e:
        logger.error(f"Error exporting reservations: {e}")
        raise


@shared_task(bind=True, base=DatabaseTask, queue="reports")
def generate_financial_summary_task(self, month: str):
    """Generate monthly financial summary. month format: YYYY-MM"""
    from app.models import Payment, Charge

    logger.info(f"Generating financial summary for {month}")

    try:
        year, month_num = map(int, month.split("-"))
        start_date = date(year, month_num, 1)

        if month_num == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month_num + 1, 1) - timedelta(days=1)

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

        total_charges = (
            self.db.query(func.sum(Charge.amount))
            .filter(Charge.created_at >= start_date, Charge.created_at <= end_date)
            .scalar()
            or 0
        )

        payment_breakdown = (
            self.db.query(
                Payment.payment_method,
                func.count(Payment.id).label("count"),
                func.sum(Payment.amount).label("total"),
            )
            .filter(
                Payment.created_at >= start_date,
                Payment.created_at <= end_date,
                Payment.status == "completed",
            )
            .group_by(Payment.payment_method)
            .all()
        )

        return {
            "month": month,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "total_revenue": float(total_revenue),
            "total_charges": float(total_charges),
            "net_revenue": float(total_revenue - total_charges),
            "payment_breakdown": [
                {"method": method, "count": count, "total": float(total)}
                for method, count, total in payment_breakdown
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error generating financial summary: {e}")
        raise
