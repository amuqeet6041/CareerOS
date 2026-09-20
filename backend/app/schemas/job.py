from pydantic import BaseModel
from datetime import datetime


class JobSkillOut(BaseModel):
    id: int
    skill_name: str
    normalized_name: str

    class Config:
        from_attributes = True


class JobQualificationOut(BaseModel):
    id: int
    qualification: str
    normalized_qualification: str

    class Config:
        from_attributes = True


class JobResponse(BaseModel):
    """Full public job representation returned to the API client."""

    id: int
    source: str | None = None
    external_id: str | None = None
    title: str
    company: str
    description: str | None = None
    employment_type: str | None = None
    work_mode: str | None = None
    location: str | None = None
    city: str | None = None
    country: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str | None = None
    application_url: str | None = None
    minimum_experience_years: float | None = None
    maximum_experience_years: float | None = None
    posted_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_active: bool | None = None
    skills: list[JobSkillOut] = []
    qualifications: list[JobQualificationOut] = []

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Paginated job listing payload.

    The shape is designed to be stable for the frontend (Phase 4 wires the
    jobs UI to ``items``).
    """

    items: list[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int