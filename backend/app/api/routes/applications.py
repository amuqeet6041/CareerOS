from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.job import Job
from app.models.user import User
from app.services.application_service import (
    create_application,
    get_application_for_job,
    list_applications,
    update_application_status,
)
from app.schemas.application import ApplicationCreate, ApplicationOut, ApplicationStatusUpdate
from app.utils.validators import is_valid_application_status

router = APIRouter()


@router.get("", response_model=list[ApplicationOut])
def list_my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_applications(db, current_user.id)


@router.post("", response_model=ApplicationOut, status_code=201)
def apply_to_job(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if get_application_for_job(db, current_user.id, payload.job_id):
        raise HTTPException(status_code=409, detail="Application already exists for this job")

    return create_application(db, current_user.id, payload.job_id)


@router.patch("/{application_id}", response_model=ApplicationOut)
def update_application(
    application_id: int,
    payload: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not is_valid_application_status(payload.status):
        raise HTTPException(status_code=422, detail="Invalid application status")

    application = update_application_status(db, application_id, current_user.id, payload.status)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application