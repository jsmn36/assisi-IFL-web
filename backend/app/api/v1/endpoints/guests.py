from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.api.dependencies import get_db
from app import models, schemas

router = APIRouter()


@router.post("", response_model=schemas.Guest, status_code=status.HTTP_201_CREATED)
def create_guest(guest_in: schemas.GuestCreate, db: Session = Depends(get_db)):
    db_guest = models.Guest(**guest_in.model_dump())
    db.add(db_guest)
    db.commit()
    db.refresh(db_guest)
    return db_guest


@router.get("", response_model=List[schemas.Guest])
def search_guests(
    query: Optional[str] = None,
    updated_since: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(models.Guest)
    if query:
        q = q.filter(
            (models.Guest.last_name.icontains(query))
            | (models.Guest.first_name.icontains(query))
        )
    if updated_since:
        q = q.filter(models.Guest.updated_at >= updated_since)
    return q.all()


@router.get("/email/{email}", response_model=schemas.Guest)
def get_guest_by_email(email: str, db: Session = Depends(get_db)):
    guest = db.query(models.Guest).filter(models.Guest.email == email).first()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest
