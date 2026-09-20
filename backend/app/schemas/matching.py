from pydantic import BaseModel, Field


class JobMatchResponse(BaseModel):
    """Complete deterministic match result for one job against the
    authenticated user's resume (``GET /api/jobs/{job_id}/match``).

    Component percentages are ``null`` (unknown) when a job does not require
    that component, or when the resume does not contain enough information to
    evaluate it -- never a fabricated score. The nominal component weights are
    included so clients can see how ``overall_match_percentage`` was produced.
    """

    job_id: int
    skill_match_percentage: float | None = None
    qualification_match_percentage: float | None = None
    experience_match_percentage: float | None = None
    overall_match_percentage: float | None = None
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    matched_qualifications: list[str] = Field(default_factory=list)
    missing_qualifications: list[str] = Field(default_factory=list)
    experience_status: str | None = None
    candidate_experience_years: float | None = None
    minimum_required_years: float | None = None
    maximum_required_years: float | None = None
    component_weights: dict[str, float]
    summary: str