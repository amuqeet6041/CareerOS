"""Response schemas for ``GET /api/career-insights`` (Phase 7)."""

from pydantic import BaseModel, Field


class ProfileEducationEntry(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None


class ProfileSummaryOut(BaseModel):
    skills: list[str] = Field(default_factory=list)
    total_experience_years: float | None = None
    education: list[ProfileEducationEntry] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    experience_entries: int = 0


class StrengthOut(BaseModel):
    skill: str
    relevance_count: int


class SkillGapOut(BaseModel):
    skill: str
    relevance_count: int
    priority: str = "low"  # high | medium | low
    why_it_matters: str = ""


class CareerDirectionOut(BaseModel):
    title: str
    matching_job_count: int
    average_match: float | None = None
    supporting_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    explanation: str = ""


class AICareerDirectionOut(BaseModel):
    title: str
    reason: str = ""
    next_steps: list[str] = Field(default_factory=list)


class AISkillDevelopmentOut(BaseModel):
    skill: str
    reason: str = ""
    priority: str = "medium"  # high | medium | low


class AIInsightsOut(BaseModel):
    status: str = "disabled"  # available | disabled | failed
    summary: str = ""
    career_directions: list[AICareerDirectionOut] = Field(default_factory=list)
    skill_development: list[AISkillDevelopmentOut] = Field(default_factory=list)
    resume_suggestions: list[str] = Field(default_factory=list)
    action_plan: list[str] = Field(default_factory=list)


class CareerInsightsResponse(BaseModel):
    """Deterministic analysis always present; AI insights are optional and
    clearly statused so the frontend can separate "career insights
    unavailable" from "AI insights unavailable"."""

    has_resume: bool = True
    profile_summary: ProfileSummaryOut
    strengths: list[StrengthOut] = Field(default_factory=list)
    skill_gaps: list[SkillGapOut] = Field(default_factory=list)
    career_directions: list[CareerDirectionOut] = Field(default_factory=list)
    action_plan: list[str] = Field(default_factory=list)
    resume_suggestions: list[str] = Field(default_factory=list)
    fetched_job_count: int = 0
    relevant_job_count: int = 0
    ai_insights: AIInsightsOut