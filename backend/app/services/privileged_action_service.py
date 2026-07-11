"""Privileged action heatmap service.

Aggregates the existing ``audit_logs`` table into:
- a user × hour-of-day grid showing concentration of high-risk actions
- a day-of-week breakdown
- a top-actors list with their privileged-action share

The set of "privileged" actions is configurable. Anything not in the set
counts as a normal action and is still surfaced in the breakdown so admins
can spot user behaviour anomalies without a separate dashboard.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import AuditLog, User


# Defaults — substring match against ``action`` column. Extend in config.
DEFAULT_PRIVILEGED_TOKENS = (
    "delete",
    "void",
    "refund",
    "credit",
    "override",
    "force_check_in",
    "force_check_out",
    "manual_post",
    "manager_void",
    "discount_approve",
    "permission_change",
    "role_change",
    "config_change",
    "export",
    "deactivate",
    "reactivate",
    "drop_",
    "purge",
)


def _is_privileged(action: str, tokens: Tuple[str, ...]) -> bool:
    if not action:
        return False
    a = action.lower()
    return any(t in a for t in tokens)


class PrivilegedActionService:
    def __init__(self, db: Session, privileged_tokens: Tuple[str, ...] = DEFAULT_PRIVILEGED_TOKENS):
        self.db = db
        self.tokens = privileged_tokens

    def _window(self, since_days: int) -> datetime:
        return datetime.now(timezone.utc) - timedelta(days=since_days)

    def heatmap(
        self,
        since_days: int = 30,
        only_privileged: bool = True,
        top_n_users: int = 20,
    ) -> Dict:
        """Return per-user × hour-of-day counts."""
        cutoff = self._window(since_days)
        rows = (
            self.db.query(
                AuditLog.user_id,
                AuditLog.username,
                AuditLog.action,
                AuditLog.created_at,
            )
            .filter(AuditLog.created_at >= cutoff)
            .filter(AuditLog.user_id.isnot(None))
            .all()
        )

        # user_id -> {"username": ..., "hours": [24], "actions_total": int}
        per_user: Dict[int, dict] = {}
        for uid, uname, action, ts in rows:
            if only_privileged and not _is_privileged(action or "", self.tokens):
                continue
            entry = per_user.setdefault(
                uid,
                {"username": uname, "hours": [0] * 24, "actions_total": 0, "by_action": {}},
            )
            hour = ts.hour if ts else 0
            entry["hours"][hour] += 1
            entry["actions_total"] += 1
            entry["by_action"][action] = entry["by_action"].get(action, 0) + 1

        # Top N
        ranked = sorted(
            per_user.items(), key=lambda kv: kv[1]["actions_total"], reverse=True
        )[:top_n_users]

        return {
            "since_days": since_days,
            "only_privileged": only_privileged,
            "users": [
                {
                    "user_id": uid,
                    "username": data["username"],
                    "actions_total": data["actions_total"],
                    "hours": data["hours"],
                    "top_actions": sorted(
                        data["by_action"].items(),
                        key=lambda kv: kv[1],
                        reverse=True,
                    )[:5],
                }
                for uid, data in ranked
            ],
        }

    def by_day_of_week(self, since_days: int = 30) -> List[Dict]:
        """Privileged-action volume by day-of-week (0=Mon)."""
        cutoff = self._window(since_days)
        rows = (
            self.db.query(AuditLog.action, AuditLog.created_at)
            .filter(AuditLog.created_at >= cutoff)
            .all()
        )
        buckets = [0] * 7
        for action, ts in rows:
            if not _is_privileged(action or "", self.tokens):
                continue
            if ts is None:
                continue
            buckets[ts.weekday()] += 1
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return [{"day": names[i], "hits": c} for i, c in enumerate(buckets)]

    def top_privileged_actions(
        self, since_days: int = 30, limit: int = 20
    ) -> List[Dict]:
        cutoff = self._window(since_days)
        rows = (
            self.db.query(
                AuditLog.action,
                func.count(AuditLog.id).label("hits"),
            )
            .filter(AuditLog.created_at >= cutoff)
            .group_by(AuditLog.action)
            .order_by(func.count(AuditLog.id).desc())
            .all()
        )
        return [
            {"action": a, "hits": int(h)}
            for a, h in rows
            if _is_privileged(a or "", self.tokens)
        ][:limit]

    def actor_summary(self, since_days: int = 30) -> Dict:
        cutoff = self._window(since_days)
        total = (
            self.db.query(func.count(AuditLog.id))
            .filter(AuditLog.created_at >= cutoff)
            .scalar()
            or 0
        )
        rows = (
            self.db.query(AuditLog.action)
            .filter(AuditLog.created_at >= cutoff)
            .all()
        )
        privileged = sum(
            1 for (action,) in rows if _is_privileged(action or "", self.tokens)
        )
        unique_actors = (
            self.db.query(func.count(func.distinct(AuditLog.user_id)))
            .filter(AuditLog.created_at >= cutoff)
            .filter(AuditLog.user_id.isnot(None))
            .scalar()
            or 0
        )
        return {
            "since_days": since_days,
            "total_actions": int(total),
            "privileged_actions": int(privileged),
            "privileged_share": (privileged / total) if total else 0.0,
            "unique_actors": int(unique_actors),
        }
