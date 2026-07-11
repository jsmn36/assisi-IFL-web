"""
Authentication Service
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.core.tenant_context import bypass_tenant_filter, get_tenant
from app.models import AuditLog, RefreshToken, User, UserTenant
from app.models.tenant import DEFAULT_TENANT_ID


class AuthService:
    """Service for authentication"""

    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30

    def __init__(self, db: Session):
        self.db = db

    def commit(self):
        self.db.commit()

    def refresh(self, obj):
        self.db.refresh(obj)

    # ─── Memberships ───────────────────────────────────────────────────────
    def get_memberships(self, user_id: int) -> List[UserTenant]:
        """Return all active tenant memberships for a user (bypass row filter)."""
        with bypass_tenant_filter():
            return (
                self.db.query(UserTenant)
                .filter(UserTenant.user_id == user_id)
                .all()
            )

    def _select_default_membership(
        self, memberships: List[UserTenant]
    ) -> Optional[UserTenant]:
        if not memberships:
            return None
        for m in memberships:
            if m.is_default:
                return m
        return memberships[0]

    # ─── Token minting ────────────────────────────────────────────────────
    def _issue_tokens(
        self,
        user: User,
        tenant_id: int,
        role: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[str, str]:
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "user_id": user.id,
                "role": role,
                "tenant_id": tenant_id,
                "is_superadmin": bool(getattr(user, "is_superuser", False)),
            }
        )
        refresh_token_str = create_refresh_token(
            data={
                "sub": str(user.id),
                "user_id": user.id,
                "tenant_id": tenant_id,
            }
        )

        rt = RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(rt)
        self.commit()
        return access_token, refresh_token_str

    # ─── Authenticate ─────────────────────────────────────────────────────
    def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[Optional[User], Optional[str], Optional[str], List[UserTenant]]:
        """Authenticate user and (when unambiguous) issue tokens.

        Returns ``(user, access_token, refresh_token, memberships)``.
          - On bad credentials/locked/inactive: ``(None, None, None, [])``.
          - When user has exactly one membership: tokens are issued and
            scoped to that tenant.
          - When user has multiple memberships: tokens are NOT issued; the
            caller must hit ``/auth/select-tenant`` with one of the returned
            memberships.
        """
        with bypass_tenant_filter():
            user = (
                self.db.query(User)
                .filter((User.username == username) | (User.email == username))
                .first()
            )

        if not user:
            self.log_audit(
                username=username,
                action="failed_login",
                status="failure",
                details="User not found",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return None, None, None, []

        if user.is_locked():
            self.log_audit(
                user_id=user.id,
                username=username,
                action="failed_login",
                status="failure",
                details="Account locked",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return None, None, None, []

        if not user.is_active:
            self.log_audit(
                user_id=user.id,
                username=username,
                action="failed_login",
                status="failure",
                details="Account inactive",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return None, None, None, []

        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= self.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.now(timezone.utc) + timedelta(
                    minutes=self.LOCKOUT_DURATION_MINUTES
                )
                self.commit()
                self.log_audit(
                    user_id=user.id,
                    username=username,
                    action="account_locked",
                    status="success",
                    details=f"Account locked after {self.MAX_LOGIN_ATTEMPTS} failed attempts",
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            else:
                self.commit()

            self.log_audit(
                user_id=user.id,
                username=username,
                action="failed_login",
                status="failure",
                details=f"Invalid password. Attempt {user.failed_login_attempts}/{self.MAX_LOGIN_ATTEMPTS}",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return None, None, None, []

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc)
        self.commit()

        memberships = self.get_memberships(user.id)

        if len(memberships) == 0:
            # Auto-provision a membership in the default tenant so the user
            # can still log in. This preserves the pre-multi-tenant behavior.
            membership = UserTenant(
                user_id=user.id,
                tenant_id=DEFAULT_TENANT_ID,
                role=user.role or "staff",
                is_default=True,
            )
            with bypass_tenant_filter():
                self.db.add(membership)
                self.commit()
            memberships = [membership]

        if len(memberships) > 1:
            self.log_audit(
                user_id=user.id,
                username=username,
                action="login_pending_tenant_select",
                status="success",
                details=f"User has {len(memberships)} memberships",
                ip_address=ip_address,
                user_agent=user_agent,
            )
            return user, None, None, memberships

        membership = memberships[0]
        access_token, refresh_token_str = self._issue_tokens(
            user,
            tenant_id=membership.tenant_id,
            role=membership.role,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.log_audit(
            user_id=user.id,
            username=username,
            action="login",
            status="success",
            details=f"Successful login (tenant={membership.tenant_id})",
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return user, access_token, refresh_token_str, memberships

    def select_tenant(
        self,
        user_id: int,
        tenant_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[Optional[User], Optional[str], Optional[str]]:
        """Mint tokens scoped to ``tenant_id`` if the user has membership."""
        with bypass_tenant_filter():
            membership = (
                self.db.query(UserTenant)
                .filter(
                    UserTenant.user_id == user_id,
                    UserTenant.tenant_id == tenant_id,
                )
                .first()
            )
            user = self.db.query(User).filter(User.id == user_id).first()

        if not user or not user.is_active or membership is None:
            return None, None, None

        access_token, refresh_token_str = self._issue_tokens(
            user,
            tenant_id=membership.tenant_id,
            role=membership.role,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.log_audit(
            user_id=user.id,
            username=user.username,
            action="tenant_selected",
            status="success",
            details=f"Issued tenant-bound tokens (tenant={tenant_id})",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return user, access_token, refresh_token_str

    # ─── User CRUD ────────────────────────────────────────────────────────
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "staff",
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        created_by: Optional[str] = None,
        tenant_id: Optional[int] = None,
    ) -> User:
        """Create new user and seed a UserTenant membership."""
        with bypass_tenant_filter():
            existing = (
                self.db.query(User)
                .filter((User.username == username) | (User.email == email))
                .first()
            )

        if existing:
            raise ValueError("Username or email already exists")

        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
            first_name=first_name,
            last_name=last_name,
            created_by=created_by,
            last_password_change=datetime.now(timezone.utc),
        )

        self.db.add(user)
        self.commit()
        self.refresh(user)

        target_tenant = tenant_id or get_tenant() or DEFAULT_TENANT_ID
        membership = UserTenant(
            user_id=user.id,
            tenant_id=target_tenant,
            role=role,
            is_default=True,
        )
        with bypass_tenant_filter():
            self.db.add(membership)
            self.commit()

        self.log_audit(
            username=created_by,
            action="create_user",
            status="success",
            details=f"Created user {username} (role={role}, tenant={target_tenant})",
        )

        return user

    def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> bool:
        """Change user password"""
        with bypass_tenant_filter():
            user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            return False

        if not verify_password(old_password, user.hashed_password):
            self.log_audit(
                user_id=user.id,
                username=user.username,
                action="failed_password_change",
                status="failure",
                details="Invalid current password",
            )
            return False

        user.hashed_password = get_password_hash(new_password)
        user.last_password_change = datetime.now(timezone.utc)

        self.db.query(RefreshToken).filter(RefreshToken.user_id == user_id).update(
            {"revoked": True}
        )

        self.commit()

        self.log_audit(
            user_id=user.id,
            username=user.username,
            action="password_change",
            status="success",
            details="Password changed successfully",
        )

        return True

    def logout(self, user_id: int, refresh_token: str) -> bool:
        """Logout user"""
        token = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id, RefreshToken.token == refresh_token
            )
            .first()
        )

        if token:
            token.revoked = True
            self.commit()

        with bypass_tenant_filter():
            user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            self.log_audit(
                user_id=user.id,
                username=user.username,
                action="logout",
                status="success",
                details="User logged out",
            )

        return True

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token, preserving the tenant binding."""
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            return None

        token = (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token == refresh_token)
            .first()
        )

        if not token or not token.is_valid():
            return None

        with bypass_tenant_filter():
            user = self.db.query(User).filter(User.id == token.user_id).first()
        if not user or not user.is_active:
            return None

        # Preserve tenant binding from the refresh token. If absent (legacy
        # token issued before tenant claim rollout), re-resolve from the
        # user's default membership.
        tenant_id = payload.get("tenant_id")
        if tenant_id is None:
            memberships = self.get_memberships(user.id)
            membership = self._select_default_membership(memberships)
            if membership is None:
                return None
            tenant_id = membership.tenant_id
            role = membership.role
        else:
            with bypass_tenant_filter():
                membership = (
                    self.db.query(UserTenant)
                    .filter(
                        UserTenant.user_id == user.id,
                        UserTenant.tenant_id == int(tenant_id),
                    )
                    .first()
                )
            if membership is None:
                return None
            role = membership.role

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "user_id": user.id,
                "role": role,
                "tenant_id": int(tenant_id),
                "is_superadmin": bool(getattr(user, "is_superuser", False)),
            }
        )

        return access_token

    def log_audit(
        self,
        action: str,
        status: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        tenant_id: Optional[int] = None,
    ) -> AuditLog:
        """Log audit event. Default tenant ensures pre-auth events still land."""
        effective_tenant = tenant_id or get_tenant() or DEFAULT_TENANT_ID
        audit_log = AuditLog(
            tenant_id=effective_tenant,
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
        )

        self.db.add(audit_log)
        self.commit()
        self.refresh(audit_log)

        return audit_log
