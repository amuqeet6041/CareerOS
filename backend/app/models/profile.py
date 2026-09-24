"""UserProfile model — stores editable profile fields for each user.

Separate from the User model to keep auth data (email/password) isolated
from career-presentation data, and to distinguish AI-extracted data from
user-confirmed edits (profile_source field).

Relationship is 1:1 with users (enforced by UNIQUE on user_id).
"""

from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Editable presentation fields
    headline = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    country = Column(String, nullable=True)

    # Provenance: "manual" = user explicitly set this;
    # "resume_extracted" = populated from CV parse (can be overwritten by user)
    profile_source = Column(String, nullable=True, default="manual")

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
