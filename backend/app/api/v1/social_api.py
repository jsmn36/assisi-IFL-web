"""
Social Interactions API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_, desc, and_
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.dependencies import get_current_user, get_db
from app.models import User, Post, InstitutionProfile
from app.models.student import StudentAdmission, StudentProfile
from app.models.social_relations import Follow, PostLike, PostComment
from app.schemas import StudentProfileResponse, StudentProfileUpdate, CommentResponse, CommentCreate

router = APIRouter(tags=["Student Social"])


class StudentPostResponse(BaseModel):
    id: int
    institution_id: int
    title: str
    content: Optional[str] = None
    type: str
    media_url: Optional[str] = None
    is_pinned: bool
    hashtags: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    institution_name: Optional[str] = None
    likes_count: int = 0
    comments_count: int = 0
    has_liked: bool = False
    avatar_url: Optional[str] = None


def _hydrate_student_post(post: Post, current_user_id: int, db: Session) -> StudentPostResponse:
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        poster = db.query(User).filter(User.id == post.institution_id).first()
        inst_name = "Unknown User"
        avatar_url = None
        if poster:
            if poster.role == "student":
                sp = db.query(StudentProfile).filter(StudentProfile.user_id == poster.id).first()
                inst_name = f"{poster.first_name or ''} {poster.last_name or ''}".strip() or poster.username
                avatar_url = sp.profile_pic_url if sp else None
            else:
                ip = db.query(InstitutionProfile).filter(InstitutionProfile.user_id == poster.id).first()
                inst_name = ip.name if ip else poster.username
                avatar_url = ip.logo_url if ip else None

        # Likes & comments count
        likes_count = db.query(PostLike).filter(PostLike.post_id == post.id).count()
        comments_count = db.query(PostComment).filter(PostComment.post_id == post.id).count()
        has_liked = db.query(PostLike).filter(PostLike.post_id == post.id, PostLike.user_id == current_user_id).first() is not None

    return StudentPostResponse(
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
        institution_name=inst_name,
        likes_count=likes_count,
        comments_count=comments_count,
        has_liked=has_liked,
        avatar_url=avatar_url
    )


# ─── Profiles ──────────────────────────────────────────────────────────
@router.get("/students/profile/{username}", response_model=StudentProfileResponse)
async def get_student_profile(username: str, db: Session = Depends(get_db)):
    """Retrieve profile details for a student by their username"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        user = db.query(User).filter(User.username == username, User.role == "student").first()
        if not user:
            raise HTTPException(status_code=404, detail="Student user not found")

        sp = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
        if not sp:
            raise HTTPException(status_code=404, detail="Student profile not found")

        # Resolve student name
        student_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username

    return StudentProfileResponse(
        id=sp.id,
        user_id=sp.user_id,
        admission_number=sp.admission_number,
        bio=sp.bio,
        profile_pic_url=sp.profile_pic_url,
        cover_photo_url=sp.cover_photo_url,
        class_or_department=sp.class_or_department,
        privacy_settings=sp.privacy_settings,
        username=user.username,
        student_name=student_name
    )


@router.put("/students/profile", response_model=StudentProfileResponse)
async def update_student_profile(
    payload: StudentProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile details for the currently logged-in student"""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can have student profiles")

    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        sp = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        if not sp:
            raise HTTPException(status_code=404, detail="Student profile not found")

        update_data = payload.dict(exclude_unset=True)
        for key, val in update_data.items():
            setattr(sp, key, val)

        db.commit()
        db.refresh(sp)
        student_name = f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or current_user.username

    return StudentProfileResponse(
        id=sp.id,
        user_id=sp.user_id,
        admission_number=sp.admission_number,
        bio=sp.bio,
        profile_pic_url=sp.profile_pic_url,
        cover_photo_url=sp.cover_photo_url,
        class_or_department=sp.class_or_department,
        privacy_settings=sp.privacy_settings,
        username=current_user.username,
        student_name=student_name
    )


# ─── Search ─────────────────────────────────────────────────────────────
@router.get("/students/search")
async def search_social(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """Search for students by username/name or posts by title/hashtags/locations"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        # Search users
        search_pattern = f"%{q}%"
        users = db.query(User).filter(
            and_(
                User.role == "student",
                User.is_active == True,
                or_(
                    User.username.ilike(search_pattern),
                    User.first_name.ilike(search_pattern),
                    User.last_name.ilike(search_pattern)
                )
            )
        ).limit(10).all()

        user_results = []
        for u in users:
            sp = db.query(StudentProfile).filter(StudentProfile.user_id == u.id).first()
            user_results.append({
                "id": u.id,
                "username": u.username,
                "name": f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username,
                "profile_pic_url": sp.profile_pic_url if sp else None,
                "class_or_department": sp.class_or_department if sp else None
            })

        # Search posts
        posts = db.query(Post).filter(
            or_(
                Post.title.ilike(search_pattern),
                Post.content.ilike(search_pattern),
                Post.hashtags.ilike(search_pattern)
            )
        ).order_by(desc(Post.created_at)).limit(10).all()

    return {
        "users": user_results,
        "posts": [
            {
                "id": p.id,
                "title": p.title,
                "content": p.content,
                "media_url": p.media_url,
                "type": p.type,
                "hashtags": p.hashtags,
                "created_at": p.created_at
            }
            for p in posts
        ]
    }


# ─── Follow System ──────────────────────────────────────────────────────
@router.post("/students/follow/{user_id}", status_code=status.HTTP_200_OK)
async def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Follow another student or institution"""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")

    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")

        # Check if already following
        existing_follow = db.query(Follow).filter(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id
        ).first()

        if existing_follow:
            return {"message": "You are already following this user"}

        follow = Follow(follower_id=current_user.id, following_id=user_id)
        db.add(follow)
        db.commit()

    return {"message": f"Successfully followed {target_user.username}"}


@router.post("/students/unfollow/{user_id}", status_code=status.HTTP_200_OK)
async def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unfollow a student or institution"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        follow = db.query(Follow).filter(
            Follow.follower_id == current_user.id,
            Follow.following_id == user_id
        ).first()

        if not follow:
            raise HTTPException(status_code=404, detail="You are not following this user")

        db.delete(follow)
        db.commit()

    return {"message": "Successfully unfollowed user"}


@router.get("/students/followers/{user_id}")
async def get_followers(user_id: int, db: Session = Depends(get_db)):
    """Get the list of followers of a user"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        follows = db.query(Follow).filter(Follow.following_id == user_id).all()
        results = []
        for f in follows:
            u = db.query(User).filter(User.id == f.follower_id).first()
            if u:
                sp = db.query(StudentProfile).filter(StudentProfile.user_id == u.id).first()
                results.append({
                    "id": u.id,
                    "username": u.username,
                    "name": f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username,
                    "profile_pic_url": sp.profile_pic_url if sp else None
                })
    return results


@router.get("/students/following/{user_id}")
async def get_following(user_id: int, db: Session = Depends(get_db)):
    """Get the list of accounts a user follows"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        follows = db.query(Follow).filter(Follow.follower_id == user_id).all()
        results = []
        for f in follows:
            u = db.query(User).filter(User.id == f.following_id).first()
            if u:
                sp = db.query(StudentProfile).filter(StudentProfile.user_id == u.id).first()
                results.append({
                    "id": u.id,
                    "username": u.username,
                    "name": f"{u.first_name or ''} {u.last_name or ''}".strip() or u.username,
                    "profile_pic_url": sp.profile_pic_url if sp else None
                })
    return results


# ─── Likes & Comments ───────────────────────────────────────────────────
@router.post("/posts/{post_id}/like")
async def toggle_like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle a like on a post"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        like = db.query(PostLike).filter(
            PostLike.post_id == post_id,
            PostLike.user_id == current_user.id
        ).first()

        if like:
            db.delete(like)
            db.commit()
            return {"liked": False, "message": "Post unliked"}
        else:
            new_like = PostLike(post_id=post_id, user_id=current_user.id)
            db.add(new_like)
            db.commit()
            return {"liked": True, "message": "Post liked"}


@router.post("/posts/{post_id}/comment", response_model=CommentResponse)
async def comment_on_post(
    post_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Comment on a post"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        comment = PostComment(
            post_id=post_id,
            user_id=current_user.id,
            content=payload.content
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)

        # Get profile pic
        sp = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        profile_pic = sp.profile_pic_url if sp else None
        username = current_user.username

    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        username=username,
        user_profile_pic=profile_pic,
        content=comment.content,
        created_at=comment.created_at
    )


@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def list_post_comments(post_id: int, db: Session = Depends(get_db)):
    """Fetch comments on a specific post"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        comments = db.query(PostComment).filter(PostComment.post_id == post_id).order_by(PostComment.created_at.asc()).all()
        results = []
        for c in comments:
            user = db.query(User).filter(User.id == c.user_id).first()
            if user:
                sp = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
                profile_pic = sp.profile_pic_url if sp else None
                results.append(CommentResponse(
                    id=c.id,
                    post_id=c.post_id,
                    user_id=c.user_id,
                    username=user.username,
                    user_profile_pic=profile_pic,
                    content=c.content,
                    created_at=c.created_at
                ))
    return results


# ─── Social Feed ────────────────────────────────────────────────────────
@router.get("/posts/student-feed", response_model=List[StudentPostResponse])
async def get_student_feed(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve posts feed customized for a student user"""
    from app.core.tenant_context import bypass_tenant_filter
    with bypass_tenant_filter():
        # Get user IDs of who they follow
        following = db.query(Follow).filter(Follow.follower_id == current_user.id).all()
        following_ids = [f.following_id for f in following]
        following_ids.append(current_user.id)  # Include self

        # Query posts:
        # Show posts made by followed users, OR notice/announcements posted by institutions/admins
        query = db.query(Post).join(User, User.id == Post.institution_id)
        query = query.filter(
            or_(
                Post.institution_id.in_(following_ids),
                User.role.in_(["institution", "admin"])
            )
        )

        query = query.order_by(desc(Post.is_pinned), desc(Post.created_at))
        posts = query.offset(skip).limit(limit).all()

        return [_hydrate_student_post(post, current_user.id, db) for post in posts]
