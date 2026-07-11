"""
ActivityService
Track and analyze user activity
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.services.base_service import BaseService
from app.models import AuditLog, User


class ActivityService(BaseService):
    """
    Service for activity tracking

    Methods:
    - get_recent_activities: Get recent system activities
    - get_user_activities: Get activities for a user
    - get_activity_stats: Get activity statistics
    - get_login_history: Get login history
    - get_failed_logins: Get failed login attempts
    """

    def get_recent_activities(
        self,
        limit: int = 50,
        action: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[AuditLog]:
        """Get recent system activities"""
        query = self.db.query(AuditLog)
        if action:
            query = query.filter(AuditLog.action == action)
        if status:
            query = query.filter(AuditLog.status == status)
        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    def get_user_activities(
        self, user_id: int, limit: int = 50, action: Optional[str] = None
    ) -> List[AuditLog]:
        """Get activities for specific user"""
        query = self.db.query(AuditLog).filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    def get_activity_stats(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get activity statistics"""
        total = (
            self.db.query(AuditLog)
            .filter(AuditLog.created_at >= start_date, AuditLog.created_at <= end_date)
            .count()
        )

        by_action = (
            self.db.query(AuditLog.action, func.count(AuditLog.id).label("count"))
            .filter(AuditLog.created_at >= start_date, AuditLog.created_at <= end_date)
            .group_by(AuditLog.action)
            .all()
        )

        by_status = (
            self.db.query(AuditLog.status, func.count(AuditLog.id).label("count"))
            .filter(AuditLog.created_at >= start_date, AuditLog.created_at <= end_date)
            .group_by(AuditLog.status)
            .all()
        )

        by_user = (
            self.db.query(
                AuditLog.user_id,
                AuditLog.username,
                func.count(AuditLog.id).label("count"),
            )
            .filter(
                AuditLog.created_at >= start_date,
                AuditLog.created_at <= end_date,
                AuditLog.user_id.isnot(None),
            )
            .group_by(AuditLog.user_id, AuditLog.username)
            .order_by(func.count(AuditLog.id).desc())
            .limit(10)
            .all()
        )

        return {
            "total_activities": total,
            "by_action": {action: count for action, count in by_action},
            "by_status": {status: count for status, count in by_status},
            "top_users": [
                {"user_id": user_id, "username": username, "count": count}
                for user_id, username, count in by_user
            ],
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        }

    def get_login_history(self, days: int = 7, limit: int = 100) -> Dict:
        """Get login history"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        logins = (
            self.db.query(AuditLog)
            .filter(AuditLog.action == "login", AuditLog.created_at >= cutoff_date)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

        by_day = (
            self.db.query(
                func.date(AuditLog.created_at).label("date"),
                func.count(AuditLog.id).label("count"),
            )
            .filter(AuditLog.action == "login", AuditLog.created_at >= cutoff_date)
            .group_by(func.date(AuditLog.created_at))
            .all()
        )

        return {
            "logins": [
                {
                    "id": log.id,
                    "username": log.username,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat(),
                }
                for log in logins
            ],
            "by_day": {str(date): count for date, count in by_day},
            "total": len(logins),
        }

    def get_failed_logins(self, days: int = 7, limit: int = 100) -> Dict:
        """Get failed login attempts"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        failed_logins = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.action == "failed_login", AuditLog.created_at >= cutoff_date
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

        by_username = (
            self.db.query(AuditLog.username, func.count(AuditLog.id).label("count"))
            .filter(
                AuditLog.action == "failed_login", AuditLog.created_at >= cutoff_date
            )
            .group_by(AuditLog.username)
            .order_by(func.count(AuditLog.id).desc())
            .limit(10)
            .all()
        )

        by_ip = (
            self.db.query(AuditLog.ip_address, func.count(AuditLog.id).label("count"))
            .filter(
                AuditLog.action == "failed_login",
                AuditLog.created_at >= cutoff_date,
                AuditLog.ip_address.isnot(None),
            )
            .group_by(AuditLog.ip_address)
            .order_by(func.count(AuditLog.id).desc())
            .limit(10)
            .all()
        )

        return {
            "failed_logins": [
                {
                    "id": log.id,
                    "username": log.username,
                    "ip_address": log.ip_address,
                    "details": log.details,
                    "created_at": log.created_at.isoformat(),
                }
                for log in failed_logins
            ],
            "by_username": {username: count for username, count in by_username},
            "by_ip": {ip: count for ip, count in by_ip},
            "total": len(failed_logins),
        }
