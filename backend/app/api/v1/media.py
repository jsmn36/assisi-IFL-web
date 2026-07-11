"""
Media Upload API Endpoints
"""
import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from app.api.dependencies import get_current_user
from app.models import User

router = APIRouter(prefix="/media", tags=["Media"])

UPLOAD_DIR = "static/uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mov", ".avi", ".pdf", ".doc", ".docx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Securely upload file assets (Images, Videos, PDFs) for posts or logos (Auth required)"""
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Validate file extension
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Supported: {list(ALLOWED_EXTENSIONS)}"
        )

    # Validate file size (check headers or read chunks)
    # Since UploadFile in FastAPI stores in spool/temp files, we read the size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum size of 50MB."
        )

    # Generate unique filename to prevent collisions
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Save file to static storage
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    relative_url = f"/static/uploads/{unique_filename}"
    return {
        "url": relative_url,
        "filename": file.filename,
        "size": file_size,
        "content_type": file.content_type
    }
