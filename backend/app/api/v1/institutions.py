"""
Institutions API Endpoints
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, get_db
from app.models import User, InstitutionProfile
from app.schemas import InstitutionProfileResponse, InstitutionProfileUpdate

router = APIRouter(prefix="/institutions", tags=["Institutions"])


@router.get("", response_model=List[InstitutionProfileResponse])
async def list_institutions(db: Session = Depends(get_db)):
    """Fetch public list of all registered institutions"""
    profiles = db.query(InstitutionProfile).all()
    return profiles


@router.get("/{id}", response_model=InstitutionProfileResponse)
async def get_institution(id: int, db: Session = Depends(get_db)):
    """Fetch profile details of a single institution"""
    profile = db.query(InstitutionProfile).filter(InstitutionProfile.id == id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution profile not found"
        )
    return profile


@router.put("/{id}", response_model=InstitutionProfileResponse)
async def update_institution(
    id: int,
    payload: InstitutionProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile data of own institution (Auth required)"""
    profile = db.query(InstitutionProfile).filter(InstitutionProfile.id == id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution profile not found"
        )

    # Permission check: must be either super admin or the owner of this profile
    if not current_user.is_superuser and current_user.id != profile.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this profile"
        )

    # Apply updates
    update_data = payload.dict(exclude_unset=True)
    for key, val in update_data.items():
        setattr(profile, key, val)

    db.commit()
    db.refresh(profile)
    return profile
