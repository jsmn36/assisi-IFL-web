"""
UserManagementService
Admin user management operations
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import AuditLog, RefreshToken, User
from app.services.auth_service import AuthService
from app.services.base_service import BaseService, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class UserManagementService(BaseService):
    """Service for admin user management"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.auth_service = AuthService(db)

    def get_users(
        self,
        skip: int = 0,
        limit: int = 50,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Dict:
        """Get users with optional filters"""
        query = self.db.query(User)

        if role:
            query = query.filter(User.role == role)

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern),
                )
            )

        total = query.count()
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

        return {"users": users, "total": total, "skip": skip, "limit": limit}

    def get_user(self, user_id: int) -> User:
        """Get single user by ID"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    def update_user(
        self,
        user_id: int,
        updated_by: str,
        username: Optional[str] = None,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        role: Optional[str] = None,
    ) -> User:
        """Update user details"""
        user = self.get_user(user_id)

        # Optimized duplicate check
        if username and username != user.username:
            if self.db.query(User.id).filter(User.username == username).first():
                raise ValueError("Username already exists")
            user.username = username

        if email and email != user.email:
            if self.db.query(User.id).filter(User.email == email).first():
                raise ValueError("Email already exists")
            user.email = email

        # Update fields safely
        for field, value in {
            "first_name": first_name,
            "last_name": last_name,
            "phone": phone,
            "role": role,
        }.items():
            if value is not None:
                setattr(user, field, value)

        user.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(user)

        self._log_audit(
            "update_user",
            "user",
            user_id,
            updated_by,
            details=f"Updated user {user.username}",
        )
        return user

    def deactivate_user(self, user_id: int, deactivated_by: str) -> User:
        """Deactivate user account"""
        user = self.get_user(user_id)
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)

        # Revoke all refresh tokens
        self.db.query(RefreshToken).filter(RefreshToken.user_id == user_id).update(
            {"revoked": True}, synchronize_session=False
        )

        self.db.commit()
        self.db.refresh(user)

        self._log_audit(
            "deactivate_user",
            "user",
            user_id,
            deactivated_by,
            details=f"Deactivated user {user.username}",
        )
        return user

    def activate_user(self, user_id: int, activated_by: str) -> User:
        """Activate user account"""
        user = self.get_user(user_id)
        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(user)

        self._log_audit(
            "activate_user",
            "user",
            user_id,
            activated_by,
            details=f"Activated user {user.username}",
        )
        return user

    def delete_user(self, user_id: int, deleted_by: str) -> bool:
        """Physical deletion of user record"""
        user = self.get_user(user_id)
        if user.id == 1 or user.username == "admin":
             raise ValueError("Cannot delete system administrator")
            
        self.db.delete(user)
        self.db.commit()
        
        self._log_audit(
            "delete_user",
            "user",
            user_id,
            deleted_by,
            details=f"Permanently deleted user {user.username}",
        )
        return True

    def reset_password(self, user_id: int, new_password: str, reset_by: str) -> User:
        """Admin reset of user password"""
        user = self.get_user(user_id)
        user.hashed_password = get_password_hash(new_password)
        user.last_password_change = datetime.now(timezone.utc)
        user.failed_login_attempts = 0
        user.locked_until = None
        user.updated_at = datetime.now(timezone.utc)

        # Revoke all refresh tokens
        self.db.query(RefreshToken).filter(RefreshToken.user_id == user_id).update(
            {"revoked": True}, synchronize_session=False
        )

        self.db.commit()
        self.db.refresh(user)

        self._log_audit(
            "reset_password",
            "user",
            user_id,
            reset_by,
            details=f"Admin reset password for {user.username}",
        )
        return user

    def unlock_account(self, user_id: int, unlocked_by: str) -> User:
        """Unlock locked user account"""
        user = self.get_user(user_id)
        user.failed_login_attempts = 0
        user.locked_until = None
        user.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(user)

        self._log_audit(
            "unlock_account",
            "user",
            user_id,
            unlocked_by,
            details=f"Unlocked account for {user.username}",
        )
        return user

    def get_user_activity(self, user_id: int, limit: int = 50) -> List[AuditLog]:
        """Get user activity logs"""
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_user_stats(self, user_id: int) -> Dict:
        """Get statistics for a user"""
        user = self.get_user(user_id)

        logs = self.db.query(AuditLog).filter(AuditLog.user_id == user_id)

        total_activities = logs.count()
        login_count = logs.filter(AuditLog.action == "login").count()
        failed_login_count = logs.filter(AuditLog.action == "failed_login").count()

        last_login = (
            logs.filter(AuditLog.action == "login")
            .order_by(AuditLog.created_at.desc())
            .first()
        )

        active_sessions = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
            .count()
        )

        return {
            "user_id": user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "total_activities": total_activities,
            "login_count": login_count,
            "failed_login_count": failed_login_count,
            "last_login": last_login.created_at.isoformat() if last_login else None,
            "active_sessions": active_sessions,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_password_change": user.last_password_change.isoformat()
            if user.last_password_change
            else None,
            "failed_login_attempts": user.failed_login_attempts,
            "is_locked": user.is_locked() if hasattr(user, "is_locked") else None,
        }

    def get_role_stats(self) -> Dict:
        """Get user statistics by role"""
        role_counts = (
            self.db.query(User.role, func.count(User.id)).group_by(User.role).all()
        )

        active_role_counts = (
            self.db.query(User.role, func.count(User.id))
            .filter(User.is_active.is_(True))
            .group_by(User.role)
            .all()
        )

        total_by_role = {role: count for role, count in role_counts}
        active_by_role = {role: count for role, count in active_role_counts}

        total_users = sum(total_by_role.values())
        active_users = sum(active_by_role.values())
        inactive_users = total_users - active_users

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "total_by_role": total_by_role,
            "active_by_role": active_by_role,
        }

    def _log_audit(
        self,
        action: str,
        resource_type: str,
        resource_id: int,
        performed_by: str,
        details: str = None,
    ):
        """Log audit entry"""
        try:
            audit = AuditLog(
                username=performed_by,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                status="success",
                details=details,
            )
            self.db.add(audit)
            self.db.commit()
        except Exception:
            logger.exception(
                "Failed to write audit entry action=%s resource=%s:%s",
                action,
                resource_type,
                resource_id,
            )
            try:
                self.db.rollback()
            except Exception:
                logger.debug("Audit rollback also failed", exc_info=True)
