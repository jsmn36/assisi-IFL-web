"""
Chat and Direct Messaging API Endpoints
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, and_, desc
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.models.student import StudentProfile
from app.models.social_relations import Message
from app.schemas import MessageCreate, MessageResponse

router = APIRouter(tags=["Chat / Direct Messaging"])


@router.post("/chat/send", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a private direct message to another student/user"""
    if current_user.id == payload.receiver_id:
        raise HTTPException(status_code=400, detail="You cannot message yourself")

    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        recipient = db.query(User).filter(User.id == payload.receiver_id).first()
        if not recipient:
            raise HTTPException(status_code=404, detail="Recipient user not found")

        message = Message(
            sender_id=current_user.id,
            receiver_id=payload.receiver_id,
            content=payload.content,
            is_encrypted=False
        )
        db.add(message)
        db.commit()
        db.refresh(message)

    return MessageResponse(
        id=message.id,
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        content=message.content,
        is_encrypted=message.is_encrypted,
        created_at=message.created_at
    )


@router.get("/chat/history/{partner_id}", response_model=List[MessageResponse])
async def get_chat_history(
    partner_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full message history between current user and chat partner"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        partner = db.query(User).filter(User.id == partner_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Partner user not found")

        messages = db.query(Message).filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == partner_id),
                and_(Message.sender_id == partner_id, Message.receiver_id == current_user.id)
            )
        ).order_by(Message.created_at.asc()).all()

    return [
        MessageResponse(
            id=m.id,
            sender_id=m.sender_id,
            receiver_id=m.receiver_id,
            content=m.content,
            is_encrypted=m.is_encrypted,
            created_at=m.created_at
        )
        for m in messages
    ]


@router.get("/chat/conversations")
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all active direct message conversation threads for the current user"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        # Get all messages involving the current user
        all_messages = db.query(Message).filter(
            or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
        ).order_by(Message.created_at.desc()).all()

        # Group by partner and get the latest message
        threads: Dict[int, Dict[str, Any]] = {}
        for m in all_messages:
            partner_id = m.receiver_id if m.sender_id == current_user.id else m.sender_id
            if partner_id not in threads:
                partner = db.query(User).filter(User.id == partner_id).first()
                if not partner:
                    continue
                sp = db.query(StudentProfile).filter(StudentProfile.user_id == partner_id).first()
                threads[partner_id] = {
                    "id": partner_id,
                    "username": partner.username,
                    "name": f"{partner.first_name or ''} {partner.last_name or ''}".strip() or partner.username,
                    "profile_pic_url": sp.profile_pic_url if sp else None,
                    "last_message": m.content,
                    "last_message_time": m.created_at
                }

    # Sort conversations by last message time descending
    sorted_threads = sorted(threads.values(), key=lambda x: x["last_message_time"], reverse=True)
    return sorted_threads
