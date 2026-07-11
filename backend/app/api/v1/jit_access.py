"""JIT (Just-in-Time) access grant API."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.models.jit_access import (
    GrantPurpose,
    GrantScopeKind,
    GrantStatus,
)
from app.services.jit_access_service import JITAccessService

router = APIRouter(prefix="/jit-access", tags=["JIT Access"])


def _serialize(g) -> dict:
    return {
        "id": g.id,
        "user_id": g.user_id,
        "purpose": g.purpose.value,
        "scope_kind": g.scope_kind.value,
        "resource_types": g.resource_types,
        "resource_filter": g.resource_filter,
        "permissions": g.permissions,
        "reason": g.reason,
        "status": g.status.value,
        "granted_at": g.granted_at.isoformat() if g.granted_at else None,
        "granted_by": g.granted_by,
        "expires_at": g.expires_at.isoformat() if g.expires_at else None,
        "revoke_after_use": g.revoke_after_use,
        "used_at": g.used_at.isoformat() if g.used_at else None,
        "revoked_at": g.revoked_at.isoformat() if g.revoked_at else None,
        "revoked_by": g.revoked_by,
        "revocation_reason": g.revocation_reason,
    }


class IssueIn(BaseModel):
    user_id: int
    purpose: GrantPurpose = GrantPurpose.OTHER
    scope_kind: GrantScopeKind = GrantScopeKind.READ
    resource_types: List[str] = []
    permissions: List[str] = []
    ttl_hours: int = Field(24, ge=1, le=24 * 30)
    reason: Optional[str] = None
    resource_filter: Optional[dict] = None
    revoke_after_use: bool = False


class RevokeIn(BaseModel):
    reason: Optional[str] = None


class RecordUseIn(BaseModel):
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None


@router.post("/grants", status_code=201)
def issue_grant(
    payload: IssueIn,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    g = JITAccessService(db).issue(
        granted_by=current_user.id, **payload.model_dump()
    )
    return _serialize(g)


@router.get("/grants")
def list_grants(
    status: Optional[GrantStatus] = None,
    user_id: Optional[int] = None,
    purpose: Optional[GrantPurpose] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows, total = JITAccessService(db).list(
        status=status, user_id=user_id, purpose=purpose, limit=limit, offset=offset
    )
    return {
        "items": [_serialize(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/grants/{grant_id}/revoke")
def revoke_grant(
    grant_id: int,
    payload: RevokeIn,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    g = JITAccessService(db).revoke(
        grant_id, revoked_by=current_user.id, reason=payload.reason
    )
    if not g:
        raise HTTPException(status_code=404, detail="Grant not found")
    return _serialize(g)


@router.post("/grants/{grant_id}/use")
def record_use(
    grant_id: int,
    payload: RecordUseIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    a = JITAccessService(db).record_use(
        grant_id,
        user_id=current_user.id,
        action=payload.action,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
    )
    if not a:
        raise HTTPException(status_code=404, detail="Grant not active or not found")
    return {"id": a.id, "occurred_at": a.occurred_at.isoformat()}


@router.post("/sweep-expired")
def sweep_expired(
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    return {"expired": JITAccessService(db).sweep_expired()}


@router.get("/me/active")
def my_active_grants(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {
        "items": [
            _serialize(g)
            for g in JITAccessService(db).active_grants_for_user(current_user.id)
        ]
    }
