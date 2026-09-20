from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.resume import ResumeOut
from app.services import resume_parser, resume_service

router = APIRouter()


@router.post("/upload", response_model=ResumeOut, status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Parse an uploaded PDF/DOCX resume and persist it for the current user."""
    contents = await file.read()

    max_bytes = settings.MAX_RESUME_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Resume exceeds the maximum size of {settings.MAX_RESUME_SIZE_MB} MB.",
        )

    try:
        parsed = resume_parser.parse_resume(
            contents,
            file.filename,
            file.content_type,
        )
    except resume_parser.UnsupportedResumeTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except (resume_parser.EmptyResumeError, resume_parser.MalformedResumeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    resume = resume_service.save_resume(db, current_user.id, file.filename or "resume", parsed)
    return resume


@router.get("/analysis", response_model=ResumeOut)
def get_resume_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current user's stored parsed resume information."""
    resume = resume_service.get_resume_for_user(db, current_user.id)
    if resume is None:
        raise HTTPException(status_code=404, detail="No resume uploaded yet.")
    return resume