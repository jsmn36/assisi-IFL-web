"""
Stories and Highlights API Endpoints
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.api.dependencies import get_current_user, get_db
from app.models import User
from app.models.student import StudentProfile
from app.models.stories import Story, Highlight, HighlightStory
from app.models.social_relations import Follow
from app.schemas import StoryCreate, StoryResponse, HighlightCreate, HighlightResponse

router = APIRouter(tags=["Stories & Highlights"])


@router.post("/stories", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(
    payload: StoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Publish a temporary story (expires after 24 hours)"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        story = Story(
            user_id=current_user.id,
            media_url=payload.media_url,
            type=payload.type,
            created_at=datetime.now(timezone.utc)
        )
        db.add(story)
        db.commit()
        db.refresh(story)

        # Get profile pic
        sp = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        profile_pic = sp.profile_pic_url if sp else None

    return StoryResponse(
        id=story.id,
        user_id=story.user_id,
        username=current_user.username,
        user_profile_pic=profile_pic,
        media_url=story.media_url,
        type=story.type,
        created_at=story.created_at
    )


@router.get("/stories/active")
async def get_active_stories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve active stories from followed users and self, grouped by user"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        # Active stories are created in the last 24 hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        # Get user IDs of followed users
        follows = db.query(Follow).filter(Follow.follower_id == current_user.id).all()
        followed_ids = [f.following_id for f in follows]
        followed_ids.append(current_user.id)  # Include self

        stories = db.query(Story).filter(
            Story.user_id.in_(followed_ids),
            Story.created_at >= cutoff
        ).order_by(Story.created_at.asc()).all()

        # Group stories by user
        grouped_stories: Dict[int, Dict[str, Any]] = {}
        for s in stories:
            u_id = s.user_id
            if u_id not in grouped_stories:
                user = db.query(User).filter(User.id == u_id).first()
                if not user:
                    continue
                sp = db.query(StudentProfile).filter(StudentProfile.user_id == u_id).first()
                grouped_stories[u_id] = {
                    "user_id": u_id,
                    "username": user.username,
                    "user_profile_pic": sp.profile_pic_url if sp else None,
                    "stories": []
                }

            grouped_stories[u_id]["stories"].append(StoryResponse(
                id=s.id,
                user_id=s.user_id,
                username=grouped_stories[u_id]["username"],
                user_profile_pic=grouped_stories[u_id]["user_profile_pic"],
                media_url=s.media_url,
                type=s.type,
                created_at=s.created_at
            ))

    return list(grouped_stories.values())


# ─── Highlights ──────────────────────────────────────────────────────────
@router.post("/highlights", response_model=HighlightResponse, status_code=status.HTTP_201_CREATED)
async def create_highlight(
    payload: HighlightCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new profile Highlight from a collection of stories"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        highlight = Highlight(
            user_id=current_user.id,
            name=payload.name,
            cover_url=payload.cover_url
        )
        db.add(highlight)
        db.flush()

        # Add stories
        story_responses = []
        for s_id in payload.story_ids:
            story = db.query(Story).filter(Story.id == s_id, Story.user_id == current_user.id).first()
            if story:
                hs = HighlightStory(highlight_id=highlight.id, story_id=story.id)
                db.add(hs)

                sp = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
                profile_pic = sp.profile_pic_url if sp else None

                story_responses.append(StoryResponse(
                    id=story.id,
                    user_id=story.user_id,
                    username=current_user.username,
                    user_profile_pic=profile_pic,
                    media_url=story.media_url,
                    type=story.type,
                    created_at=story.created_at
                ))

        db.commit()
        db.refresh(highlight)

    return HighlightResponse(
        id=highlight.id,
        user_id=highlight.user_id,
        name=highlight.name,
        cover_url=highlight.cover_url,
        stories=story_responses
    )


@router.get("/highlights/{user_id}", response_model=List[HighlightResponse])
async def get_highlights(user_id: int, db: Session = Depends(get_db)):
    """Fetch all highlights for a specific user"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        highlights = db.query(Highlight).filter(Highlight.user_id == user_id).order_by(Highlight.created_at.desc()).all()
        results = []

        for h in highlights:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                continue
            sp = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
            profile_pic = sp.profile_pic_url if sp else None

            stories = []
            for hs in h.highlight_stories:
                s = hs.story
                if s:
                    stories.append(StoryResponse(
                        id=s.id,
                        user_id=s.user_id,
                        username=user.username,
                        user_profile_pic=profile_pic,
                        media_url=s.media_url,
                        type=s.type,
                        created_at=s.created_at
                    ))

            results.append(HighlightResponse(
                id=h.id,
                user_id=h.user_id,
                name=h.name,
                cover_url=h.cover_url,
                stories=stories
            ))

    return results
