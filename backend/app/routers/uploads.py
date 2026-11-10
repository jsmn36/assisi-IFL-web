from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy import Column, DateTime, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Session

from ..database import Base, get_db

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

router = APIRouter(prefix="/uploads", tags=["uploads"])


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, default="")
    type = Column(String(32), default="media")
    institution_name = Column(String(255), default="Assisi Institute")
    institution_id = Column(Integer, default=1)
    hashtags = Column(String(255), default="")
    media_data = Column(LargeBinary, nullable=True)
    media_content_type = Column(String(128), nullable=True)
    media_filename = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


def _serialize(u: Upload, request: Request) -> dict:
    media_url = None
    if u.media_data is not None:
        base = str(request.base_url).rstrip("/")
        if request.headers.get("x-forwarded-proto") == "https":
            base = base.replace("http://", "https://", 1)
        media_url = f"{base}/uploads/{u.id}/media"
    return {
        "id": u.id,
        "title": u.title,
        "content": u.content,
        "type": u.type,
        "institution_name": u.institution_name,
        "institution_id": u.institution_id,
        "hashtags": u.hashtags,
        "media_url": media_url,
        "media_content_type": u.media_content_type,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


@router.get("")
def list_uploads(request: Request, db: Session = Depends(get_db)) -> list[dict]:
    items = db.query(Upload).order_by(Upload.created_at.desc()).all()
    return [_serialize(u, request) for u in items]


@router.post("")
async def create_upload(
    request: Request,
    title: str = Form(...),
    content: str = Form(""),
    type: str = Form("media"),
    institution_name: str = Form("Assisi Institute"),
    institution_id: int = Form(1),
    hashtags: str = Form(""),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
) -> dict:
    data = None
    if file is not None:
        data = await file.read()
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large (max 50MB)")
    u = Upload(
        title=title,
        content=content,
        type=type,
        institution_name=institution_name,
        institution_id=institution_id,
        hashtags=hashtags,
        media_data=data,
        media_content_type=file.content_type if file else None,
        media_filename=file.filename if file else None,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return _serialize(u, request)


@router.get("/{upload_id}/media")
def get_media(upload_id: int, db: Session = Depends(get_db)) -> Response:
    u = db.get(Upload, upload_id)
    if not u or u.media_data is None:
        raise HTTPException(status_code=404, detail="Media not found")
    return Response(
        content=u.media_data,
        media_type=u.media_content_type or "application/octet-stream",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.delete("/{upload_id}")
def delete_upload(upload_id: int, db: Session = Depends(get_db)) -> dict:
    u = db.get(Upload, upload_id)
    if not u:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(u)
    db.commit()
    return {"status": "deleted"}
