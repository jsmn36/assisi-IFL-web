"""Guest feedback service with close-loop logic.

Submission heuristics:

- NPS <= 6 OR rating_1_5 <= 2 OR sentiment == NEGATIVE -> auto-create
  a resolution task in OPEN with a 48-hour SLA.
- POSITIVE feedback skips the task but is still recorded.
- ``resolve`` writes the resolution summary, flips status, and (if the
  guest has an email) records a notification through NotificationService.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Guest, Reservation
from app.models.feedback import (
    FeedbackChannel,
    FeedbackResolution,
    FeedbackSentiment,
    GuestFeedback,
    ResolutionStatus,
)

logger = logging.getLogger(__name__)


def _is_negative(nps: Optional[int], rating: Optional[int], sentiment: FeedbackSentiment) -> bool:
    if nps is not None and nps <= 6:
        return True
    if rating is not None and rating <= 2:
        return True
    return sentiment == FeedbackSentiment.NEGATIVE


class FeedbackService:
    DEFAULT_SLA_HOURS = 48

    def __init__(self, db: Session):
        self.db = db

    # ---------- intake ----------

    def submit(
        self,
        *,
        channel: FeedbackChannel,
        guest_id: Optional[int] = None,
        reservation_id: Optional[int] = None,
        nps_score: Optional[int] = None,
        rating_1_5: Optional[int] = None,
        sentiment: FeedbackSentiment = FeedbackSentiment.NEUTRAL,
        title: Optional[str] = None,
        body: Optional[str] = None,
        tags: Optional[str] = None,
        default_owner_user_id: Optional[int] = None,
    ) -> GuestFeedback:
        fb = GuestFeedback(
            guest_id=guest_id,
            reservation_id=reservation_id,
            channel=channel,
            nps_score=nps_score,
            rating_1_5=rating_1_5,
            sentiment=sentiment,
            title=title,
            body=body,
            tags=tags,
        )
        self.db.add(fb)
        self.db.flush()
        if _is_negative(nps_score, rating_1_5, sentiment):
            self.db.add(
                FeedbackResolution(
                    feedback_id=fb.id,
                    status=ResolutionStatus.OPEN,
                    owner_user_id=default_owner_user_id,
                    due_date=datetime.now(timezone.utc)
                    + timedelta(hours=self.DEFAULT_SLA_HOURS),
                )
            )
        self.db.commit()
        self.db.refresh(fb)
        return fb

    # ---------- queries ----------

    def list(
        self,
        sentiment: Optional[FeedbackSentiment] = None,
        guest_id: Optional[int] = None,
        with_open_task: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[GuestFeedback], int]:
        q = self.db.query(GuestFeedback)
        if sentiment:
            q = q.filter(GuestFeedback.sentiment == sentiment)
        if guest_id is not None:
            q = q.filter(GuestFeedback.guest_id == guest_id)
        if with_open_task is True:
            q = q.join(GuestFeedback.resolution).filter(
                FeedbackResolution.status.in_(
                    [ResolutionStatus.OPEN, ResolutionStatus.IN_PROGRESS]
                )
            )
        total = q.count()
        rows = (
            q.order_by(GuestFeedback.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return rows, total

    def get(self, feedback_id: int) -> Optional[GuestFeedback]:
        return self.db.query(GuestFeedback).filter(GuestFeedback.id == feedback_id).first()

    # ---------- resolution ----------

    def update_resolution(
        self,
        feedback_id: int,
        *,
        status: Optional[ResolutionStatus] = None,
        owner_user_id: Optional[int] = None,
        due_date: Optional[datetime] = None,
        resolution_summary: Optional[str] = None,
    ) -> Optional[FeedbackResolution]:
        fb = self.get(feedback_id)
        if not fb:
            return None
        res = fb.resolution
        if not res:
            res = FeedbackResolution(feedback_id=fb.id, status=ResolutionStatus.OPEN)
            self.db.add(res)
            self.db.flush()
        if status is not None:
            res.status = status
        if owner_user_id is not None:
            res.owner_user_id = owner_user_id
        if due_date is not None:
            res.due_date = due_date
        if resolution_summary is not None:
            res.resolution_summary = resolution_summary
        self.db.commit()
        self.db.refresh(res)
        return res

    def resolve_and_notify(
        self,
        feedback_id: int,
        *,
        resolution_summary: str,
        actor_user_id: Optional[int] = None,
    ) -> Optional[FeedbackResolution]:
        fb = self.get(feedback_id)
        if not fb:
            return None
        res = fb.resolution
        if not res:
            res = FeedbackResolution(feedback_id=fb.id, status=ResolutionStatus.OPEN)
            self.db.add(res)
            self.db.flush()
        res.status = ResolutionStatus.RESOLVED
        res.resolution_summary = resolution_summary
        res.resolved_at = datetime.now(timezone.utc)
        res.resolved_by = actor_user_id

        # Notify the guest if we have an email. We rely on NotificationService
        # to honor the suppression list.
        if fb.guest_id:
            guest = self.db.query(Guest).filter(Guest.id == fb.guest_id).first()
            if guest and guest.email:
                self._notify_guest(guest, fb, resolution_summary)
                res.guest_notified_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(res)
        return res

    def _notify_guest(self, guest: Guest, fb: GuestFeedback, summary: str) -> None:
        """Best-effort notification; non-fatal on failure."""
        try:
            from app.models import Notification, NotificationStatus, NotificationType
            from app.services.suppression_service import SuppressionService
            from app.models.suppression import SuppressionChannel

            suppressed = SuppressionService(self.db).is_suppressed(
                guest.email, SuppressionChannel.EMAIL
            )
            self.db.add(
                Notification(
                    type=NotificationType.EMAIL,
                    status=(
                        NotificationStatus.SUPPRESSED
                        if suppressed
                        else NotificationStatus.PENDING
                    ),
                    recipient_email=guest.email,
                    guest_id=guest.id,
                    subject="We've resolved your feedback",
                    message=(
                        f"Hi {guest.first_name},\n\nThank you for your feedback. "
                        f"Here's what we did about it:\n\n{summary}\n\n"
                        "If anything's still off, please reply to this email and "
                        "we'll keep working on it."
                    ),
                    template_name="feedback_resolution",
                )
            )
        except Exception:  # noqa: BLE001
            logger.exception("Failed to enqueue resolution notification for guest %s", guest.id)

    def overdue(self) -> List[FeedbackResolution]:
        now = datetime.now(timezone.utc)
        return (
            self.db.query(FeedbackResolution)
            .filter(FeedbackResolution.status.in_(
                [ResolutionStatus.OPEN, ResolutionStatus.IN_PROGRESS]
            ))
            .filter(FeedbackResolution.due_date.isnot(None))
            .filter(FeedbackResolution.due_date < now)
            .all()
        )
