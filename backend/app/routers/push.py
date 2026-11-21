import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Session

from ..config import settings
from ..database import Base, SessionLocal, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/push", tags=["push"])


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(Text, unique=True, nullable=False)
    p256dh = Column(String(255), nullable=False)
    auth = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SubKeys(BaseModel):
    p256dh: str
    auth: str


class SubscriptionIn(BaseModel):
    endpoint: str
    keys: SubKeys


class UnsubscribeIn(BaseModel):
    endpoint: str


@router.get("/public-key")
def public_key() -> dict[str, str]:
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=503, detail="Push not configured")
    return {"publicKey": settings.VAPID_PUBLIC_KEY}


@router.post("/subscribe")
def subscribe(sub: SubscriptionIn, db: Session = Depends(get_db)) -> dict[str, str]:
    existing = db.query(PushSubscription).filter_by(endpoint=sub.endpoint).first()
    if existing:
        existing.p256dh = sub.keys.p256dh
        existing.auth = sub.keys.auth
    else:
        db.add(PushSubscription(endpoint=sub.endpoint, p256dh=sub.keys.p256dh, auth=sub.keys.auth))
    db.commit()
    return {"status": "subscribed"}


@router.post("/unsubscribe")
def unsubscribe(body: UnsubscribeIn, db: Session = Depends(get_db)) -> dict[str, str]:
    db.query(PushSubscription).filter_by(endpoint=body.endpoint).delete()
    db.commit()
    return {"status": "unsubscribed"}


def send_to_all(title: str, body: str, url: str = "/") -> None:
    """Send a push to every subscriber. Runs as a background task."""
    if not (settings.VAPID_PRIVATE_KEY and settings.VAPID_PUBLIC_KEY):
        logger.info("VAPID keys not set; skipping push")
        return
    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        logger.warning("pywebpush not installed; skipping push")
        return

    payload = json.dumps({"title": title, "body": body, "url": url})
    db = SessionLocal()
    try:
        for s in db.query(PushSubscription).all():
            try:
                webpush(
                    subscription_info={"endpoint": s.endpoint, "keys": {"p256dh": s.p256dh, "auth": s.auth}},
                    data=payload,
                    vapid_private_key=settings.VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": settings.VAPID_SUBJECT},
                    ttl=86400,
                )
            except WebPushException as e:
                code = getattr(e.response, "status_code", None)
                if code in (404, 410):
                    db.delete(s)
                else:
                    logger.warning("Push failed: %s", e)
        db.commit()
    finally:
        db.close()
