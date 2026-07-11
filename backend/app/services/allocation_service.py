"""Allocation pool engine.

For a given (room_type_id, night), the engine computes:

  reserved          = confirmed/checked-in reservations covering the night
  active_holds      = holds with night_from <= night <= night_to and not released
  base_sellable     = total_inventory - safety_stock - quarantine - reserved - active_holds + inbound
  channel_sellable  = min(base_sellable, channel_buffer.max_sellable) per channel

The booking flow asks ``safe_to_sell(room_type_id, night, channel)``
before promising any room. Returns 0 when the answer is "do not sell".
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date, timedelta
from typing import Dict, Iterable, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models import Reservation, ReservationStatus
from app.models.allocation import Allocation, ChannelBuffer, Hold, HoldReason


@dataclass
class AvailabilitySnapshot:
    room_type_id: int
    night: _date
    total_inventory: int
    safety_stock: int
    inbound: int
    quarantine: int
    reserved: int
    holds: int
    base_sellable: int
    by_channel: Dict[str, int]


class AllocationService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- allocation CRUD ----------

    def upsert(
        self,
        *,
        room_type_id: int,
        night: _date,
        total_inventory: int,
        safety_stock: int = 0,
        inbound: int = 0,
        quarantine: int = 0,
    ) -> Allocation:
        row = (
            self.db.query(Allocation)
            .filter(Allocation.room_type_id == room_type_id)
            .filter(Allocation.night == night)
            .first()
        )
        if not row:
            row = Allocation(room_type_id=room_type_id, night=night)
            self.db.add(row)
        row.total_inventory = total_inventory
        row.safety_stock = safety_stock
        row.inbound = inbound
        row.quarantine = quarantine
        self.db.commit()
        self.db.refresh(row)
        return row

    def get(
        self, room_type_id: int, night: _date
    ) -> Optional[Allocation]:
        return (
            self.db.query(Allocation)
            .filter(Allocation.room_type_id == room_type_id)
            .filter(Allocation.night == night)
            .first()
        )

    def set_channel_buffer(
        self,
        *,
        room_type_id: int,
        night: _date,
        channel: str,
        max_sellable: int,
    ) -> ChannelBuffer:
        row = (
            self.db.query(ChannelBuffer)
            .filter(ChannelBuffer.room_type_id == room_type_id)
            .filter(ChannelBuffer.night == night)
            .filter(ChannelBuffer.channel == channel)
            .first()
        )
        if not row:
            row = ChannelBuffer(
                room_type_id=room_type_id,
                night=night,
                channel=channel,
                max_sellable=0,
            )
            self.db.add(row)
        row.max_sellable = max_sellable
        self.db.commit()
        self.db.refresh(row)
        return row

    # ---------- holds ----------

    def create_hold(
        self,
        *,
        room_type_id: int,
        night_from: _date,
        night_to: _date,
        quantity: int = 1,
        reason: HoldReason = HoldReason.OUT_OF_ORDER,
        note: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> Hold:
        h = Hold(
            room_type_id=room_type_id,
            night_from=night_from,
            night_to=night_to,
            quantity=quantity,
            reason=reason,
            note=note,
            created_by=created_by,
        )
        self.db.add(h)
        self.db.commit()
        self.db.refresh(h)
        return h

    def release_hold(self, hold_id: int) -> Optional[Hold]:
        from datetime import datetime, timezone
        h = self.db.query(Hold).filter(Hold.id == hold_id).first()
        if not h:
            return None
        h.released_at = datetime.now(timezone.utc)
        self.db.commit()
        return h

    # ---------- queries ----------

    def _reserved_for_night(self, room_type_id: int, night: _date) -> int:
        # A reservation covers the night when check_in_date <= night < check_out_date.
        count = (
            self.db.query(func.count(Reservation.id))
            .filter(Reservation.room_type_id == room_type_id)
            .filter(Reservation.check_in_date <= night)
            .filter(Reservation.check_out_date > night)
            .filter(
                Reservation.status.in_(
                    [
                        ReservationStatus.CONFIRMED,
                        ReservationStatus.PENDING,
                        ReservationStatus.CHECKED_IN,
                    ]
                )
            )
            .scalar()
            or 0
        )
        return int(count)

    def _holds_for_night(self, room_type_id: int, night: _date) -> int:
        rows = (
            self.db.query(Hold)
            .filter(Hold.room_type_id == room_type_id)
            .filter(Hold.night_from <= night)
            .filter(Hold.night_to >= night)
            .filter(Hold.released_at.is_(None))
            .all()
        )
        return sum(int(h.quantity or 0) for h in rows)

    def snapshot(
        self, room_type_id: int, night: _date
    ) -> AvailabilitySnapshot:
        alloc = self.get(room_type_id, night)
        if not alloc:
            return AvailabilitySnapshot(
                room_type_id=room_type_id,
                night=night,
                total_inventory=0,
                safety_stock=0,
                inbound=0,
                quarantine=0,
                reserved=0,
                holds=0,
                base_sellable=0,
                by_channel={},
            )
        reserved = self._reserved_for_night(room_type_id, night)
        holds = self._holds_for_night(room_type_id, night)
        base = (
            alloc.total_inventory
            - alloc.safety_stock
            - alloc.quarantine
            - reserved
            - holds
            + alloc.inbound
        )
        base = max(0, base)
        # Channel-level caps.
        buffers = (
            self.db.query(ChannelBuffer)
            .filter(ChannelBuffer.room_type_id == room_type_id)
            .filter(ChannelBuffer.night == night)
            .all()
        )
        by_channel = {
            b.channel: min(int(b.max_sellable), base) for b in buffers
        }
        return AvailabilitySnapshot(
            room_type_id=room_type_id,
            night=night,
            total_inventory=int(alloc.total_inventory),
            safety_stock=int(alloc.safety_stock),
            inbound=int(alloc.inbound),
            quarantine=int(alloc.quarantine),
            reserved=reserved,
            holds=holds,
            base_sellable=base,
            by_channel=by_channel,
        )

    def safe_to_sell(
        self,
        room_type_id: int,
        night: _date,
        channel: Optional[str] = None,
    ) -> int:
        snap = self.snapshot(room_type_id, night)
        if channel and channel in snap.by_channel:
            return snap.by_channel[channel]
        return snap.base_sellable

    def range_snapshot(
        self,
        room_type_id: int,
        nights: Iterable[_date],
    ) -> List[AvailabilitySnapshot]:
        return [self.snapshot(room_type_id, n) for n in nights]
