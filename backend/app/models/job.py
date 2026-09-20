from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Job(Base):
    """A job listing aggregated from an external source.

    The ``(source, external_id)`` pair is unique so re-ingesting a job from the
    same provider updates the existing row instead of creating a duplicate.
    """

    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_jobs_source_external_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=True)  # e.g. name of the job API/provider
    external_id = Column(String, nullable=True, index=True)

    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    description = Column(String, nullable=True)

    employment_type = Column(String, nullable=True)  # full-time | part-time | ...
    work_mode = Column(String, nullable=True)  # remote | hybrid | onsite
    location = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)

    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    currency = Column(String, nullable=True)

    application_url = Column(String, nullable=True)

    minimum_experience_years = Column(Float, nullable=True)
    maximum_experience_years = Column(Float, nullable=True)

    posted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    is_active = Column(Boolean, nullable=True, default=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    skills = relationship(
        "JobSkill",
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    qualifications = relationship(
        "JobQualification",
        back_populates="job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    saved_jobs = relationship("SavedJob", back_populates="job")
    applications = relationship("Application", back_populates="job")


class JobSkill(Base):
    """A skill required by a job. Names are stored as provided plus a
    case-normalized copy so duplicates can be prevented regardless of source
    casing (e.g. "Python" vs "python")."""

    __tablename__ = "job_skills"
    __table_args__ = (
        UniqueConstraint(
            "job_id", "normalized_name", name="uq_job_skills_job_skill"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_name = Column(String, nullable=False)
    normalized_name = Column(String, nullable=False, index=True)

    job = relationship("Job", back_populates="skills")


class JobQualification(Base):
    """A qualification (degree, certificate, license) required by a job."""

    __tablename__ = "job_qualifications"
    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "normalized_qualification",
            name="uq_job_qualifications_job_qualification",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(
        Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    qualification = Column(String, nullable=False)
    normalized_qualification = Column(String, nullable=False, index=True)

    job = relationship("Job", back_populates="qualifications")