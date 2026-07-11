"""Anomaly alerts REST API."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db, require_role
from app.models import User
from app.models.anomaly import AnomalySeverity, AnomalyStatus
from app.services.anomaly_service import (
    METRIC_SOURCES,
    AnomalyService,
)

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])


def _serialize_alert(a) -> dict:
    return {
        "id": a.id,
        "metric_key": a.metric_key,
        "scope": a.scope,
        "observed_value": float(a.observed_value or 0),
        "baseline_mean": a.baseline_mean,
        "baseline_stdev": a.baseline_stdev,
        "z_score": a.z_score,
        "direction": a.direction,
        "severity": a.severity.value if a.severity else None,
        "status": a.status.value if a.status else None,
        "summary": a.summary,
        "root_cause_hint": a.root_cause_hint,
        "suggested_action": a.suggested_action,
        "acknowledged_by": a.acknowledged_by,
        "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
        "notes": a.notes,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }


class AcknowledgeIn(BaseModel):
    notes: Optional[str] = None


class MuteIn(BaseModel):
    metric_key: str
    scope: str = "all"
    reason: Optional[str] = None
    ttl_hours: Optional[int] = None


class StatusIn(BaseModel):
    status: AnomalyStatus


@router.get("")
def list_alerts(
    status: Optional[AnomalyStatus] = None,
    severity: Optional[AnomalySeverity] = None,
    since_days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows, total = AnomalyService(db).list_alerts(
        status=status, severity=severity, since_days=since_days, limit=limit, offset=offset
    )
    return {
        "items": [_serialize_alert(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/scan")
def run_scan(
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    return AnomalyService(db).run_daily_scan()


@router.post("/recompute-baseline")
def recompute_baseline(
    metric_key: str,
    scope: str = "all",
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    if metric_key not in METRIC_SOURCES:
        raise HTTPException(status_code=400, detail="Unknown metric_key")
    b = AnomalyService(db).recompute_baseline(metric_key, scope)
    return {
        "metric_key": b.metric_key,
        "scope": b.scope,
        "mean": b.mean,
        "stdev": b.stdev,
        "sample_size": b.sample_size,
        "window_days": b.window_days,
        "last_recomputed_at": b.last_recomputed_at.isoformat() if b.last_recomputed_at else None,
    }


@router.post("/{alert_id}/acknowledge")
def acknowledge(
    alert_id: int,
    payload: AcknowledgeIn,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    a = AnomalyService(db).acknowledge(alert_id, current_user.id, notes=payload.notes)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _serialize_alert(a)


@router.post("/{alert_id}/status")
def set_status(
    alert_id: int,
    payload: StatusIn,
    _: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    a = AnomalyService(db).mark(alert_id, payload.status)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _serialize_alert(a)


@router.post("/mutes")
def add_mute(
    payload: MuteIn,
    current_user: User = Depends(require_role("admin", "manager")),
    db: Session = Depends(get_db),
):
    m = AnomalyService(db).mute(
        metric_key=payload.metric_key,
        scope=payload.scope,
        reason=payload.reason,
        ttl_hours=payload.ttl_hours,
        created_by=current_user.id,
    )
    return {
        "id": m.id,
        "metric_key": m.metric_key,
        "scope": m.scope,
        "expires_at": m.expires_at.isoformat() if m.expires_at else None,
    }


@router.get("/metrics")
def list_metrics(_: User = Depends(get_current_user)):
    """Available metric keys for muting / baseline recompute."""
    return {"metrics": list(METRIC_SOURCES.keys())}
