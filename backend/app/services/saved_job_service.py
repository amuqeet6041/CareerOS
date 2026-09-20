"""
Saved-job service.

Business logic for saving, unsaving, and listing saved jobs, scoped to an
authenticated user. Uses the existing SavedJob persistence model.
"""

from sqlalchemy.orm import Session, selectinload

from app.models.application import SavedJob
from app.models.job import Job


def create_saved_job(db: Session, user_id: int, job_id: int) -> SavedJob:
    saved_job = SavedJob(user_id=user_id, job_id=job_id)
    db.add(saved_job)
    db.commit()
    db.refresh(saved_job)
    return saved_job


def get_saved_job(db: Session, user_id: int, job_id: int) -> SavedJob | None:
    return (
        db.query(SavedJob)
        .filter(SavedJob.user_id == user_id, SavedJob.job_id == job_id)
        .first()
    )


def delete_saved_job(db: Session, user_id: int, job_id: int) -> bool:
    """Delete one user's saved-job row. Idempotent: missing rows return False."""
    saved_job = get_saved_job(db, user_id, job_id)
    if saved_job is None:
        return False
    db.delete(saved_job)
    db.commit()
    return True


def list_saved_jobs(db: Session, user_id: int) -> list[SavedJob]:
    """List the user's saved jobs newest-first with job data embedded."""
    return (
        db.query(SavedJob)
        .options(
            selectinload(SavedJob.job).selectinload(Job.skills),
            selectinload(SavedJob.job).selectinload(Job.qualifications),
        )
        .filter(SavedJob.user_id == user_id)
        .order_by(SavedJob.saved_at.desc(), SavedJob.id.desc())
        .all()
    )