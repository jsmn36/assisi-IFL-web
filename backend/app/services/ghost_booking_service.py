"""Ghost Booking Classifier — rule engine.

Each signal contributes additive points to a risk score (0..100). Tiers:

- 0..29   -> low,   decision=allow
- 30..59  -> medium, decision=require_deposit
- 60..84  -> high,   decision=require_review
- 85+     -> block,  decision=block

Signals (all evaluated even if some are missing — missing == 0 points):

1. Disposable / suspicious email domain (e.g. mailinator, tempmail).        +25
2. Free-mail domain on a high-value booking (>=3 nights).                   +5
3. Booking originated very close to arrival (<24h) with no prepayment.      +20
4. Total amount >= 2x the property's recent ADR.                            +10
5. Guest no-show history rate >= 30% (computed from prior reservations).    +20
6. Channel marked as high-risk (configurable list).                          +15
7. Geo mismatch — IP country != billing country (if both known).            +15
8. Overlapping booking same guest within 1 day on a different channel.     +20
9. Repeated cancellations from the same email in last 90 days (>=2).        +15
10. Group / multi-room booking with no deposit at long lead time.           +10
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Guest,
    Reservation,
    ReservationSource,
    ReservationStatus,
)
from app.models.ghost_booking import (
    GhostBookingScore,
    GhostDecision,
    GhostRiskTier,
)


# Signal weights (single source of truth — tunable here, not scattered).
SIGNAL_WEIGHTS: Dict[str, int] = {
    "disposable_email_domain": 25,
    "freemail_high_value": 5,
    "last_minute_no_prepay": 20,
    "amount_far_above_adr": 10,
    "guest_no_show_history": 20,
    "high_risk_channel": 15,
    "geo_mismatch": 15,
    "overlapping_booking": 20,
    "repeat_cancellation_email": 15,
    "long_lead_group_no_deposit": 10,
}


_DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "tempmail.com",
    "10minutemail.com",
    "guerrillamail.com",
    "yopmail.com",
    "throwawaymail.com",
    "trashmail.com",
    "fakeinbox.com",
}
_FREEMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "proton.me",
    "protonmail.com",
}
_HIGH_RISK_CHANNELS = {
    # Channel-source values mapping to higher cancellation/no-show rates.
    # Tune as data arrives.
    ReservationSource.OTHER,
}


@dataclass
class GBCInput:
    reservation_id: Optional[int]
    guest_id: Optional[int]
    guest_email: Optional[str]
    source: Optional[ReservationSource]
    total_amount: float
    number_of_nights: int
    lead_time_hours: float
    deposit_paid: float
    ip_country: Optional[str] = None
    billing_country: Optional[str] = None
    is_group: bool = False


@dataclass
class Contribution:
    signal: str
    points: int
    evidence: dict


class GhostBookingService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- public API ----------

    def score_reservation(
        self, reservation_id: int, **extra_signals
    ) -> GhostBookingScore:
        res = self.db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not res:
            raise ValueError(f"Reservation {reservation_id} not found")
        guest = self.db.query(Guest).filter(Guest.id == res.guest_id).first() if res.guest_id else None

        lead_hours = self._lead_time_hours(res)
        gbc_input = GBCInput(
            reservation_id=res.id,
            guest_id=res.guest_id,
            guest_email=(guest.email if guest else None),
            source=res.source,
            total_amount=float(res.total_amount or 0),
            number_of_nights=int(res.number_of_nights or 0),
            lead_time_hours=lead_hours,
            deposit_paid=float(res.deposit_paid or 0),
            ip_country=extra_signals.get("ip_country"),
            billing_country=extra_signals.get("billing_country"),
            is_group=bool(res.group_reservation_id) if hasattr(res, "group_reservation_id") else False,
        )

        contributions = self._evaluate_all(gbc_input)
        return self._persist(reservation_id, gbc_input, contributions)

    def evaluate_only(self, gbc_input: GBCInput) -> Tuple[int, GhostRiskTier, GhostDecision, List[Contribution]]:
        """Pure evaluation — no DB write. Useful for pre-booking flows."""
        contributions = self._evaluate_all(gbc_input)
        score = sum(c.points for c in contributions)
        tier, decision = self._tier_and_decision(score)
        return score, tier, decision, contributions

    def override(
        self,
        score_id: int,
        new_decision: GhostDecision,
        actor_user_id: Optional[int],
        reason: str,
    ) -> Optional[GhostBookingScore]:
        row = self.db.query(GhostBookingScore).filter(GhostBookingScore.id == score_id).first()
        if not row:
            return None
        row.overridden_at = datetime.now(timezone.utc)
        row.overridden_by = actor_user_id
        row.override_decision = new_decision
        row.override_reason = reason[:500] if reason else None
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_scores(
        self,
        tier: Optional[GhostRiskTier] = None,
        decision: Optional[GhostDecision] = None,
        since_days: int = 30,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[GhostBookingScore], int]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
        q = self.db.query(GhostBookingScore).filter(GhostBookingScore.created_at >= cutoff)
        if tier:
            q = q.filter(GhostBookingScore.risk_tier == tier)
        if decision:
            q = q.filter(GhostBookingScore.decision == decision)
        total = q.count()
        rows = (
            q.order_by(GhostBookingScore.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return rows, total

    def get(self, score_id: int) -> Optional[GhostBookingScore]:
        return self.db.query(GhostBookingScore).filter(GhostBookingScore.id == score_id).first()

    # ---------- helpers ----------

    def _lead_time_hours(self, res: Reservation) -> float:
        if not res.created_at or not res.check_in_date:
            return 0.0
        check_in_dt = datetime.combine(
            res.check_in_date, datetime.min.time(), tzinfo=timezone.utc
        )
        created = res.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        delta = (check_in_dt - created).total_seconds() / 3600.0
        return max(0.0, delta)

    def _evaluate_all(self, x: GBCInput) -> List[Contribution]:
        out: List[Contribution] = []

        email_domain = _email_domain(x.guest_email)

        # 1. Disposable / suspicious email domain
        if email_domain and email_domain in _DISPOSABLE_DOMAINS:
            out.append(
                Contribution(
                    "disposable_email_domain",
                    SIGNAL_WEIGHTS["disposable_email_domain"],
                    {"domain": email_domain},
                )
            )

        # 2. Freemail on high-value booking
        if (
            email_domain
            and email_domain in _FREEMAIL_DOMAINS
            and x.number_of_nights >= 3
            and x.total_amount > 500
        ):
            out.append(
                Contribution(
                    "freemail_high_value",
                    SIGNAL_WEIGHTS["freemail_high_value"],
                    {"domain": email_domain, "nights": x.number_of_nights},
                )
            )

        # 3. Last-minute booking with no prepayment
        if x.lead_time_hours < 24 and x.deposit_paid <= 0 and x.total_amount > 0:
            out.append(
                Contribution(
                    "last_minute_no_prepay",
                    SIGNAL_WEIGHTS["last_minute_no_prepay"],
                    {"lead_time_hours": x.lead_time_hours},
                )
            )

        # 4. Amount above recent ADR
        adr = self._recent_adr()
        if adr > 0 and x.number_of_nights > 0:
            per_night = x.total_amount / max(1, x.number_of_nights)
            if per_night > 2 * adr:
                out.append(
                    Contribution(
                        "amount_far_above_adr",
                        SIGNAL_WEIGHTS["amount_far_above_adr"],
                        {"per_night": per_night, "adr": adr},
                    )
                )

        # 5. Guest no-show history
        if x.guest_id:
            rate = self._no_show_rate(x.guest_id)
            if rate >= 0.30:
                out.append(
                    Contribution(
                        "guest_no_show_history",
                        SIGNAL_WEIGHTS["guest_no_show_history"],
                        {"rate": rate},
                    )
                )

        # 6. High-risk channel
        if x.source and x.source in _HIGH_RISK_CHANNELS:
            out.append(
                Contribution(
                    "high_risk_channel",
                    SIGNAL_WEIGHTS["high_risk_channel"],
                    {"source": getattr(x.source, "value", str(x.source))},
                )
            )

        # 7. Geo mismatch
        if x.ip_country and x.billing_country and x.ip_country.lower() != x.billing_country.lower():
            out.append(
                Contribution(
                    "geo_mismatch",
                    SIGNAL_WEIGHTS["geo_mismatch"],
                    {"ip_country": x.ip_country, "billing_country": x.billing_country},
                )
            )

        # 8. Overlapping bookings same email, different channel, within ±1 day
        if email_domain and x.guest_email:
            if self._has_overlapping_booking(x.guest_email, x.reservation_id):
                out.append(
                    Contribution(
                        "overlapping_booking",
                        SIGNAL_WEIGHTS["overlapping_booking"],
                        {"email": x.guest_email},
                    )
                )

        # 9. Repeat cancellations same email in last 90 days
        if x.guest_email:
            cancels = self._recent_cancellation_count(x.guest_email)
            if cancels >= 2:
                out.append(
                    Contribution(
                        "repeat_cancellation_email",
                        SIGNAL_WEIGHTS["repeat_cancellation_email"],
                        {"cancellations_90d": cancels},
                    )
                )

        # 10. Long-lead group booking with no deposit
        if x.is_group and x.lead_time_hours > 24 * 30 and x.deposit_paid <= 0:
            out.append(
                Contribution(
                    "long_lead_group_no_deposit",
                    SIGNAL_WEIGHTS["long_lead_group_no_deposit"],
                    {"lead_time_hours": x.lead_time_hours},
                )
            )

        return out

    def _tier_and_decision(self, score: int) -> Tuple[GhostRiskTier, GhostDecision]:
        if score >= 85:
            return GhostRiskTier.BLOCK, GhostDecision.BLOCK
        if score >= 60:
            return GhostRiskTier.HIGH, GhostDecision.REQUIRE_REVIEW
        if score >= 30:
            return GhostRiskTier.MEDIUM, GhostDecision.REQUIRE_DEPOSIT
        return GhostRiskTier.LOW, GhostDecision.ALLOW

    def _recent_adr(self) -> float:
        """Average nightly_rate over confirmed/checked-in last 60 days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=60)
        row = (
            self.db.query(func.avg(Reservation.nightly_rate))
            .filter(Reservation.created_at >= cutoff)
            .filter(
                Reservation.status.in_(
                    [
                        ReservationStatus.CONFIRMED,
                        ReservationStatus.CHECKED_IN,
                        ReservationStatus.CHECKED_OUT,
                    ]
                )
                if hasattr(ReservationStatus, "CHECKED_OUT")
                else Reservation.status == ReservationStatus.CONFIRMED
            )
            .scalar()
        )
        return float(row or 0)

    def _no_show_rate(self, guest_id: int) -> float:
        total = (
            self.db.query(func.count(Reservation.id))
            .filter(Reservation.guest_id == guest_id)
            .scalar()
            or 0
        )
        if not total:
            return 0.0
        no_shows = (
            self.db.query(func.count(Reservation.id))
            .filter(Reservation.guest_id == guest_id)
            .filter(
                Reservation.status == getattr(ReservationStatus, "NO_SHOW", ReservationStatus.CANCELLED)
            )
            .scalar()
            or 0
        )
        return float(no_shows) / float(total)

    def _has_overlapping_booking(self, email: str, exclude_id: Optional[int]) -> bool:
        # Look for a same-email guest with a reservation in the next 14 days
        # that we are not currently scoring.
        guest_ids = [
            g.id for g in self.db.query(Guest.id).filter(Guest.email == email).all()
        ]
        if not guest_ids:
            return False
        soon = datetime.now(timezone.utc) + timedelta(days=14)
        q = (
            self.db.query(func.count(Reservation.id))
            .filter(Reservation.guest_id.in_(guest_ids))
            .filter(Reservation.check_in_date <= soon.date())
        )
        if exclude_id:
            q = q.filter(Reservation.id != exclude_id)
        return (q.scalar() or 0) > 0

    def _recent_cancellation_count(self, email: str) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        guest_ids = [
            g.id for g in self.db.query(Guest.id).filter(Guest.email == email).all()
        ]
        if not guest_ids:
            return 0
        return int(
            self.db.query(func.count(Reservation.id))
            .filter(Reservation.guest_id.in_(guest_ids))
            .filter(Reservation.status == ReservationStatus.CANCELLED)
            .filter(Reservation.created_at >= cutoff)
            .scalar()
            or 0
        )

    def _persist(
        self,
        reservation_id: int,
        x: GBCInput,
        contributions: List[Contribution],
    ) -> GhostBookingScore:
        score = sum(c.points for c in contributions)
        tier, decision = self._tier_and_decision(score)
        row = GhostBookingScore(
            reservation_id=reservation_id,
            guest_id=x.guest_id,
            risk_score=int(score),
            risk_tier=tier,
            decision=decision,
            signals_snapshot={
                "guest_email": x.guest_email,
                "source": getattr(x.source, "value", str(x.source) if x.source else None),
                "total_amount": x.total_amount,
                "number_of_nights": x.number_of_nights,
                "lead_time_hours": x.lead_time_hours,
                "deposit_paid": x.deposit_paid,
                "ip_country": x.ip_country,
                "billing_country": x.billing_country,
                "is_group": x.is_group,
            },
            contributions=[
                {"signal": c.signal, "points": c.points, "evidence": c.evidence}
                for c in contributions
            ],
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)

        # Best-effort: also log to the Decision Audit Ledger if it's available.
        try:
            from app.services.decision_audit_service import DecisionAuditService
            DecisionAuditService(self.db).record(
                feature_id="ghost_booking_classifier",
                decision_type="score_reservation",
                outcome=decision.value,
                inputs=row.signals_snapshot,
                contributions=row.contributions,
                model_version="rules.v1",
                confidence=float(score) / 100.0,
                resource_kind="reservation",
                resource_id=str(reservation_id),
            )
        except Exception:  # noqa: BLE001 — DAL is best-effort
            pass

        return row


def _email_domain(email: Optional[str]) -> Optional[str]:
    if not email or "@" not in email:
        return None
    return email.lower().split("@", 1)[1].strip()
