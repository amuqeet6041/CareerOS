"""
Application tracking service.

Business logic for creating, listing, and updating job applications, scoped
to an authenticated user.
"""

from sqlalchemy.orm import Session, selectinload

from app.models.application import Application
from app.models.job import Job


def create_application(db: Session, user_id: int, job_id: int) -> Application:
    application = Application(user_id=user_id, job_id=job_id, status="applied")
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def list_applications(db: Session, user_id: int) -> list[Application]:
    return (
        db.query(Application)
        .options(
            selectinload(Application.job).selectinload(Job.skills),
            selectinload(Application.job).selectinload(Job.qualifications),
        )
        .filter(Application.user_id == user_id)
        .order_by(Application.applied_at.desc(), Application.id.desc())
        .all()
    )


def get_application(db: Session, application_id: int, user_id: int) -> Application | None:
    return (
        db.query(Application)
        .filter(Application.id == application_id, Application.user_id == user_id)
        .first()
    )


def get_application_for_job(db: Session, user_id: int, job_id: int) -> Application | None:
    return (
        db.query(Application)
        .filter(Application.user_id == user_id, Application.job_id == job_id)
        .first()
    )


def update_application_status(
    db: Session, application_id: int, user_id: int, status: str
) -> Application | None:
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == user_id,
    ).first()
    if not application:
        return None
    application.status = status
    db.commit()
    db.refresh(application)
    return application