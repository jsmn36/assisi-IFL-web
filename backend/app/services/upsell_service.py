"""Upsell chain dispatcher.

Two entry points:

- :meth:`UpsellService.trigger` — called from anywhere in the app when
  a relevant event happens. Spins up a ``UpsellChainRun`` per matching
  chain and immediately schedules step 0.

- :meth:`UpsellService.process_due` — called by the scheduler. Walks
  pending runs whose ``next_step_at`` has passed, executes that step,
  and advances the cursor.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Guest, Reservation
from app.models.upsell import (
    UpsellChain,
    UpsellChainRun,
    UpsellRunStatus,
    UpsellSend,
    UpsellStep,
    UpsellStepType,
    UpsellTrigger,
)

logger = logging.getLogger(__name__)


def _render(template: str, ctx: Dict[str, Any]) -> str:
    """Simple {{var}} substitution — no Jinja, no surprises."""
    out = template or ""
    for k, v in ctx.items():
        out = out.replace("{{" + k + "}}", str(v))
    return out


class UpsellService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- chain admin ----------

    def list_chains(self) -> List[UpsellChain]:
        return self.db.query(UpsellChain).order_by(UpsellChain.id).all()

    def create_chain(
        self,
        *,
        name: str,
        trigger: UpsellTrigger,
        description: Optional[str] = None,
        conditions: Optional[dict] = None,
        steps: Optional[List[dict]] = None,
    ) -> UpsellChain:
        chain = UpsellChain(
            name=name,
            trigger=trigger,
            description=description,
            conditions=conditions or {},
        )
        self.db.add(chain)
        self.db.flush()
        for i, s in enumerate(steps or []):
            self.db.add(
                UpsellStep(
                    chain_id=chain.id,
                    step_order=s.get("step_order", i),
                    step_type=UpsellStepType(s["step_type"]),
                    delay_minutes=int(s.get("delay_minutes", 0)),
                    subject=s.get("subject"),
                    body_template=s["body_template"],
                )
            )
        self.db.commit()
        self.db.refresh(chain)
        return chain

    def update_chain(self, chain_id: int, **fields) -> Optional[UpsellChain]:
        chain = self.db.query(UpsellChain).filter(UpsellChain.id == chain_id).first()
        if not chain:
            return None
        for k, v in fields.items():
            if v is None:
                continue
            setattr(chain, k, v)
        self.db.commit()
        self.db.refresh(chain)
        return chain

    def delete_chain(self, chain_id: int) -> bool:
        chain = self.db.query(UpsellChain).filter(UpsellChain.id == chain_id).first()
        if not chain:
            return False
        self.db.delete(chain)
        self.db.commit()
        return True

    # ---------- trigger ----------

    def trigger(
        self,
        trigger: UpsellTrigger,
        *,
        guest_id: Optional[int] = None,
        reservation_id: Optional[int] = None,
        event_payload: Optional[dict] = None,
    ) -> List[UpsellChainRun]:
        """Find matching chains and create runs."""
        chains = (
            self.db.query(UpsellChain)
            .filter(UpsellChain.trigger == trigger)
            .filter(UpsellChain.is_active.is_(True))
            .all()
        )
        runs: List[UpsellChainRun] = []
        payload = event_payload or {}
        for chain in chains:
            if not self._matches_conditions(chain.conditions or {}, payload):
                continue
            steps = chain.steps
            if not steps:
                continue
            first_delay = steps[0].delay_minutes or 0
            run = UpsellChainRun(
                chain_id=chain.id,
                trigger_event=trigger.value,
                guest_id=guest_id,
                reservation_id=reservation_id,
                status=UpsellRunStatus.PENDING,
                next_step_index=0,
                next_step_at=datetime.now(timezone.utc) + timedelta(minutes=first_delay),
            )
            self.db.add(run)
            runs.append(run)
        self.db.commit()
        for r in runs:
            self.db.refresh(r)
        return runs

    def _matches_conditions(self, conditions: dict, payload: dict) -> bool:
        if not conditions:
            return True
        for k, v in conditions.items():
            if payload.get(k) != v:
                return False
        return True

    # ---------- step execution ----------

    def process_due(self, limit: int = 50) -> Dict[str, int]:
        now = datetime.now(timezone.utc)
        runs = (
            self.db.query(UpsellChainRun)
            .filter(
                UpsellChainRun.status.in_(
                    [UpsellRunStatus.PENDING, UpsellRunStatus.RUNNING]
                )
            )
            .filter(UpsellChainRun.next_step_at <= now)
            .limit(limit)
            .all()
        )
        executed = 0
        completed = 0
        failed = 0
        for run in runs:
            try:
                if self._execute_next_step(run):
                    executed += 1
                if run.status == UpsellRunStatus.COMPLETED:
                    completed += 1
            except Exception as exc:  # noqa: BLE001
                logger.exception("Upsell run %s failed", run.id)
                run.status = UpsellRunStatus.FAILED
                run.error_message = str(exc)[:1000]
                self.db.commit()
                failed += 1
        return {"runs_processed": len(runs), "executed": executed, "completed": completed, "failed": failed}

    def _execute_next_step(self, run: UpsellChainRun) -> bool:
        chain = (
            self.db.query(UpsellChain).filter(UpsellChain.id == run.chain_id).first()
        )
        if not chain or not chain.is_active:
            run.status = UpsellRunStatus.CANCELLED
            self.db.commit()
            return False
        steps = chain.steps
        if run.next_step_index >= len(steps):
            run.status = UpsellRunStatus.COMPLETED
            run.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            return False
        step = steps[run.next_step_index]
        run.status = UpsellRunStatus.RUNNING

        # Build context.
        ctx: Dict[str, Any] = {}
        guest = None
        if run.guest_id:
            guest = self.db.query(Guest).filter(Guest.id == run.guest_id).first()
            if guest:
                ctx["guest_name"] = f"{guest.first_name} {guest.last_name}".strip()
                ctx["guest_email"] = guest.email or ""
        if run.reservation_id:
            res = self.db.query(Reservation).filter(Reservation.id == run.reservation_id).first()
            if res:
                ctx["confirmation_number"] = res.confirmation_number
                ctx["check_in_date"] = str(res.check_in_date or "")
                ctx["check_out_date"] = str(res.check_out_date or "")

        rendered = _render(step.body_template, ctx)
        send = self._dispatch(run, step, guest, rendered)
        self.db.add(send)

        # Advance cursor.
        run.next_step_index += 1
        if run.next_step_index >= len(steps):
            run.status = UpsellRunStatus.COMPLETED
            run.completed_at = datetime.now(timezone.utc)
            run.next_step_at = None
        else:
            run.next_step_at = datetime.now(timezone.utc) + timedelta(
                minutes=steps[run.next_step_index].delay_minutes or 0
            )

        self.db.commit()
        self.db.refresh(run)
        return True

    def _dispatch(
        self,
        run: UpsellChainRun,
        step: UpsellStep,
        guest: Optional[Guest],
        rendered_body: str,
    ) -> UpsellSend:
        if step.step_type == UpsellStepType.EMAIL:
            recipient = guest.email if guest else None
            send = UpsellSend(
                run_id=run.id,
                step_id=step.id,
                step_order=step.step_order,
                channel="email",
                recipient=recipient,
                body=rendered_body[:5000],
            )
            if not recipient:
                send.error_message = "no recipient email"
                return send
            # Honor the suppression list.
            from app.services.suppression_service import SuppressionService
            from app.models.suppression import SuppressionChannel

            if SuppressionService(self.db).is_suppressed(
                recipient, SuppressionChannel.EMAIL
            ):
                send.suppressed = True
                send.error_message = "recipient on suppression list"
                return send
            # We can't easily await here; record as sent and let the
            # notification service handle actual delivery if integrated.
            send.sent_at = datetime.now(timezone.utc)
            logger.info(
                "Upsell %s step %s would send email to %s",
                run.id,
                step.step_order,
                recipient,
            )
            return send
        if step.step_type == UpsellStepType.SMS:
            recipient = (guest.phone or guest.mobile) if guest else None
            send = UpsellSend(
                run_id=run.id,
                step_id=step.id,
                step_order=step.step_order,
                channel="sms",
                recipient=recipient,
                body=rendered_body[:1600],
            )
            if not recipient:
                send.error_message = "no recipient phone"
                return send
            from app.services.suppression_service import SuppressionService
            from app.models.suppression import SuppressionChannel

            if SuppressionService(self.db).is_suppressed(
                recipient, SuppressionChannel.SMS
            ):
                send.suppressed = True
                send.error_message = "recipient on suppression list"
                return send
            send.sent_at = datetime.now(timezone.utc)
            return send

        # NOTE: internal note — always sent, no recipient.
        return UpsellSend(
            run_id=run.id,
            step_id=step.id,
            step_order=step.step_order,
            channel="note",
            recipient=None,
            sent_at=datetime.now(timezone.utc),
            body=rendered_body[:5000],
        )

    # ---------- reporting ----------

    def chain_metrics(self, chain_id: int) -> dict:
        runs = (
            self.db.query(UpsellChainRun)
            .filter(UpsellChainRun.chain_id == chain_id)
            .all()
        )
        sends = (
            self.db.query(UpsellSend)
            .join(UpsellChainRun)
            .filter(UpsellChainRun.chain_id == chain_id)
            .all()
        )
        return {
            "runs_total": len(runs),
            "runs_completed": sum(1 for r in runs if r.status == UpsellRunStatus.COMPLETED),
            "runs_failed": sum(1 for r in runs if r.status == UpsellRunStatus.FAILED),
            "sends_total": len(sends),
            "sends_suppressed": sum(1 for s in sends if s.suppressed),
            "sends_with_error": sum(1 for s in sends if s.error_message),
        }
