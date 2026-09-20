from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobListResponse, JobResponse
from app.schemas.matching import JobMatchResponse
from app.services.job_search import (
    MAX_PAGE_SIZE,
    SORT_OPTIONS,
    search_jobs,
)
from app.services.matching_engine import COMPONENT_WEIGHTS_PERCENT
from app.services.matching_service import match_resume_to_job
from app.services.resume_service import get_resume_for_user
from app.utils.job_fields import (
    EMPLOYMENT_TYPES,
    WORK_MODES,
    is_known_employment_type,
    is_known_work_mode,
)

router = APIRouter()


@router.get("", response_model=JobListResponse)
def list_jobs(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None, description="Free-text search over title, company, description, location, and skills"),
    location: str | None = Query(default=None, description="Substring match against the free-form location text"),
    city: str | None = Query(default=None, description="Substring match against the job city"),
    work_mode: str | None = Query(default=None, description="One of: remote, hybrid, onsite"),
    employment_type: str | None = Query(default=None, description="One of: full-time, part-time, contract, internship, temporary, freelance"),
    salary_min: float | None = Query(default=None, ge=0, description="Include jobs whose max salary is at or above this value"),
    salary_max: float | None = Query(default=None, ge=0, description="Include jobs whose min salary is at or below this value"),
    source: str | None = Query(default=None, description="Provider source id, e.g. 'demo'"),
    include_inactive: bool = Query(default=False, description="Include expired/inactive jobs"),
    sort: str = Query(default="date_newest", description="One of: date_newest, date_oldest, salary_desc"),
    page: int = Query(default=1, ge=1, description="1-based page number"),
    page_size: int = Query(default=20, ge=1, le=MAX_PAGE_SIZE, description="Items per page (max 100)"),
):
    if work_mode is not None and not is_known_work_mode(work_mode):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid work_mode {work_mode!r}; expected one of: {', '.join(sorted(WORK_MODES))}",
        )
    if employment_type is not None and not is_known_employment_type(employment_type):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid employment_type {employment_type!r}; expected one of: {', '.join(sorted(EMPLOYMENT_TYPES))}",
        )
    if sort not in SORT_OPTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort {sort!r}; expected one of: {', '.join(sorted(SORT_OPTIONS))}",
        )

    total, items = search_jobs(
        db,
        search=search,
        location=location,
        city=city,
        work_mode=work_mode,
        employment_type=employment_type,
        salary_min=salary_min,
        salary_max=salary_max,
        source=source,
        include_inactive=include_inactive,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return JobListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = (
        db.query(Job)
        .options(selectinload(Job.skills), selectinload(Job.qualifications))
        .filter(Job.id == job_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/match", response_model=JobMatchResponse)
def get_job_match(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deterministic match of the authenticated user's resume against a job.

    Authentication is required and the match always uses the caller's OWN
    resume (never a client-supplied user id). Returns 404 if the job does not
    exist or if the user has no uploaded resume.
    """
    job = (
        db.query(Job)
        .options(selectinload(Job.skills), selectinload(Job.qualifications))
        .filter(Job.id == job_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resume = get_resume_for_user(db, current_user.id)
    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="No resume uploaded yet. Upload a resume before requesting a match.",
        )

    result = match_resume_to_job(resume, job)
    return JobMatchResponse(
        job_id=job.id,
        skill_match_percentage=result.skill_match_percentage,
        qualification_match_percentage=result.qualification_match_percentage,
        experience_match_percentage=result.experience_match_percentage,
        overall_match_percentage=result.overall_match_percentage,
        matched_skills=result.matched_skills,
        missing_skills=result.missing_skills,
        matched_qualifications=result.matched_qualifications,
        missing_qualifications=result.missing_qualifications,
        experience_status=result.experience_status,
        candidate_experience_years=result.candidate_experience_years,
        minimum_required_years=result.minimum_required_years,
        maximum_required_years=result.maximum_required_years,
        component_weights=COMPONENT_WEIGHTS_PERCENT,
        summary=result.summary,
    )


@router.post("/{job_id}/save")
def save_job(job_id: int, current_user: User = Depends(get_current_user)):
    # Placeholder: persists to SavedJob once the saved-jobs flow is wired up
    # for real (Phase 5). Endpoint exists now so the auth requirement is
    # exercised and documented.
    return {"message": f"Job {job_id} saved for user {current_user.id} (placeholder)"}