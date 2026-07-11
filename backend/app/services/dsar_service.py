"""DSAR + consent version services."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.dsar import (
    ConsentKind,
    ConsentRecord,
    ConsentVersion,
    DSARKind,
    DSARRequest,
    DSARStatus,
)


# --------------------------- DSAR ---------------------------


class DSARService:
    DEFAULT_SLA_DAYS = 30

    def __init__(self, db: Session):
        self.db = db

    def intake(
        self,
        *,
        subject_email: str,
        kind: DSARKind,
        subject_name: Optional[str] = None,
        summary: Optional[str] = None,
        guest_id: Optional[int] = None,
        created_by: Optional[int] = None,
    ) -> DSARRequest:
        r = DSARRequest(
            subject_email=subject_email,
            subject_name=subject_name,
            kind=kind,
            summary=summary,
            guest_id=guest_id,
            due_date=datetime.now(timezone.utc)
            + timedelta(days=self.DEFAULT_SLA_DAYS),
            created_by=created_by,
        )
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        return r

    def update_status(
        self,
        request_id: int,
        status: DSARStatus,
        actor_user_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Optional[DSARRequest]:
        r = self.db.query(DSARRequest).filter(DSARRequest.id == request_id).first()
        if not r:
            return None
        r.status = status
        if notes:
            r.notes = (r.notes + "\n" if r.notes else "") + notes
        if status == DSARStatus.VERIFYING_IDENTITY and r.identity_verified_at is None:
            pass  # operator will explicitly verify
        if status in (DSARStatus.DELIVERED, DSARStatus.REJECTED) and r.closed_at is None:
            r.closed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(r)
        return r

    def verify_identity(
        self, request_id: int, actor_user_id: int
    ) -> Optional[DSARRequest]:
        r = self.db.query(DSARRequest).filter(DSARRequest.id == request_id).first()
        if not r:
            return None
        r.identity_verified_at = datetime.now(timezone.utc)
        r.identity_verified_by = actor_user_id
        if r.status == DSARStatus.VERIFYING_IDENTITY:
            r.status = DSARStatus.PROCESSING
        self.db.commit()
        self.db.refresh(r)
        return r

    def mark_delivered(
        self,
        request_id: int,
        *,
        delivery_method: str,
        file_path: Optional[str] = None,
        file_sha256: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        actor_user_id: Optional[int] = None,
    ) -> Optional[DSARRequest]:
        r = self.db.query(DSARRequest).filter(DSARRequest.id == request_id).first()
        if not r:
            return None
        # If raw bytes are provided, hash them; otherwise trust the caller's hash.
        if file_bytes is not None and not file_sha256:
            file_sha256 = hashlib.sha256(file_bytes).hexdigest()
        r.status = DSARStatus.DELIVERED
        r.delivery_method = delivery_method
        r.delivered_at = datetime.now(timezone.utc)
        r.delivered_by = actor_user_id
        r.delivered_file_path = file_path
        r.delivered_file_sha256 = file_sha256
        r.closed_at = r.delivered_at
        self.db.commit()
        self.db.refresh(r)
        return r

    def list(
        self,
        status: Optional[DSARStatus] = None,
        kind: Optional[DSARKind] = None,
        overdue_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[DSARRequest], int]:
        q = self.db.query(DSARRequest)
        if status:
            q = q.filter(DSARRequest.status == status)
        if kind:
            q = q.filter(DSARRequest.kind == kind)
        if overdue_only:
            now = datetime.now(timezone.utc)
            q = q.filter(DSARRequest.due_date < now)
            q = q.filter(
                DSARRequest.status.notin_(
                    [DSARStatus.DELIVERED, DSARStatus.REJECTED]
                )
            )
        total = q.count()
        rows = (
            q.order_by(DSARRequest.received_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return rows, total


# --------------------------- Consent ---------------------------


class ConsentService:
    def __init__(self, db: Session):
        self.db = db

    def publish_version(
        self,
        *,
        kind: ConsentKind,
        version_label: str,
        body: str,
        effective_at: Optional[datetime] = None,
        created_by: Optional[int] = None,
    ) -> ConsentVersion:
        # Deprecate any prior active version of the same kind.
        now = datetime.now(timezone.utc)
        prior = (
            self.db.query(ConsentVersion)
            .filter(ConsentVersion.kind == kind)
            .filter(ConsentVersion.deprecated_at.is_(None))
            .all()
        )
        for p in prior:
            p.deprecated_at = now
        v = ConsentVersion(
            kind=kind,
            version_label=version_label,
            body=body,
            body_sha256=hashlib.sha256(body.encode("utf-8")).hexdigest(),
            effective_at=effective_at or now,
            created_by=created_by,
        )
        self.db.add(v)
        self.db.commit()
        self.db.refresh(v)
        return v

    def latest_version(self, kind: ConsentKind) -> Optional[ConsentVersion]:
        return (
            self.db.query(ConsentVersion)
            .filter(ConsentVersion.kind == kind)
            .filter(ConsentVersion.deprecated_at.is_(None))
            .order_by(ConsentVersion.effective_at.desc())
            .first()
        )

    def list_versions(
        self, kind: Optional[ConsentKind] = None
    ) -> List[ConsentVersion]:
        q = self.db.query(ConsentVersion)
        if kind:
            q = q.filter(ConsentVersion.kind == kind)
        return q.order_by(ConsentVersion.kind, ConsentVersion.effective_at.desc()).all()

    def record_acceptance(
        self,
        *,
        consent_version_id: int,
        guest_id: Optional[int] = None,
        subject_email: Optional[str] = None,
        accepted: bool = True,
        method: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ConsentRecord:
        r = ConsentRecord(
            consent_version_id=consent_version_id,
            guest_id=guest_id,
            subject_email=subject_email,
            accepted=accepted,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
        )
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        return r

    def history_for_guest(
        self, guest_id: int
    ) -> List[Tuple[ConsentRecord, ConsentVersion]]:
        rows = (
            self.db.query(ConsentRecord, ConsentVersion)
            .join(ConsentVersion, ConsentVersion.id == ConsentRecord.consent_version_id)
            .filter(ConsentRecord.guest_id == guest_id)
            .order_by(ConsentRecord.captured_at.desc())
            .all()
        )
        return rows
