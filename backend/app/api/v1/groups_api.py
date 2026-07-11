"""
Groups, Classrooms, Assignments, and Events API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.models.student import StudentProfile
from app.models.groups import Group, GroupMember, Event, Assignment
from app.schemas import GroupCreate, GroupResponse, AssignmentCreate, AssignmentResponse, EventCreate, EventResponse

router = APIRouter(tags=["Groups & Classrooms"])


@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    payload: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new community group or academic classroom"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        group = Group(
            name=payload.name,
            description=payload.description,
            created_by=current_user.id,
            is_classroom=payload.is_classroom,
            class_or_department=payload.class_or_department
        )
        db.add(group)
        db.flush()

        # Join the creator immediately as admin
        member = GroupMember(
            group_id=group.id,
            user_id=current_user.id,
            role="admin"
        )
        db.add(member)
        db.commit()
        db.refresh(group)

    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_by=group.created_by,
        is_classroom=group.is_classroom,
        class_or_department=group.class_or_department,
        created_at=group.created_at,
        member_count=1
    )


@router.get("/groups", response_model=List[GroupResponse])
async def list_groups(
    joined_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List groups/classrooms (either joined ones or all discoverable ones)"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        if joined_only:
            memberships = db.query(GroupMember).filter(GroupMember.user_id == current_user.id).all()
            group_ids = [m.group_id for m in memberships]
            groups = db.query(Group).filter(Group.id.in_(group_ids)).all()
        else:
            groups = db.query(Group).all()

        results = []
        for g in groups:
            m_count = db.query(GroupMember).filter(GroupMember.group_id == g.id).count()
            results.append(GroupResponse(
                id=g.id,
                name=g.name,
                description=g.description,
                created_by=g.created_by,
                is_classroom=g.is_classroom,
                class_or_department=g.class_or_department,
                created_at=g.created_at,
                member_count=m_count
            ))

    return results


@router.post("/groups/{group_id}/join", status_code=status.HTTP_200_OK)
async def join_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join a community group or classroom"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        # Check if already a member
        member = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        ).first()

        if member:
            return {"message": "You are already a member of this group"}

        new_member = GroupMember(
            group_id=group_id,
            user_id=current_user.id,
            role="member"
        )
        db.add(new_member)
        db.commit()

    return {"message": f"Successfully joined group {group.name}"}


@router.post("/groups/{group_id}/leave", status_code=status.HTTP_200_OK)
async def leave_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Leave a group/classroom"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        member = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        ).first()

        if not member:
            raise HTTPException(status_code=404, detail="You are not a member of this group")

        db.delete(member)
        db.commit()

    return {"message": "Successfully left group"}


@router.get("/groups/{group_id}/members")
async def list_group_members(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List members of a group/classroom (requires membership to view)"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        # Membership check
        is_member = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        ).first() is not None

        if not is_member and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="You must be a member of this group to view its members list")

        memberships = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
        results = []
        for m in memberships:
            user = db.query(User).filter(User.id == m.user_id).first()
            if user:
                sp = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
                results.append({
                    "id": user.id,
                    "username": user.username,
                    "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username,
                    "profile_pic_url": sp.profile_pic_url if sp else None,
                    "role": m.role,
                    "joined_at": m.joined_at
                })

    return results


# ─── Assignments ────────────────────────────────────────────────────────
@router.post("/groups/{group_id}/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    group_id: int,
    payload: AssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an assignment or share study materials inside a classroom"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        # Check if classroom exists and if user is member
        group = db.query(Group).filter(Group.id == group_id, Group.is_classroom == True).first()
        if not group:
            raise HTTPException(status_code=404, detail="Classroom group not found")

        member = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        ).first()

        if not member:
            raise HTTPException(status_code=403, detail="You are not a member of this classroom")

        assignment = Assignment(
            title=payload.title,
            description=payload.description,
            file_url=payload.file_url,
            due_date=payload.due_date,
            group_id=group_id,
            created_by=current_user.id
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)

    return AssignmentResponse(
        id=assignment.id,
        title=assignment.title,
        description=assignment.description,
        file_url=assignment.file_url,
        due_date=assignment.due_date,
        group_id=assignment.group_id,
        created_by=assignment.created_by,
        created_at=assignment.created_at
    )


@router.get("/groups/{group_id}/assignments", response_model=List[AssignmentResponse])
async def list_assignments(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all assignments inside a classroom"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        member = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        ).first()

        if not member and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="You must be a member of this classroom to view assignments")

        assignments = db.query(Assignment).filter(Assignment.group_id == group_id).order_by(Assignment.created_at.desc()).all()

    return [
        AssignmentResponse(
            id=a.id,
            title=a.title,
            description=a.description,
            file_url=a.file_url,
            due_date=a.due_date,
            group_id=a.group_id,
            created_by=a.created_by,
            created_at=a.created_at
        )
        for a in assignments
    ]


# ─── Events ─────────────────────────────────────────────────────────────
@router.post("/groups/{group_id}/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    group_id: int,
    payload: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a classroom event (tests, schedules, deadlines)"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        member = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        ).first()

        if not member:
            raise HTTPException(status_code=403, detail="You are not a member of this group")

        event = Event(
            title=payload.title,
            description=payload.description,
            date=payload.date,
            location=payload.location,
            created_by=current_user.id,
            group_id=group_id
        )
        db.add(event)
        db.commit()
        db.refresh(event)

    return EventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        date=event.date,
        location=event.location,
        group_id=event.group_id,
        created_by=event.created_by,
        created_at=event.created_at
    )


@router.get("/groups/{group_id}/events", response_model=List[EventResponse])
async def list_events(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List upcoming events of a classroom/group"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        member = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == current_user.id
        ).first()

        if not member and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="You must be a member of this group to view events")

        events = db.query(Event).filter(Event.group_id == group_id).order_by(Event.date.asc()).all()

    return [
        EventResponse(
            id=e.id,
            title=e.title,
            description=e.description,
            date=e.date,
            location=e.location,
            group_id=e.group_id,
            created_by=e.created_by,
            created_at=e.created_at
        )
        for e in events
    ]
