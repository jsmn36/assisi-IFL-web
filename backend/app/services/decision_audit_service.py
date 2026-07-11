"""Append-only Decision Audit Ledger service.

Called from any AI/rule feature at decision time. We keep the API
fail-soft — DAL outages must never block the underlying business
decision; in v1 we just commit best-effort.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.decision_audit import (
    DALDecisionStatus,
    DecisionEntry,
    DecisionOutcome,
    DecisionOverride,
)

logger = logging.getLogger(__name__)


class DecisionAuditService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- write ----------

    def record(
        self,
        *,
        feature_id: str,
        decision_type: str,
        outcome: str,
        inputs: Optional[dict] = None,
        contributions: Optional[list] = None,
        model_version: Optional[str] = None,
        confidence: Optional[float] = None,
        resource_kind: Optional[str] = None,
        resource_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[DecisionEntry]:
        try:
            row = DecisionEntry(
                feature_id=feature_id,
                decision_type=decision_type,
                outcome=outcome,
                inputs=inputs or {},
                contributions=contributions or [],
                model_version=model_version,
                confidence=confidence,
                resource_kind=resource_kind,
                resource_id=str(resource_id) if resource_id is not None else None,
                correlation_id=correlation_id,
            )
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)
            return row
        except Exception:  # noqa: BLE001 — fail-soft
            logger.exception("DAL record failed for feature=%s", feature_id)
            try:
                self.db.rollback()
            except Exception:
                pass
            return None

    def override(
        self,
        decision_entry_id: int,
        *,
        new_outcome: str,
        reason: str,
        actor_user_id: Optional[int] = None,
    ) -> Optional[DecisionOverride]:
        entry = (
            self.db.query(DecisionEntry)
            .filter(DecisionEntry.id == decision_entry_id)
            .first()
        )
        if not entry:
            return None
        ov = DecisionOverride(
            decision_entry_id=entry.id,
            original_outcome=entry.outcome,
            new_outcome=new_outcome,
            reason=reason,
            actor_user_id=actor_user_id,
        )
        self.db.add(ov)
        self.db.commit()
        self.db.refresh(ov)
        return ov

    def attach_outcome(
        self,
        decision_entry_id: int,
        *,
        outcome_label: str,
        outcome_value: Optional[dict] = None,
        notes: Optional[str] = None,
    ) -> Optional[DecisionOutcome]:
        entry = (
            self.db.query(DecisionEntry)
            .filter(DecisionEntry.id == decision_entry_id)
            .first()
        )
        if not entry:
            return None
        o = DecisionOutcome(
            decision_entry_id=entry.id,
            outcome_label=outcome_label,
            outcome_value=outcome_value or {},
            notes=notes,
        )
        self.db.add(o)
        entry.status = DALDecisionStatus.OUTCOME_RECORDED
        self.db.commit()
        self.db.refresh(o)
        return o

    # ---------- query ----------

    def list_entries(
        self,
        feature_id: Optional[str] = None,
        decision_type: Optional[str] = None,
        outcome: Optional[str] = None,
        resource_kind: Optional[str] = None,
        resource_id: Optional[str] = None,
        since_days: int = 30,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[DecisionEntry], int]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
        q = self.db.query(DecisionEntry).filter(DecisionEntry.created_at >= cutoff)
        if feature_id:
            q = q.filter(DecisionEntry.feature_id == feature_id)
        if decision_type:
            q = q.filter(DecisionEntry.decision_type == decision_type)
        if outcome:
            q = q.filter(DecisionEntry.outcome == outcome)
        if resource_kind:
            q = q.filter(DecisionEntry.resource_kind == resource_kind)
        if resource_id is not None:
            q = q.filter(DecisionEntry.resource_id == str(resource_id))
        total = q.count()
        rows = (
            q.order_by(DecisionEntry.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return rows, total

    def get(self, entry_id: int) -> Optional[DecisionEntry]:
        return (
            self.db.query(DecisionEntry)
            .filter(DecisionEntry.id == entry_id)
            .first()
        )

    def get_overrides(self, entry_id: int) -> List[DecisionOverride]:
        return (
            self.db.query(DecisionOverride)
            .filter(DecisionOverride.decision_entry_id == entry_id)
            .order_by(DecisionOverride.created_at)
            .all()
        )

    def get_outcomes(self, entry_id: int) -> List[DecisionOutcome]:
        return (
            self.db.query(DecisionOutcome)
            .filter(DecisionOutcome.decision_entry_id == entry_id)
            .order_by(DecisionOutcome.observed_at)
            .all()
        )

    def accuracy_by_feature(self, since_days: int = 60) -> List[dict]:
        """Approximate precision per feature using attached outcomes."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
        rows = (
            self.db.query(
                DecisionEntry.feature_id,
                DecisionEntry.outcome,
                DecisionOutcome.outcome_label,
                func.count(DecisionEntry.id),
            )
            .join(DecisionOutcome, DecisionOutcome.decision_entry_id == DecisionEntry.id)
            .filter(DecisionEntry.created_at >= cutoff)
            .group_by(
                DecisionEntry.feature_id,
                DecisionEntry.outcome,
                DecisionOutcome.outcome_label,
            )
            .all()
        )
        by_feature: Dict[str, Dict[str, int]] = {}
        for feat, outcome, label, count in rows:
            agg = by_feature.setdefault(feat, {"total": 0, "true_positive": 0, "false_positive": 0})
            agg["total"] += int(count)
            if label in ("true_positive", "confirmed"):
                agg["true_positive"] += int(count)
            elif label in ("false_positive", "rejected"):
                agg["false_positive"] += int(count)
        out: List[dict] = []
        for feat, agg in by_feature.items():
            precision = (
                agg["true_positive"] / (agg["true_positive"] + agg["false_positive"])
                if (agg["true_positive"] + agg["false_positive"])
                else None
            )
            out.append({"feature_id": feat, **agg, "precision": precision})
        return out
