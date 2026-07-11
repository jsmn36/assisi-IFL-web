"""Corporate account service.

Adds aggregation on top of the CorporateAccount/Membership models:
total spend, active member count, top members by revenue.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Guest, Reservation, ReservationStatus
from app.models.corporate import (
    CorporateAccount,
    CorporateMembership,
    CorporateStatus,
)


class CorporateService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- CRUD ----------

    def list_accounts(
        self,
        status: Optional[CorporateStatus] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[CorporateAccount], int]:
        q = self.db.query(CorporateAccount)
        if status:
            q = q.filter(CorporateAccount.status == status)
        if search:
            term = f"%{search.lower()}%"
            q = q.filter(
                func.lower(CorporateAccount.name).like(term)
                | (CorporateAccount.tax_id.ilike(term))
            )
        total = q.count()
        rows = (
            q.order_by(CorporateAccount.name)
            .offset(offset)
            .limit(limit)
            .all()
        )
        return rows, total

    def get_account(self, account_id: int) -> Optional[CorporateAccount]:
        return (
            self.db.query(CorporateAccount)
            .filter(CorporateAccount.id == account_id)
            .first()
        )

    def create_account(self, **fields) -> CorporateAccount:
        acc = CorporateAccount(**fields)
        self.db.add(acc)
        self.db.commit()
        self.db.refresh(acc)
        return acc

    def update_account(
        self, account_id: int, **fields
    ) -> Optional[CorporateAccount]:
        acc = self.get_account(account_id)
        if not acc:
            return None
        for k, v in fields.items():
            if v is None:
                continue
            setattr(acc, k, v)
        self.db.commit()
        self.db.refresh(acc)
        return acc

    def delete_account(self, account_id: int) -> bool:
        acc = self.get_account(account_id)
        if not acc:
            return False
        self.db.delete(acc)
        self.db.commit()
        return True

    # ---------- membership ----------

    def add_member(
        self,
        account_id: int,
        guest_id: int,
        role: Optional[str] = None,
        is_primary: bool = False,
    ) -> CorporateMembership:
        # Conservative: clear any earlier active membership for this guest.
        active = (
            self.db.query(CorporateMembership)
            .filter(CorporateMembership.guest_id == guest_id)
            .filter(CorporateMembership.left_at.is_(None))
            .all()
        )
        for old in active:
            old.left_at = datetime.now(timezone.utc)
        m = CorporateMembership(
            corporate_id=account_id,
            guest_id=guest_id,
            role=role,
            is_primary=is_primary,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return m

    def remove_member(self, membership_id: int) -> bool:
        m = (
            self.db.query(CorporateMembership)
            .filter(CorporateMembership.id == membership_id)
            .first()
        )
        if not m:
            return False
        m.left_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def list_members(self, account_id: int) -> List[dict]:
        rows = (
            self.db.query(CorporateMembership, Guest)
            .join(Guest, Guest.id == CorporateMembership.guest_id)
            .filter(CorporateMembership.corporate_id == account_id)
            .order_by(CorporateMembership.joined_at.desc())
            .all()
        )
        return [
            {
                "membership_id": m.id,
                "guest_id": g.id,
                "guest_name": f"{g.first_name} {g.last_name}".strip(),
                "email": g.email,
                "role": m.role,
                "is_primary": m.is_primary,
                "joined_at": m.joined_at.isoformat() if m.joined_at else None,
                "left_at": m.left_at.isoformat() if m.left_at else None,
            }
            for m, g in rows
        ]

    # ---------- analytics ----------

    def account_spend(self, account_id: int, since_days: int = 365) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
        member_guest_ids = [
            m.guest_id
            for m in self.db.query(CorporateMembership)
            .filter(CorporateMembership.corporate_id == account_id)
            .all()
        ]
        if not member_guest_ids:
            return {
                "account_id": account_id,
                "since_days": since_days,
                "total_revenue": 0.0,
                "stays": 0,
                "active_members": 0,
                "top_members": [],
            }
        agg = (
            self.db.query(
                Reservation.guest_id,
                func.count(Reservation.id),
                func.coalesce(func.sum(Reservation.total_amount), 0),
            )
            .filter(Reservation.guest_id.in_(member_guest_ids))
            .filter(Reservation.status != ReservationStatus.CANCELLED)
            .filter(Reservation.created_at >= cutoff)
            .group_by(Reservation.guest_id)
            .all()
        )
        rows = []
        total = 0.0
        stays = 0
        for gid, c, rev in agg:
            guest = self.db.query(Guest).filter(Guest.id == gid).first()
            rev_f = float(rev or 0)
            total += rev_f
            stays += int(c)
            rows.append(
                {
                    "guest_id": gid,
                    "guest_name": (
                        f"{guest.first_name} {guest.last_name}".strip()
                        if guest
                        else f"guest#{gid}"
                    ),
                    "stays": int(c),
                    "revenue": rev_f,
                }
            )
        rows.sort(key=lambda r: r["revenue"], reverse=True)
        return {
            "account_id": account_id,
            "since_days": since_days,
            "total_revenue": total,
            "stays": stays,
            "active_members": len(member_guest_ids),
            "top_members": rows[:10],
        }
