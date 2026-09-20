from pydantic import BaseModel


class JobOut(BaseModel):
    id: int
    title: str
    company: str
    location: str | None = None
    work_mode: str | None = None
    job_type: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str | None = None
    description: str | None = None
    apply_url: str | None = None

    class Config:
        from_attributes = True


class JobMatchOut(JobOut):
    skill_match_percentage: float = 0.0
    qualification_match_percentage: float = 0.0
