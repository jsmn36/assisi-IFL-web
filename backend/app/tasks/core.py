"""
Core Background Tasks
In PostgreSQL mode, these are Celery tasks.
In SQLite mode, this module is not imported — use APScheduler.
"""
from app.config import settings

if not settings.is_postgresql_mode:
    raise ImportError(
        "Celery tasks require PostgreSQL mode. " "Set DATABASE_URL to enable."
    )

from celery import shared_task
from app.tasks.base import DatabaseTask, CachedTask
from app.database import SessionLocal
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, base=DatabaseTask)
def test_task(self, message: str):
    """Test task to verify Celery is working."""
    logger.info(f"Test task executed: {message}")
    return {
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": self.request.id,
    }


@shared_task(bind=True, base=DatabaseTask)
def process_reservation_confirmation(self, reservation_id: int):
    """Process reservation confirmation: status update, audit log, email queue."""
    from app.models import Reservation
    from app.services.audit_service import AuditService

    logger.info(f"Processing confirmation for reservation {reservation_id}")
    try:
        reservation = (
            self.db.query(Reservation).filter(Reservation.id == reservation_id).first()
        )

        if not reservation:
            logger.error(f"Reservation {reservation_id} not found")
            return {"success": False, "error": "Reservation not found"}

        if reservation.status == "pending":
            reservation.status = "confirmed"
            self.db.commit()

        audit = AuditService(self.db)
        audit.log_action(
            user_id=None,
            action="reservation_confirmed",
            entity_type="reservation",
            entity_id=reservation_id,
            details={"confirmation_code": reservation.confirmation_code},
        )

        from app.tasks.emails import send_confirmation_email

        send_confirmation_email.delay(reservation_id)

        return {
            "success": True,
            "reservation_id": reservation_id,
            "confirmation_code": reservation.confirmation_code,
        }

    except Exception as e:
        logger.error(f"Error processing confirmation: {e}")
        self.db.rollback()
        raise


@shared_task(bind=True, base=CachedTask)
def calculate_revenue_metrics(self, start_date: str, end_date: str):
    """Calculate revenue metrics for a date range. Cached to prevent duplicate runs."""
    from app.models import Reservation
    from sqlalchemy import func

    logger.info(f"Calculating revenue metrics: {start_date} to {end_date}")
    db = SessionLocal()
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        reservation_count = (
            db.query(func.count(Reservation.id))
            .filter(
                Reservation.check_in_date >= start.date(),
                Reservation.check_in_date <= end.date(),
            )
            .scalar()
            or 0
        )

        return {
            "start_date": start_date,
            "end_date": end_date,
            "reservation_count": reservation_count,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()


@shared_task(bind=True)
def cleanup_expired_sessions(self):
    """Clean up expired user sessions (TTL handled by Redis automatically)."""
    logger.info("Cleaning up expired sessions")
    return {"success": True, "timestamp": datetime.now(timezone.utc).isoformat()}
