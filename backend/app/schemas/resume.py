from pydantic import BaseModel
from datetime import datetime


class SkillOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class EducationOut(BaseModel):
    id: int
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None

    class Config:
        from_attributes = True


class ExperienceOut(BaseModel):
    id: int
    company: str
    title: str | None = None
    description: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    currently_employed: bool = False

    class Config:
        from_attributes = True


class CertificationOut(BaseModel):
    id: int
    name: str
    issuer: str | None = None
    issue_year: int | None = None
    expiry_year: int | None = None

    class Config:
        from_attributes = True


class ResumeOut(BaseModel):
    id: int
    file_name: str
    uploaded_at: datetime
    analysis_status: str = "parsed"
    total_experience_years: float | None = None
    skills: list[SkillOut] = []
    education: list[EducationOut] = []
    experience: list[ExperienceOut] = []
    certifications: list[CertificationOut] = []

    class Config:
        from_attributes = True
