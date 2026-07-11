"""Compliance Calendar service — CRUD + reminder dispatch."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.compliance_calendar import (
    ComplianceItem,
    ComplianceItemCategory,
    ComplianceItemStatus,
)

logger = logging.getLogger(__name__)


class ComplianceCalendarService:
    REMINDER_THRESHOLDS_DAYS = (90, 30, 7)

    def __init__(self, db: Session):
        self.db = db

    # ---------- queries ----------

    def list(
        self,
        status: Optional[ComplianceItemStatus] = None,
        category: Optional[ComplianceItemCategory] = None,
        owner_user_id: Optional[int] = None,
        within_days: Optional[int] = None,
        include_done: bool = False,
        limit: int = 200,
        offset: int = 0,
    ) -> Tuple[List[ComplianceItem], int]:
        q = self.db.query(ComplianceItem)
        if status:
            q = q.filter(ComplianceItem.status == status)
        elif not include_done:
            q = q.filter(
                ComplianceItem.status != ComplianceItemStatus.DONE,
                ComplianceItem.status != ComplianceItemStatus.WAIVED,
            )
        if category:
            q = q.filter(ComplianceItem.category == category)
        if owner_user_id is not None:
            q = q.filter(ComplianceItem.owner_user_id == owner_user_id)
        if within_days is not None:
            horizon = datetime.now(timezone.utc) + timedelta(days=within_days)
            q = q.filter(ComplianceItem.due_date <= horizon)
        total = q.count()
        rows = (
            q.order_by(ComplianceItem.due_date.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return rows, total

    def get(self, item_id: int) -> Optional[ComplianceItem]:
        return (
            self.db.query(ComplianceItem)
            .filter(ComplianceItem.id == item_id)
            .first()
        )

    # ---------- mutations ----------

    def create(
        self,
        *,
        title: str,
        due_date: datetime,
        category: ComplianceItemCategory = ComplianceItemCategory.OTHER,
        description: Optional[str] = None,
        owner_user_id: Optional[int] = None,
        recurrence_months: Optional[int] = None,
        created_by: Optional[int] = None,
    ) -> ComplianceItem:
        item = ComplianceItem(
            title=title,
            description=description,
            category=category,
            due_date=due_date,
            owner_user_id=owner_user_id,
            recurrence_months=recurrence_months,
            created_by=created_by,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(self, item_id: int, **fields) -> Optional[ComplianceItem]:
        item = self.get(item_id)
        if not item:
            return None
        for k, v in fields.items():
            if v is None:
                continue
            setattr(item, k, v)
        self.db.commit()
        self.db.refresh(item)
        return item

    def mark_done(
        self,
        item_id: int,
        completed_by: Optional[int] = None,
        evidence_url: Optional[str] = None,
    ) -> Optional[ComplianceItem]:
        item = self.get(item_id)
        if not item:
            return None
        item.status = ComplianceItemStatus.DONE
        item.completed_at = datetime.now(timezone.utc)
        item.completed_by = completed_by
        if evidence_url:
            item.completion_evidence_url = evidence_url
        self.db.commit()
        self.db.refresh(item)

        # Auto-create the next occurrence for recurring items.
        if item.recurrence_months:
            try:
                self.create(
                    title=item.title,
                    description=item.description,
                    category=item.category,
                    due_date=item.due_date + timedelta(days=30 * item.recurrence_months),
                    owner_user_id=item.owner_user_id,
                    recurrence_months=item.recurrence_months,
                    created_by=completed_by,
                )
            except Exception:  # noqa: BLE001 — don't fail mark_done on recurrence
                logger.exception("Failed to create recurring follow-up for %s", item_id)

        return item

    def delete(self, item_id: int) -> bool:
        item = self.get(item_id)
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

    # ---------- reminders / status sweep ----------

    def sweep(self) -> dict:
        """
        Walk open items, fire reminders for each unsent threshold, and flip
        past-due items to OVERDUE. Returns counts so the scheduler can log.

        This method only updates the reminder timestamps and status fields.
        Actual notification dispatch is the caller's job — call
        :meth:`pending_reminders` to get the items that need a send.
        """
        now = datetime.now(timezone.utc)
        overdue_count = 0
        open_items = (
            self.db.query(ComplianceItem)
            .filter(
                or_(
                    ComplianceItem.status == ComplianceItemStatus.OPEN,
                    ComplianceItem.status == ComplianceItemStatus.IN_PROGRESS,
                    ComplianceItem.status == ComplianceItemStatus.OVERDUE,
                )
            )
            .all()
        )
        for item in open_items:
            if item.due_date < now and item.status != ComplianceItemStatus.OVERDUE:
                item.status = ComplianceItemStatus.OVERDUE
                overdue_count += 1
        self.db.commit()
        return {"overdue_count": overdue_count, "items_examined": len(open_items)}

    def pending_reminders(self) -> List[Tuple[ComplianceItem, int]]:
        """
        Items that have crossed a reminder threshold but not yet been sent
        a notification for that threshold. Returns ``(item, threshold_days)``
        tuples; the caller fires the notification and then records send.
        """
        now = datetime.now(timezone.utc)
        out: List[Tuple[ComplianceItem, int]] = []
        for item in (
            self.db.query(ComplianceItem)
            .filter(ComplianceItem.status != ComplianceItemStatus.DONE)
            .filter(ComplianceItem.status != ComplianceItemStatus.WAIVED)
            .all()
        ):
            days_to_due = (item.due_date - now).total_seconds() / 86400.0
            for threshold in self.REMINDER_THRESHOLDS_DAYS:
                attr = f"reminder_{threshold}d_sent_at"
                if days_to_due <= threshold and not getattr(item, attr):
                    out.append((item, threshold))
                    break  # one reminder per sweep
        return out

    def record_reminder_sent(self, item_id: int, threshold_days: int) -> None:
        item = self.get(item_id)
        if not item:
            return
        attr = f"reminder_{threshold_days}d_sent_at"
        if hasattr(item, attr):
            setattr(item, attr, datetime.now(timezone.utc))
            self.db.commit()
