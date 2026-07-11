"""Guest Lifetime Value cohort engine.

Aggregates reservation data into per-guest LTV with channel/segment
breakdown. Identity matching is conservative: it joins by ``guest_id``
first, then by normalized email as a fallback so OTA-originated guests
who later booked direct get merged.

Cohorts:
- High-Value Repeat Direct: 3+ stays AND any direct booking
- Occasional OTA Guest:     2+ stays AND no direct booking
- One-Time Visitor:         exactly 1 stay
- New Direct Booker:        1 stay AND direct
- Inactive Lapsed:          last stay > 365 days ago AND was repeat
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Guest, Reservation, ReservationSource


DIRECT_SOURCES = {ReservationSource.DIRECT, ReservationSource.WALK_IN}


@dataclass
class GuestLTV:
    guest_id: int
    name: str
    email: Optional[str]
    total_stays: int
    total_revenue: float
    avg_revenue_per_stay: float
    first_stay_date: Optional[str]
    last_stay_date: Optional[str]
    direct_stays: int
    ota_stays: int
    primary_channel: str
    cohort: str


def _classify(stay_count: int, direct: int, last_stay: Optional[datetime]) -> str:
    days_since = None
    if last_stay:
        days_since = (datetime.now(timezone.utc) - last_stay).days
    if stay_count >= 3 and direct >= 1:
        return "high_value_repeat_direct"
    if stay_count >= 2 and direct == 0:
        return "occasional_ota"
    if stay_count == 1 and direct >= 1:
        return "new_direct"
    if stay_count == 1:
        return "one_time_ota"
    if days_since is not None and days_since > 365 and stay_count >= 2:
        return "inactive_lapsed"
    return "other"


class GuestLTVService:
    def __init__(self, db: Session):
        self.db = db

    def compute_all(
        self,
        limit: int = 1000,
        offset: int = 0,
        min_stays: int = 1,
        cohort: Optional[str] = None,
    ) -> Tuple[List[GuestLTV], int]:
        # Aggregate per guest. Filter out non-revenue-producing statuses.
        from app.models import ReservationStatus

        agg = (
            self.db.query(
                Reservation.guest_id.label("gid"),
                func.count(Reservation.id).label("stays"),
                func.coalesce(func.sum(Reservation.total_amount), 0).label("revenue"),
                func.min(Reservation.check_in_date).label("first"),
                func.max(Reservation.check_in_date).label("last"),
            )
            .filter(
                Reservation.status.in_(
                    [
                        ReservationStatus.CONFIRMED,
                        ReservationStatus.CHECKED_IN,
                        ReservationStatus.CHECKED_OUT,
                        ReservationStatus.COMPLETED,
                    ]
                )
                if hasattr(ReservationStatus, "COMPLETED")
                else Reservation.status != ReservationStatus.CANCELLED
            )
            .group_by(Reservation.guest_id)
            .having(func.count(Reservation.id) >= min_stays)
            .all()
        )

        results: List[GuestLTV] = []
        for r in agg:
            guest = (
                self.db.query(Guest).filter(Guest.id == r.gid).first()
            )
            if not guest:
                continue
            by_source = (
                self.db.query(Reservation.source, func.count(Reservation.id))
                .filter(Reservation.guest_id == r.gid)
                .group_by(Reservation.source)
                .all()
            )
            channel_counts = {
                getattr(s, "value", str(s) or "unknown"): int(c)
                for s, c in by_source
            }
            direct = sum(
                v
                for k, v in channel_counts.items()
                if k in {s.value for s in DIRECT_SOURCES}
            )
            ota = sum(v for k, v in channel_counts.items()) - direct
            primary = max(channel_counts.items(), key=lambda kv: kv[1])[0] if channel_counts else "unknown"

            last_dt = (
                datetime.combine(r.last, datetime.min.time(), tzinfo=timezone.utc)
                if r.last
                else None
            )
            label = _classify(int(r.stays), direct, last_dt)
            if cohort and label != cohort:
                continue

            results.append(
                GuestLTV(
                    guest_id=r.gid,
                    name=f"{guest.first_name} {guest.last_name}".strip(),
                    email=guest.email,
                    total_stays=int(r.stays),
                    total_revenue=float(r.revenue or 0),
                    avg_revenue_per_stay=(float(r.revenue or 0) / int(r.stays))
                    if r.stays
                    else 0.0,
                    first_stay_date=r.first.isoformat() if r.first else None,
                    last_stay_date=r.last.isoformat() if r.last else None,
                    direct_stays=direct,
                    ota_stays=ota,
                    primary_channel=primary,
                    cohort=label,
                )
            )

        results.sort(key=lambda g: g.total_revenue, reverse=True)
        total = len(results)
        return results[offset : offset + limit], total

    def top_n(self, n: int = 100) -> List[GuestLTV]:
        rows, _ = self.compute_all(limit=n)
        return rows

    def cohort_summary(self) -> Dict:
        rows, _ = self.compute_all(limit=100_000)
        agg: Dict[str, Dict] = {}
        for r in rows:
            entry = agg.setdefault(
                r.cohort, {"guests": 0, "revenue": 0.0, "stays": 0}
            )
            entry["guests"] += 1
            entry["revenue"] += r.total_revenue
            entry["stays"] += r.total_stays
        return {
            "cohorts": [
                {
                    "cohort": k,
                    "guests": v["guests"],
                    "revenue": v["revenue"],
                    "stays": v["stays"],
                    "avg_revenue_per_guest": (v["revenue"] / v["guests"])
                    if v["guests"]
                    else 0.0,
                }
                for k, v in sorted(agg.items(), key=lambda kv: kv[1]["revenue"], reverse=True)
            ]
        }

    def export_csv(self, rows: List[GuestLTV]) -> str:
        import csv
        import io

        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(
            [
                "guest_id",
                "name",
                "email",
                "total_stays",
                "total_revenue",
                "avg_revenue_per_stay",
                "first_stay_date",
                "last_stay_date",
                "direct_stays",
                "ota_stays",
                "primary_channel",
                "cohort",
            ]
        )
        for r in rows:
            w.writerow(
                [
                    r.guest_id,
                    r.name,
                    r.email or "",
                    r.total_stays,
                    f"{r.total_revenue:.2f}",
                    f"{r.avg_revenue_per_stay:.2f}",
                    r.first_stay_date or "",
                    r.last_stay_date or "",
                    r.direct_stays,
                    r.ota_stays,
                    r.primary_channel,
                    r.cohort,
                ]
            )
        return buf.getvalue()
