from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class SavedJob(Base):
    __tablename__ = "saved_jobs"
    __table_args__ = (
        # A job can only be saved once per user.
        UniqueConstraint("user_id", "job_id", name="uq_saved_jobs_user_job"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    saved_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved_jobs")
    job = relationship("Job", back_populates="saved_jobs")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        # Prevent duplicate applications for the same job.
        UniqueConstraint("user_id", "job_id", name="uq_applications_user_job"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    status = Column(String, default="applied")  # applied | in_review | interview | offer | rejected
    applied_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # --- Legacy columns (kept for backward compat) ---
    preferred_location = Column(String, nullable=True)
    preferred_work_mode = Column(String, nullable=True)
    preferred_job_type = Column(String, nullable=True)

    # --- Phase 9: JSON-encoded list[str] fields ---
    # e.g. preferred_roles = '["Data Analyst", "BI Analyst"]'
    preferred_roles = Column(String, nullable=True)
    preferred_skills = Column(String, nullable=True)
    preferred_work_modes = Column(String, nullable=True)
    preferred_employment_types = Column(String, nullable=True)
    preferred_industries = Column(String, nullable=True)

    # Salary range (stored as strings to avoid float edge cases)
    salary_min = Column(String, nullable=True)
    salary_max = Column(String, nullable=True)
    currency = Column(String, nullable=True, default="USD")

    # Career level: entry | junior | mid | senior | lead
    career_level = Column(String, nullable=True)

    # Relocation willingness stored as "true"/"false"/NULL for SQLite compat
    open_to_relocate = Column(String, nullable=True)

    user = relationship("User", back_populates="preferences")
