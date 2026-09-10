from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# User & Auth Schemas
class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = "institution"  # admin, institution


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str
    institution_id: Optional[int] = None


# Institution Profile Schemas
class InstitutionProfileCreate(BaseModel):
    name: str
    location: Optional[str] = None
    about: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website_url: Optional[str] = None
    social_links: Optional[str] = None  # JSON serialized string


class InstitutionProfileUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    about: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website_url: Optional[str] = None
    social_links: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None


class InstitutionProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str
    location: Optional[str] = None
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    about: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website_url: Optional[str] = None
    social_links: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Post Schemas
class PostCreate(BaseModel):
    title: str
    content: Optional[str] = None
    type: str = "news"  # image, video, pdf, notice, announcement, event, news
    media_url: Optional[str] = None
    is_pinned: bool = False
    hashtags: Optional[str] = None


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None
    media_url: Optional[str] = None
    is_pinned: Optional[bool] = None
    hashtags: Optional[str] = None


class PostResponse(BaseModel):
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

    class Config:
        from_attributes = True


# Admin Panel & Platform Analytics Schemas
class AnalyticsResponse(BaseModel):
    total_posts: int
    total_institutions: int
    post_types_count: Dict[str, int]
    posts_by_institution: List[Dict[str, Any]]


# Student Profile Schemas
class StudentProfileResponse(BaseModel):
    id: int
    user_id: int
    admission_number: str
    bio: Optional[str] = None
    profile_pic_url: Optional[str] = None
    cover_photo_url: Optional[str] = None
    class_or_department: Optional[str] = None
    privacy_settings: str
    username: str
    student_name: str

    class Config:
        from_attributes = True


class StudentProfileUpdate(BaseModel):
    bio: Optional[str] = None
    profile_pic_url: Optional[str] = None
    cover_photo_url: Optional[str] = None
    class_or_department: Optional[str] = None
    privacy_settings: Optional[str] = None


# Post Like & Comment Schemas
class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    username: str
    user_profile_pic: Optional[str] = None
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# Story & Highlight Schemas
class StoryCreate(BaseModel):
    media_url: str
    type: str = "image"


class StoryResponse(BaseModel):
    id: int
    user_id: int
    username: str
    user_profile_pic: Optional[str] = None
    media_url: str
    type: str
    created_at: datetime

    class Config:
        from_attributes = True


class HighlightCreate(BaseModel):
    name: str
    cover_url: Optional[str] = None
    story_ids: List[int] = []


class HighlightResponse(BaseModel):
    id: int
    user_id: int
    name: str
    cover_url: Optional[str] = None
    stories: List[StoryResponse] = []

    class Config:
        from_attributes = True


# Chat Message Schemas
class MessageCreate(BaseModel):
    receiver_id: int
    content: str


class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    is_encrypted: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Group & Classroom Schemas
class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_classroom: bool = False
    class_or_department: Optional[str] = None


class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_by: int
    is_classroom: bool
    class_or_department: Optional[str] = None
    created_at: datetime
    member_count: int = 0

    class Config:
        from_attributes = True


class AssignmentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    file_url: Optional[str] = None
    due_date: Optional[datetime] = None


class AssignmentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    file_url: Optional[str] = None
    due_date: Optional[datetime] = None
    group_id: int
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: datetime
    location: Optional[str] = None
    group_id: Optional[int] = None


class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    date: datetime
    location: Optional[str] = None
    group_id: Optional[int] = None
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True
