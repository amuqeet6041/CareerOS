from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("Resume", back_populates="user")
    saved_jobs = relationship("SavedJob", back_populates="user")
    applications = relationship("Application", back_populates="user")
    # Phase 9: 1:1 relationships (uselist=False — each user has at most one row)
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
