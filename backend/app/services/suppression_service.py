"""Suppression list service.

A single place to ask "should this recipient receive a message?". The
notification service must call :meth:`SuppressionService.is_suppressed`
before every outbound send.

Suppression checks fall back to ``ALL`` channel matches — if a recipient
is suppressed for ``ALL``, both email and SMS sends are blocked.
"""
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.suppression import (
    Suppression,
    SuppressionChannel,
    SuppressionReason,
    normalize_address,
)


class SuppressionService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- queries ----------

    def is_suppressed(
        self, address: str, channel: SuppressionChannel = SuppressionChannel.EMAIL
    ) -> Optional[Suppression]:
        """Return the matching Suppression row or None."""
        if not address:
            return None
        norm = normalize_address(address, channel)
        # Match the explicit channel OR an ``ALL`` block on the same address.
        row = (
            self.db.query(Suppression)
            .filter(Suppression.address == norm)
            .filter(
                Suppression.channel.in_(
                    [channel, SuppressionChannel.ALL]
                )
            )
            .first()
        )
        return row

    def filter_addresses(
        self,
        addresses: List[str],
        channel: SuppressionChannel = SuppressionChannel.EMAIL,
    ) -> Tuple[List[str], List[str]]:
        """Partition a recipient list into ``(allowed, suppressed)``."""
        allowed: List[str] = []
        blocked: List[str] = []
        for a in addresses:
            if self.is_suppressed(a, channel):
                blocked.append(a)
            else:
                allowed.append(a)
        return allowed, blocked

    def list(
        self,
        channel: Optional[SuppressionChannel] = None,
        reason: Optional[SuppressionReason] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Suppression], int]:
        q = self.db.query(Suppression)
        if channel:
            q = q.filter(Suppression.channel == channel)
        if reason:
            q = q.filter(Suppression.reason == reason)
        if search:
            term = f"%{search.lower()}%"
            q = q.filter(Suppression.address.ilike(term))
        total = q.count()
        rows = q.order_by(Suppression.created_at.desc()).offset(offset).limit(limit).all()
        return rows, total

    # ---------- mutations ----------

    def add(
        self,
        address: str,
        channel: SuppressionChannel = SuppressionChannel.EMAIL,
        reason: SuppressionReason = SuppressionReason.MANUAL,
        notes: Optional[str] = None,
        source: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> Suppression:
        """Add (idempotent — returns existing row on duplicate)."""
        norm = normalize_address(address, channel)
        existing = (
            self.db.query(Suppression)
            .filter(Suppression.address == norm)
            .filter(Suppression.channel == channel)
            .first()
        )
        if existing:
            return existing
        row = Suppression(
            address=norm,
            channel=channel,
            reason=reason,
            notes=notes,
            source=source,
            created_by=created_by,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def remove(self, suppression_id: int) -> bool:
        row = self.db.query(Suppression).filter(Suppression.id == suppression_id).first()
        if not row:
            return False
        self.db.delete(row)
        self.db.commit()
        return True

    def bulk_import(
        self,
        addresses: List[str],
        channel: SuppressionChannel,
        reason: SuppressionReason = SuppressionReason.MANUAL,
        source: Optional[str] = "bulk-import",
        created_by: Optional[int] = None,
    ) -> int:
        """Bulk-add. Skips duplicates silently."""
        added = 0
        for a in addresses:
            norm = normalize_address(a, channel)
            if not norm:
                continue
            existing = (
                self.db.query(Suppression)
                .filter(Suppression.address == norm)
                .filter(Suppression.channel == channel)
                .first()
            )
            if existing:
                continue
            self.db.add(
                Suppression(
                    address=norm,
                    channel=channel,
                    reason=reason,
                    source=source,
                    created_by=created_by,
                )
            )
            added += 1
        self.db.commit()
        return added
