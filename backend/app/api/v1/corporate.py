"""Corporate accounts API."""
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.models.corporate import CorporateStatus
from app.services.corporate_service import CorporateService

router = APIRouter(prefix="/corporate", tags=["Corporate Accounts"])


def _serialize_account(a) -> dict:
    return {
        "id": a.id,
        "name": a.name,
        "legal_name": a.legal_name,
        "tax_id": a.tax_id,
        "industry": a.industry,
        "address": a.address,
        "phone": a.phone,
        "email": a.email,
        "website": a.website,
        "status": a.status.value,
        "credit_limit": float(a.credit_limit) if a.credit_limit is not None else None,
        "payment_terms_days": a.payment_terms_days,
        "discount_pct": float(a.discount_pct or 0),
        "rate_code": a.rate_code,
        "notes": a.notes,
        "primary_contact_user_id": a.primary_contact_user_id,
        "account_manager_user_id": a.account_manager_user_id,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


class AccountIn(BaseModel):
    name: str = Field(..., min_length=2)
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    status: CorporateStatus = CorporateStatus.ACTIVE
    credit_limit: Optional[Decimal] = None
    payment_terms_days: Optional[int] = None
    discount_pct: Optional[Decimal] = None
    rate_code: Optional[str] = None
    notes: Optional[str] = None
    primary_contact_user_id: Optional[int] = None
    account_manager_user_id: Optional[int] = None


class MemberIn(BaseModel):
    guest_id: int
    role: Optional[str] = None
    is_primary: bool = False


@router.get("/accounts")
def list_accounts(
    status: Optional[CorporateStatus] = None,
    search: Optional[str] = Query(None, min_length=1),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows, total = CorporateService(db).list_accounts(
        status=status, search=search, limit=limit, offset=offset
    )
    return {
        "items": [_serialize_account(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/accounts/{account_id}")
def get_account(
    account_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    acc = CorporateService(db).get_account(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize_account(acc)


@router.post("/accounts", status_code=201)
def create_account(
    payload: AccountIn,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    a = CorporateService(db).create_account(**payload.model_dump())
    return _serialize_account(a)


@router.patch("/accounts/{account_id}")
def update_account(
    account_id: int,
    payload: AccountIn,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    a = CorporateService(db).update_account(
        account_id, **payload.model_dump(exclude_unset=True)
    )
    if not a:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize_account(a)


@router.delete("/accounts/{account_id}", status_code=204)
def delete_account(
    account_id: int,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if not CorporateService(db).delete_account(account_id):
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/accounts/{account_id}/members")
def list_members(
    account_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"items": CorporateService(db).list_members(account_id)}


@router.post("/accounts/{account_id}/members", status_code=201)
def add_member(
    account_id: int,
    payload: MemberIn,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    m = CorporateService(db).add_member(
        account_id,
        payload.guest_id,
        role=payload.role,
        is_primary=payload.is_primary,
    )
    return {
        "membership_id": m.id,
        "guest_id": m.guest_id,
        "joined_at": m.joined_at.isoformat() if m.joined_at else None,
    }


@router.delete("/members/{membership_id}", status_code=204)
def remove_member(
    membership_id: int,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    if not CorporateService(db).remove_member(membership_id):
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/accounts/{account_id}/spend")
def account_spend(
    account_id: int,
    since_days: int = Query(365, ge=1, le=3650),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CorporateService(db).account_spend(account_id, since_days=since_days)
