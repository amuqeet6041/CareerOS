from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String, nullable=False)
    raw_text = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Set by the AI resume pipeline when employment dates are available so the
    # matching engine can score experience. Null (not zero) when experience
    # cannot be derived reliably. Values are months / 12, rounded to 2 decimals.
    total_experience_years = Column(Float, nullable=True)

    # "parsed" (deterministic) | "ai_analyzed" | "ai_failed".
    analysis_status = Column(String, nullable=False, default="parsed", server_default="parsed")

    user = relationship("User", back_populates="resumes")
    skills = relationship("Skill", back_populates="resume")
    education = relationship("Education", back_populates="resume")
    experience = relationship("Experience", back_populates="resume")
    certifications = relationship("Certification", back_populates="resume")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    name = Column(String, nullable=False)

    resume = relationship("Resume", back_populates="skills")


class Education(Base):
    __tablename__ = "education"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    institution = Column(String, nullable=True)
    degree = Column(String, nullable=True)
    field_of_study = Column(String, nullable=True)
    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)

    resume = relationship("Resume", back_populates="education")


class Experience(Base):
    __tablename__ = "experience"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    company = Column(String, nullable=False)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    location = Column(String, nullable=True)
    # Format "YYYY-MM". Null means unknown; the duration policy treats missing
    # dates as insufficient information rather than guessing.
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    currently_employed = Column(Boolean, nullable=False, default=False, server_default="0")

    resume = relationship("Resume", back_populates="experience")


class Certification(Base):
    __tablename__ = "certifications"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    name = Column(String, nullable=False)
    issuer = Column(String, nullable=True)
    issue_year = Column(Integer, nullable=True)
    expiry_year = Column(Integer, nullable=True)

    resume = relationship("Resume", back_populates="certifications")
