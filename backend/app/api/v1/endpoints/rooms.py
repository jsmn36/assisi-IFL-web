from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencies import get_db
from app import models, schemas

router = APIRouter()


@router.get("/available", response_model=List[schemas.Room])
def get_available_rooms(property_id: int, db: Session = Depends(get_db)):
    return db.query(models.Room).filter(models.Room.property_id == property_id).all()


@router.post("/{room_id}/clean")
def mark_room_clean(room_id: int, db: Session = Depends(get_db)):
    room = db.query(models.Room).filter(models.Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"success": True, "message": "Room marked as clean"}
