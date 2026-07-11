"""
Super Admin Management and Analytics API Endpoints
"""
import os
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.api.dependencies import get_current_user, get_db
from app.models import User, InstitutionProfile, Post, UserTenant
from app.models.tenant import DEFAULT_TENANT_ID
from app.schemas import AnalyticsResponse, InstitutionProfileResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/admin", tags=["Super Admin"])


class InstitutionRegisterPayload(BaseModel):
    username: str
    email: EmailStr
    password: str
    name: str
    about: str = ""
    contact_email: EmailStr = None
    phone: str = ""
    website_url: str = ""


@router.post("/institutions", response_model=InstitutionProfileResponse, status_code=status.HTTP_201_CREATED)
async def register_institution_account(
    payload: InstitutionRegisterPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Super Admin registers a new educational institution account & profile (Auth required: Admin)"""
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Super Admin role required."
        )

    auth_service = AuthService(db)
    
    # Create the user credentials
    try:
        user = auth_service.create_user(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            role="institution",
            created_by=current_user.username
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Create the profile record
    profile = InstitutionProfile(
        user_id=user.id,
        name=payload.name,
        about=payload.about,
        contact_email=payload.contact_email or payload.email,
        phone=payload.phone,
        website_url=payload.website_url,
        logo_url="https://images.unsplash.com/photo-1546410531-bb4caa6b424d?auto=format&fit=crop&q=80&w=200",  # Beautiful fallback
        banner_url="https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&q=80&w=1200"  # Beautiful banner fallback
    )
    
    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


@router.delete("/institutions/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_institution_account(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Super Admin deletes an institution account, cascading and removing all posts (Auth required: Admin)"""
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Super Admin role required."
        )

    profile = db.query(InstitutionProfile).filter(InstitutionProfile.id == id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution profile not found"
        )

    user = db.query(User).filter(User.id == profile.user_id).first()
    if user:
        db.delete(user)
        
    db.commit()
    return


# === Student Management ===
@router.get("/pending-students")
async def list_pending_students(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List student registration accounts pending institutional approval"""
    if current_user.role not in ["admin", "institution"] and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Institutional or Super Admin role required."
        )

    from app.models.student import StudentProfile
    from app.core.tenant_context import bypass_tenant_filter

    with bypass_tenant_filter():
        pending_users = db.query(User).filter(
            User.role == "student",
            User.is_active == False
        ).all()

        results = []
        for u in pending_users:
            sp = db.query(StudentProfile).filter(StudentProfile.user_id == u.id).first()
            results.append({
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "name": f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username,
                "admission_number": sp.admission_number if sp else "N/A",
                "class_or_department": sp.class_or_department if sp else "N/A",
                "created_at": u.created_at
            })
    return results


@router.post("/students/{user_id}/approve")
async def approve_student_registration(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a student account registration, enabling them to log in"""
    if current_user.role not in ["admin", "institution"] and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Institutional or Super Admin role required."
        )

    from app.models.student import StudentProfile, StudentAdmission
    from app.core.tenant_context import bypass_tenant_filter

    with bypass_tenant_filter():
        user = db.query(User).filter(User.id == user_id, User.role == "student").first()
        if not user:
            raise HTTPException(status_code=404, detail="Student not found")

        user.is_active = True
        
        sp = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
        if sp:
            admission = db.query(StudentAdmission).filter(StudentAdmission.admission_number == sp.admission_number).first()
            if admission:
                admission.is_registered = True

        db.commit()

    return {"message": f"Student {user.username} approved successfully"}


@router.post("/students/{user_id}/reject")
async def reject_student_registration(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a student account registration, deleting their user profile"""
    if current_user.role not in ["admin", "institution"] and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Institutional or Super Admin role required."
        )

    from app.models.student import StudentProfile
    from app.core.tenant_context import bypass_tenant_filter

    with bypass_tenant_filter():
        user = db.query(User).filter(User.id == user_id, User.role == "student").first()
        if not user:
            raise HTTPException(status_code=404, detail="Student not found")

        db.delete(user)
        db.commit()

    return {"message": f"Student registration for {user.username} rejected and deleted"}


@router.delete("/students/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student_account(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a student account completely"""
    if current_user.role not in ["admin", "institution"] and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Institutional or Super Admin role required."
        )

    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        user = db.query(User).filter(User.id == user_id, User.role == "student").first()
        if not user:
            raise HTTPException(status_code=404, detail="Student not found")

        db.delete(user)
        db.commit()

    return


@router.get("/students")
async def list_all_students(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all registered student accounts with details"""
    if current_user.role not in ["admin", "institution"] and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Institutional or Super Admin role required."
        )

    from app.models.student import StudentProfile
    from app.core.tenant_context import bypass_tenant_filter

    with bypass_tenant_filter():
        students = db.query(User).filter(User.role == "student").all()
        results = []
        for u in students:
            sp = db.query(StudentProfile).filter(StudentProfile.user_id == u.id).first()
            results.append({
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "name": f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username,
                "admission_number": sp.admission_number if sp else "N/A",
                "class_or_department": sp.class_or_department if sp else "N/A",
                "is_active": u.is_active,
                "created_at": u.created_at
            })
    return results


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_platform_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Super Admin fetches aggregated dashboard metrics and storage usage details (Auth required: Admin)"""
    if not current_user.is_superuser and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Super Admin role required."
        )

    total_posts = db.query(Post).count()
    total_institutions = db.query(InstitutionProfile).count()

    # Category breakdown
    post_types = ["image", "video", "pdf", "notice", "announcement", "event", "news"]
    post_types_count = {}
    for p_type in post_types:
        count = db.query(Post).filter(Post.type == p_type).count()
        post_types_count[p_type] = count

    # Group count by institution
    institutions = db.query(InstitutionProfile).all()
    posts_by_institution = []
    for inst in institutions:
        count = db.query(Post).filter(Post.institution_id == inst.user_id).count()
        posts_by_institution.append({
            "id": inst.id,
            "name": inst.name,
            "posts_count": count
        })

    return AnalyticsResponse(
        total_posts=total_posts,
        total_institutions=total_institutions,
        post_types_count=post_types_count,
        posts_by_institution=posts_by_institution
    )
