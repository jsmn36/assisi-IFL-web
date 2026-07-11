from app.config import settings

if not settings.is_postgresql_mode:
    raise ImportError(
        "Celery tasks require PostgreSQL mode. Set DATABASE_URL to enable."
    )

from celery import shared_task
from app.tasks.base import DatabaseTask
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_task_results():
    """Remove stale Celery result entries from Redis."""
    logger.info("Running cleanup_old_task_results")
    return {"success": True, "timestamp": datetime.now(timezone.utc).isoformat()}


@shared_task(bind=True, base=DatabaseTask)
def cleanup_old_audit_logs(self, days: int = 90):
    """Delete gate-execution history rows older than ``days``.

    Retained for backward compatibility — wired against
    GateExecutionHistory, not AuditLog. The real AuditLog retention task
    is :func:`purge_audit_logs` below.
    """
    from app.models.gate_execution_history import GateExecutionHistory

    logger.info(f"Cleaning up gate-execution history older than {days} days")
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        old_logs_count = (
            self.db.query(GateExecutionHistory)
            .filter(GateExecutionHistory.executed_at < cutoff)
            .delete(synchronize_session=False)
        )
        self.db.commit()

        return {
            "success": True,
            "old_logs_count": old_logs_count,
            "days": days,
            "cutoff_date": cutoff.isoformat(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error cleaning up gate-execution history: {e}")
        self.db.rollback()
        raise


@shared_task(bind=True, base=DatabaseTask)
def purge_audit_logs(self, days: int | None = None):
    """Delete AuditLog rows older than ``days`` (defaults to settings).

    Runs across every active tenant via :func:`run_for_each_tenant` so the
    SQLAlchemy session filter doesn't need to be bypassed. Pass
    ``days=0`` to opt out at task-call time even if the global setting is
    nonzero.
    """
    from app.config import settings
    from app.core.tenant_loop import run_for_each_tenant
    from app.models import AuditLog

    if days is None:
        days = settings.AUDIT_RETENTION_DAYS

    if not days or days <= 0:
        logger.info("AuditLog retention disabled (days=%s); skipping", days)
        return {"success": True, "skipped": True, "days": days}

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    def _purge_one_tenant() -> int:
        deleted = (
            self.db.query(AuditLog)
            .filter(AuditLog.created_at < cutoff)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return int(deleted or 0)

    deleted_per_tenant: dict[int, int] = {}

    def _runner() -> None:
        from app.core.tenant_context import get_tenant

        tid = get_tenant()
        if tid is None:
            return
        deleted_per_tenant[tid] = _purge_one_tenant()

    run_for_each_tenant(_runner, job_name="purge_audit_logs")

    total = sum(deleted_per_tenant.values())
    logger.info(
        "AuditLog retention complete: deleted %d rows across %d tenants (cutoff=%s)",
        total,
        len(deleted_per_tenant),
        cutoff.isoformat(),
    )
    return {
        "success": True,
        "total_deleted": total,
        "per_tenant": deleted_per_tenant,
        "days": days,
        "cutoff_date": cutoff.isoformat(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@shared_task(bind=True, base=DatabaseTask)
def update_room_status(self):
    """Update room statuses based on current reservations."""
    from app.models.room import Room, OccupancyState

    logger.info("Updating room statuses")
    try:
        rooms = self.db.query(Room).all()
        total_rooms = len(rooms)
        updated = 0

        for room in rooms:
            old_state = room.occupancy_state
            if room.occupancy_state is None:
                room.occupancy_state = OccupancyState.VACANT
                if room.occupancy_state != old_state:
                    updated += 1

        self.db.commit()

        return {
            "success": True,
            "total_rooms": total_rooms,
            "updated": updated,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error updating room status: {e}")
        self.db.rollback()
        raise


@shared_task(bind=True, base=DatabaseTask)
def calculate_daily_statistics(self):
    """Calculate daily hotel statistics."""
    from app.models.reservation import Reservation
    from app.models.room import Room
    from app.models.charge import Charge
    from sqlalchemy import func

    logger.info("Calculating daily statistics")
    try:
        today = datetime.now(timezone.utc).date()

        total_rooms = self.db.query(func.count(Room.id)).scalar() or 0

        checkins_today = (
            self.db.query(func.count(Reservation.id))
            .filter(
                Reservation.check_in_date == today, Reservation.status == "confirmed"
            )
            .scalar()
            or 0
        )

        checkouts_today = (
            self.db.query(func.count(Reservation.id))
            .filter(Reservation.check_out_date == today)
            .scalar()
            or 0
        )

        occupied_rooms = (
            self.db.query(func.count(Reservation.id))
            .filter(
                Reservation.check_in_date <= today,
                Reservation.check_out_date > today,
                Reservation.status == "confirmed",
            )
            .scalar()
            or 0
        )

        occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0

        revenue_today = (
            self.db.query(func.sum(Charge.amount))
            .filter(Charge.charge_date == today)
            .scalar()
            or 0
        )

        return {
            "date": today.isoformat(),
            "occupancy_rate": round(occupancy_rate, 2),
            "revenue_today": float(revenue_today),
            "checkins_today": checkins_today,
            "checkouts_today": checkouts_today,
            "occupied_rooms": occupied_rooms,
            "total_rooms": total_rooms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Error calculating daily statistics: {e}")
        raise
