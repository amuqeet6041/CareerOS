from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user
from app.models.user import User
from app.services.job_service import search_jobs
from app.schemas.job import JobOut

router = APIRouter()


@router.get("", response_model=list[JobOut])
def list_jobs(
    location: str | None = Query(default=None),
    work_mode: str | None = Query(default=None),
    job_type: str | None = Query(default=None),
):
    query = {"location": location, "work_mode": work_mode, "job_type": job_type}
    jobs = search_jobs(query)
    return jobs


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int):
    # Placeholder: replace with a real database lookup.
    raise HTTPException(status_code=404, detail="Job not found")


@router.post("/{job_id}/save")
def save_job(job_id: int, current_user: User = Depends(get_current_user)):
    # Placeholder: persist to SavedJob model once job fetching is wired up.
    return {"message": f"Job {job_id} saved for user {current_user.id} (placeholder)"}
