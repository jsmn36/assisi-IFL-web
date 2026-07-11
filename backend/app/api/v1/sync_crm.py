from app.config import settings
import os
from fastapi import APIRouter, Depends, Query, status, Request, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.guest import Guest
from app.models.stay import Stay
from app.models.charge import Charge

router = APIRouter(prefix="/sync/crm", tags=["CRM Sync"])

# PMS_SERVICE_TOKEN is now used from settings


def get_sync_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        if settings.PMS_SERVICE_TOKEN and token == settings.PMS_SERVICE_TOKEN:
            return {"id": "system"}
    # fallback to standard auth
    from fastapi.security import HTTPBearer

    try:
        user = get_current_user(request, HTTPBearer(auto_error=False)(request), db)
        return user
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or service token",
        )


def item_to_dict(obj):
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    # Fallback to simple generic dump
    return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}


@router.get("/guests", status_code=status.HTTP_200_OK)
def sync_guests(
    request: Request,
    updated_since: datetime = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    user=Depends(get_sync_user),
):
    """Canonical incremental sync endpoint for CRM (Guests)."""
    query = db.query(Guest)
    if updated_since:
        if hasattr(Guest, "updated_at"):
            query = query.filter(Guest.updated_at >= updated_since)
        elif hasattr(Guest, "created_at"):
            query = query.filter(Guest.created_at >= updated_since)

    items = query.offset(skip).limit(limit).all()
    return {"items": [item_to_dict(i) for i in items]}


@router.get("/stays", status_code=status.HTTP_200_OK)
def sync_stays(
    request: Request,
    updated_since: datetime = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    user=Depends(get_sync_user),
):
    """Canonical incremental sync endpoint for CRM (Stays)."""
    query = db.query(Stay)
    if updated_since:
        if hasattr(Stay, "updated_at"):
            query = query.filter(Stay.updated_at >= updated_since)
        elif hasattr(Stay, "created_at"):
            query = query.filter(Stay.created_at >= updated_since)

    items = query.offset(skip).limit(limit).all()
    # Remap for CRM transformer safely
    res = []
    for i in items:
        base = item_to_dict(i)
        if "id" not in base:
            base["id"] = getattr(i, "id", None)
        if "guest_id" not in base:
            base["guest_id"] = getattr(i, "guest_id", None)
        if "total_amount" not in base:
            base["total_amount"] = getattr(i, "total_charges", 0)
        res.append(base)

    return {"items": res}


@router.get("/charges", status_code=status.HTTP_200_OK)
def sync_charges(
    request: Request,
    updated_since: datetime = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db),
    user=Depends(get_sync_user),
):
    """Canonical incremental sync endpoint for CRM (Charges)."""
    query = db.query(Charge)
    if updated_since:
        if hasattr(Charge, "updated_at"):
            query = query.filter(Charge.updated_at >= updated_since)
        elif hasattr(Charge, "created_at"):
            query = query.filter(Charge.created_at >= updated_since)

    items = query.offset(skip).limit(limit).all()
    return {"items": [item_to_dict(i) for i in items]}
