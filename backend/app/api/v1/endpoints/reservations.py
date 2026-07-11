from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencies import get_db
from app import models, schemas
from app.cm import schemas as cm_schemas
from app.services.reservation_service import ReservationService

router = APIRouter()


@router.post(
    "", response_model=schemas.Reservation, status_code=status.HTTP_201_CREATED
)
def create_reservation(
    reservation_in: schemas.ReservationCreate, db: Session = Depends(get_db)
):
    service = ReservationService(db)
    return service.create_reservation(reservation_in)


@router.get("/{reservation_id}", response_model=schemas.Reservation)
def get_reservation(reservation_id: int, db: Session = Depends(get_db)):
    res = (
        db.query(models.Reservation)
        .filter(models.Reservation.id == reservation_id)
        .first()
    )
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return res


@router.post("/{reservation_id}/confirm", response_model=schemas.Reservation)
def confirm_reservation(reservation_id: int, db: Session = Depends(get_db)):
    service = ReservationService(db)
    return service.confirm_reservation(reservation_id)
