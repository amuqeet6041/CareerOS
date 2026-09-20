from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=True)  # e.g. name of the job API/provider
    external_id = Column(String, nullable=True, index=True)

    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=True)
    work_mode = Column(String, nullable=True)  # remote | hybrid | onsite
    job_type = Column(String, nullable=True)  # full-time | part-time | internship | contract

    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    currency = Column(String, nullable=True)

    description = Column(String, nullable=True)
    apply_url = Column(String, nullable=True)

    fetched_at = Column(DateTime, default=datetime.utcnow)

    saved_jobs = relationship("SavedJob", back_populates="job")
    applications = relationship("Application", back_populates="job")
