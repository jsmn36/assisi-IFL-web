"""Time-bound access grant lifecycle.

The auth layer is free to call :meth:`active_grants_for_user` whenever
it needs to know what scopes a JIT user holds right now. The sweep job
flips expired grants to ``EXPIRED`` so the list query stays cheap.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.jit_access import (
    GrantPurpose,
    GrantScopeKind,
    GrantStatus,
    JITAccessActivity,
    JITAccessGrant,
)


class JITAccessService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- grant lifecycle ----------

    def issue(
        self,
        *,
        user_id: int,
        purpose: GrantPurpose,
        scope_kind: GrantScopeKind,
        resource_types: List[str],
        permissions: List[str],
        ttl_hours: int = 24,
        reason: Optional[str] = None,
        resource_filter: Optional[dict] = None,
        revoke_after_use: bool = False,
        granted_by: Optional[int] = None,
    ) -> JITAccessGrant:
        g = JITAccessGrant(
            user_id=user_id,
            purpose=purpose,
            scope_kind=scope_kind,
            resource_types=resource_types,
            permissions=permissions,
            reason=reason,
            resource_filter=resource_filter or {},
            revoke_after_use=revoke_after_use,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
            granted_by=granted_by,
        )
        self.db.add(g)
        self.db.commit()
        self.db.refresh(g)
        return g

    def revoke(
        self,
        grant_id: int,
        revoked_by: Optional[int] = None,
        reason: Optional[str] = None,
    ) -> Optional[JITAccessGrant]:
        g = self.db.query(JITAccessGrant).filter(JITAccessGrant.id == grant_id).first()
        if not g:
            return None
        if g.status not in (GrantStatus.ACTIVE,):
            return g
        g.status = GrantStatus.REVOKED
        g.revoked_at = datetime.now(timezone.utc)
        g.revoked_by = revoked_by
        g.revocation_reason = (reason or "")[:255]
        self.db.commit()
        self.db.refresh(g)
        return g

    def sweep_expired(self) -> int:
        now = datetime.now(timezone.utc)
        expired = (
            self.db.query(JITAccessGrant)
            .filter(JITAccessGrant.status == GrantStatus.ACTIVE)
            .filter(JITAccessGrant.expires_at < now)
            .all()
        )
        for g in expired:
            g.status = GrantStatus.EXPIRED
        self.db.commit()
        return len(expired)

    # ---------- queries ----------

    def active_grants_for_user(self, user_id: int) -> List[JITAccessGrant]:
        now = datetime.now(timezone.utc)
        return (
            self.db.query(JITAccessGrant)
            .filter(JITAccessGrant.user_id == user_id)
            .filter(JITAccessGrant.status == GrantStatus.ACTIVE)
            .filter(JITAccessGrant.expires_at > now)
            .all()
        )

    def user_has_permission(self, user_id: int, permission: str) -> bool:
        for g in self.active_grants_for_user(user_id):
            if permission in (g.permissions or []):
                return True
        return False

    def list(
        self,
        status: Optional[GrantStatus] = None,
        user_id: Optional[int] = None,
        purpose: Optional[GrantPurpose] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[JITAccessGrant], int]:
        q = self.db.query(JITAccessGrant)
        if status:
            q = q.filter(JITAccessGrant.status == status)
        if user_id is not None:
            q = q.filter(JITAccessGrant.user_id == user_id)
        if purpose:
            q = q.filter(JITAccessGrant.purpose == purpose)
        total = q.count()
        rows = (
            q.order_by(JITAccessGrant.granted_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return rows, total

    # ---------- consumption ----------

    def record_use(
        self,
        grant_id: int,
        user_id: int,
        *,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ) -> Optional[JITAccessActivity]:
        g = self.db.query(JITAccessGrant).filter(JITAccessGrant.id == grant_id).first()
        if not g or g.status != GrantStatus.ACTIVE:
            return None
        activity = JITAccessActivity(
            grant_id=grant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
        )
        self.db.add(activity)
        g.used_at = datetime.now(timezone.utc)
        if g.revoke_after_use:
            g.status = GrantStatus.CONSUMED
        self.db.commit()
        self.db.refresh(activity)
        return activity
