"""Anomaly detection — rule-based v1.

Each :class:`MetricSource` knows how to fetch (a) the current observed
value for a metric and (b) the historical series used to build the
baseline. The detector then:

1. Loads or recomputes the baseline (mean + stdev over the last N days).
2. Computes a z-score for the observed value.
3. If |z| crosses a threshold AND the metric isn't muted, writes an
   ``AnomalyAlert`` row and returns it.

Root-cause hints are produced by a small set of deterministic rules
(e.g. "cancellation rate from channel X spiked"). No ML in v1.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Callable, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Reservation
from app.models.anomaly import (
    AnomalyAlert,
    AnomalyMute,
    AnomalySeverity,
    AnomalyStatus,
    KpiBaseline,
)

# Thresholds — single source of truth, easy to swap to per-tenant config.
WARNING_Z = 2.0
CRITICAL_Z = 3.0
DEFAULT_WINDOW_DAYS = 60


@dataclass
class MetricSample:
    metric_key: str
    scope: str
    value: float
    sampled_at: datetime


@dataclass
class DetectionResult:
    metric_key: str
    scope: str
    observed_value: float
    mean: float
    stdev: float
    z_score: float
    triggered: bool
    severity: AnomalySeverity
    direction: str
    summary: str
    root_cause_hint: Optional[str] = None
    suggested_action: Optional[str] = None


# ---------------------------------------------------------------------------
# Metric sources — small adapters over the existing data.
# ---------------------------------------------------------------------------

MetricFn = Callable[[Session, datetime], List[MetricSample]]


def _daily_revenue(db: Session, day: datetime) -> List[MetricSample]:
    """Total reservation revenue for the given day (overall + by channel)."""
    end = day.replace(hour=23, minute=59, second=59, microsecond=0)
    start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    rows = (
        db.query(Reservation.source, func.coalesce(func.sum(Reservation.total_amount), 0))
        .filter(Reservation.check_in_date >= start.date())
        .filter(Reservation.check_in_date <= end.date())
        .group_by(Reservation.source)
        .all()
    )
    out: List[MetricSample] = []
    total = 0.0
    for src, amt in rows:
        v = float(amt or 0)
        total += v
        out.append(
            MetricSample(
                metric_key="reservations.revenue_daily",
                scope=f"source={getattr(src, 'value', src) or 'unknown'}",
                value=v,
                sampled_at=day,
            )
        )
    out.append(
        MetricSample(
            metric_key="reservations.revenue_daily",
            scope="all",
            value=total,
            sampled_at=day,
        )
    )
    return out


def _daily_cancellations(db: Session, day: datetime) -> List[MetricSample]:
    """Cancellation count + rate by channel for the given day."""
    from app.models import ReservationStatus  # noqa: WPS433
    cutoff_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    cutoff_end = day.replace(hour=23, minute=59, second=59, microsecond=0)
    rows = (
        db.query(
            Reservation.source,
            func.count(Reservation.id),
            func.sum(
                func.case(
                    (Reservation.status == ReservationStatus.CANCELLED, 1), else_=0
                )
            ),
        )
        .filter(Reservation.created_at >= cutoff_start)
        .filter(Reservation.created_at <= cutoff_end)
        .group_by(Reservation.source)
        .all()
    )
    out: List[MetricSample] = []
    for src, total, cancels in rows:
        rate = float(cancels or 0) / float(total or 1)
        out.append(
            MetricSample(
                metric_key="reservations.cancellation_rate_daily",
                scope=f"source={getattr(src, 'value', src) or 'unknown'}",
                value=rate,
                sampled_at=day,
            )
        )
    return out


METRIC_SOURCES: Dict[str, MetricFn] = {
    "reservations.revenue_daily": _daily_revenue,
    "reservations.cancellation_rate_daily": _daily_cancellations,
}


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class AnomalyService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- baseline ----------

    def _historical_series(
        self,
        fn: MetricFn,
        metric_key: str,
        scope: str,
        end: datetime,
        window_days: int,
    ) -> List[float]:
        series: List[float] = []
        for i in range(1, window_days + 1):
            day = end - timedelta(days=i)
            samples = fn(self.db, day)
            for s in samples:
                if s.metric_key == metric_key and s.scope == scope:
                    series.append(s.value)
        return series

    def recompute_baseline(
        self,
        metric_key: str,
        scope: str = "all",
        window_days: int = DEFAULT_WINDOW_DAYS,
    ) -> KpiBaseline:
        fn = METRIC_SOURCES.get(metric_key)
        if not fn:
            raise ValueError(f"Unknown metric_key: {metric_key}")
        series = self._historical_series(
            fn, metric_key, scope, datetime.now(timezone.utc), window_days
        )
        mean = statistics.mean(series) if series else 0.0
        stdev = statistics.pstdev(series) if len(series) > 1 else 0.0
        baseline = (
            self.db.query(KpiBaseline)
            .filter(KpiBaseline.metric_key == metric_key, KpiBaseline.scope == scope)
            .first()
        )
        if not baseline:
            baseline = KpiBaseline(metric_key=metric_key, scope=scope, window_days=window_days)
            self.db.add(baseline)
        baseline.mean = float(mean)
        baseline.stdev = float(stdev)
        baseline.sample_size = len(series)
        baseline.window_days = window_days
        baseline.last_recomputed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(baseline)
        return baseline

    # ---------- detection ----------

    def _is_muted(self, metric_key: str, scope: str) -> bool:
        now = datetime.now(timezone.utc)
        q = (
            self.db.query(AnomalyMute)
            .filter(AnomalyMute.metric_key == metric_key)
            .filter(AnomalyMute.scope == scope)
            .filter(
                (AnomalyMute.expires_at.is_(None)) | (AnomalyMute.expires_at > now)
            )
        )
        return q.first() is not None

    def evaluate_sample(self, sample: MetricSample) -> DetectionResult:
        baseline = (
            self.db.query(KpiBaseline)
            .filter(KpiBaseline.metric_key == sample.metric_key)
            .filter(KpiBaseline.scope == sample.scope)
            .first()
        )
        if not baseline or baseline.sample_size < 7:
            return DetectionResult(
                metric_key=sample.metric_key,
                scope=sample.scope,
                observed_value=sample.value,
                mean=baseline.mean if baseline else 0.0,
                stdev=baseline.stdev if baseline else 0.0,
                z_score=0.0,
                triggered=False,
                severity=AnomalySeverity.INFO,
                direction="above" if (baseline and sample.value > baseline.mean) else "below",
                summary="insufficient baseline samples",
            )
        if baseline.stdev <= 0:
            return DetectionResult(
                metric_key=sample.metric_key,
                scope=sample.scope,
                observed_value=sample.value,
                mean=baseline.mean,
                stdev=baseline.stdev,
                z_score=0.0,
                triggered=False,
                severity=AnomalySeverity.INFO,
                direction="flat",
                summary="zero variance baseline (constant series)",
            )
        z = (sample.value - baseline.mean) / baseline.stdev
        direction = "above" if z >= 0 else "below"
        triggered = abs(z) >= WARNING_Z and not self._is_muted(
            sample.metric_key, sample.scope
        )
        severity = AnomalySeverity.INFO
        if abs(z) >= CRITICAL_Z:
            severity = AnomalySeverity.CRITICAL
        elif abs(z) >= WARNING_Z:
            severity = AnomalySeverity.WARNING

        summary = (
            f"{sample.metric_key} ({sample.scope}) = {sample.value:.2f} "
            f"vs. baseline μ={baseline.mean:.2f} σ={baseline.stdev:.2f} "
            f"(z={z:.2f}, {direction})"
        )
        hint, action = self._explain(sample, baseline, z)
        return DetectionResult(
            metric_key=sample.metric_key,
            scope=sample.scope,
            observed_value=sample.value,
            mean=baseline.mean,
            stdev=baseline.stdev,
            z_score=z,
            triggered=triggered,
            severity=severity,
            direction=direction,
            summary=summary,
            root_cause_hint=hint,
            suggested_action=action,
        )

    def _explain(
        self,
        sample: MetricSample,
        baseline: KpiBaseline,
        z: float,
    ) -> Tuple[Optional[str], Optional[str]]:
        m = sample.metric_key
        # Per-metric heuristic explanations.
        if m == "reservations.revenue_daily" and z < 0:
            return (
                "Revenue dropped below baseline.",
                "Drill into bookings by channel and cancellations; check whether "
                "OTA rate parity broke or a competitor flash-sale started.",
            )
        if m == "reservations.cancellation_rate_daily" and z > 0:
            return (
                "Cancellation rate spike — could be policy change or OTA outage.",
                "Review cancellation reasons in the booking source above. "
                "Suggest reverting any recent cancellation-policy change.",
            )
        return None, None

    # ---------- recording ----------

    def record_alert(self, result: DetectionResult) -> Optional[AnomalyAlert]:
        if not result.triggered:
            return None
        alert = AnomalyAlert(
            metric_key=result.metric_key,
            scope=result.scope,
            observed_value=Decimal(str(result.observed_value)),
            baseline_mean=result.mean,
            baseline_stdev=result.stdev,
            z_score=result.z_score,
            direction=result.direction,
            severity=result.severity,
            status=AnomalyStatus.OPEN,
            summary=result.summary,
            root_cause_hint=result.root_cause_hint,
            suggested_action=result.suggested_action,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    # ---------- orchestration ----------

    def run_daily_scan(
        self, target_day: Optional[datetime] = None
    ) -> Dict[str, int]:
        day = target_day or datetime.now(timezone.utc)
        triggered = 0
        evaluated = 0
        for metric_key, fn in METRIC_SOURCES.items():
            for sample in fn(self.db, day):
                evaluated += 1
                # Make sure we have a baseline before evaluating.
                if not (
                    self.db.query(KpiBaseline)
                    .filter(KpiBaseline.metric_key == sample.metric_key)
                    .filter(KpiBaseline.scope == sample.scope)
                    .first()
                ):
                    self.recompute_baseline(sample.metric_key, sample.scope)
                result = self.evaluate_sample(sample)
                if self.record_alert(result):
                    triggered += 1
        return {"evaluated": evaluated, "triggered": triggered}

    # ---------- queries ----------

    def list_alerts(
        self,
        status: Optional[AnomalyStatus] = None,
        severity: Optional[AnomalySeverity] = None,
        since_days: int = 30,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[AnomalyAlert], int]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
        q = self.db.query(AnomalyAlert).filter(AnomalyAlert.created_at >= cutoff)
        if status:
            q = q.filter(AnomalyAlert.status == status)
        if severity:
            q = q.filter(AnomalyAlert.severity == severity)
        total = q.count()
        rows = (
            q.order_by(AnomalyAlert.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return rows, total

    def acknowledge(
        self,
        alert_id: int,
        actor_user_id: Optional[int],
        notes: Optional[str] = None,
    ) -> Optional[AnomalyAlert]:
        a = self.db.query(AnomalyAlert).filter(AnomalyAlert.id == alert_id).first()
        if not a:
            return None
        a.status = AnomalyStatus.ACKNOWLEDGED
        a.acknowledged_by = actor_user_id
        a.acknowledged_at = datetime.now(timezone.utc)
        a.notes = notes
        self.db.commit()
        self.db.refresh(a)
        return a

    def mark(self, alert_id: int, status: AnomalyStatus) -> Optional[AnomalyAlert]:
        a = self.db.query(AnomalyAlert).filter(AnomalyAlert.id == alert_id).first()
        if not a:
            return None
        a.status = status
        self.db.commit()
        self.db.refresh(a)
        return a

    def mute(
        self,
        metric_key: str,
        scope: str = "all",
        reason: Optional[str] = None,
        ttl_hours: Optional[int] = None,
        created_by: Optional[int] = None,
    ) -> AnomalyMute:
        m = AnomalyMute(
            metric_key=metric_key,
            scope=scope,
            reason=reason,
            expires_at=(
                datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
                if ttl_hours
                else None
            ),
            created_by=created_by,
        )
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return m
