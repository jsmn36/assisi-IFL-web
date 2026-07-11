"""
Posts Feed and Management API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, desc
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user, get_db
from app.models import User, Post, InstitutionProfile
from app.schemas import PostCreate, PostUpdate, PostResponse

router = APIRouter(prefix="/posts", tags=["Posts"])


def _hydrate_post_response(post: Post, db: Session) -> PostResponse:
    # Resolve the institution's display name
    from app.models.student import StudentProfile
    poster = db.query(User).filter(User.id == post.institution_id).first()
    inst_name = "Unknown User"
    if poster:
        if poster.role == "student":
            sp = db.query(StudentProfile).filter(StudentProfile.user_id == poster.id).first()
            inst_name = f"{poster.first_name or ''} {poster.last_name or ''}".strip() or poster.username
        else:
            profile = db.query(InstitutionProfile).filter(InstitutionProfile.user_id == post.institution_id).first()
            inst_name = profile.name if profile else poster.username
    
    return PostResponse(
        id=post.id,
        institution_id=post.institution_id,
        title=post.title,
        content=post.content,
        type=post.type,
        media_url=post.media_url,
        is_pinned=post.is_pinned,
        hashtags=post.hashtags,
        created_at=post.created_at,
        updated_at=post.updated_at,
        institution_name=inst_name
    )


@router.get("", response_model=List[PostResponse])
async def list_posts(
    institution_id: Optional[int] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Fetch public timeline of posts with advanced search, categories, and pinning sorting"""
    query = db.query(Post)

    if institution_id is not None:
        query = query.filter(Post.institution_id == institution_id)
        
    if type is not None:
        query = query.filter(Post.type == type)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Post.title.ilike(search_filter),
                Post.content.ilike(search_filter),
                Post.hashtags.ilike(search_filter)
            )
        )

    # Sort: pinned notices first, then newest first
    query = query.order_by(desc(Post.is_pinned), desc(Post.created_at))
    posts = query.offset(skip).limit(limit).all()

    return [_hydrate_post_response(post, db) for post in posts]


@router.get("/{id}", response_model=PostResponse)
async def get_post(id: int, db: Session = Depends(get_db)):
    """Fetch details of a single post"""
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return _hydrate_post_response(post, db)


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    payload: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["institution", "admin", "student"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only institutions, admins, or students can create posts"
        )

    post = Post(
        institution_id=current_user.id,
        title=payload.title,
        content=payload.content,
        type=payload.type,
        media_url=payload.media_url,
        is_pinned=payload.is_pinned,
        hashtags=payload.hashtags
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return _hydrate_post_response(post, db)


@router.put("/{id}", response_model=PostResponse)
async def update_post(
    id: int,
    payload: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Modify details of a post (Auth required: Owner Institution or Admin)"""
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Permission check: must be owner or super admin
    if not current_user.is_superuser and current_user.id != post.institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this post"
        )

    update_data = payload.dict(exclude_unset=True)
    for key, val in update_data.items():
        setattr(post, key, val)

    db.commit()
    db.refresh(post)

    return _hydrate_post_response(post, db)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a post (Auth required: Owner Institution or Admin)"""
    post = db.query(Post).filter(Post.id == id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Permission check: must be owner or super admin
    if not current_user.is_superuser and current_user.id != post.institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this post"
        )

    db.delete(post)
    db.commit()
    return
