from pydantic import BaseModel
from datetime import datetime


class SkillOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class EducationOut(BaseModel):
    id: int
    institution: str
    degree: str | None = None
    field_of_study: str | None = None

    class Config:
        from_attributes = True


class ExperienceOut(BaseModel):
    id: int
    company: str
    title: str | None = None
    description: str | None = None

    class Config:
        from_attributes = True


class CertificationOut(BaseModel):
    id: int
    name: str
    issuer: str | None = None

    class Config:
        from_attributes = True


class ResumeOut(BaseModel):
    id: int
    file_name: str
    uploaded_at: datetime
    skills: list[SkillOut] = []
    education: list[EducationOut] = []
    experience: list[ExperienceOut] = []
    certifications: list[CertificationOut] = []

    class Config:
        from_attributes = True
