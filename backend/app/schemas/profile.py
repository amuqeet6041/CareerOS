"""Pydantic schemas for the Profile & Preferences API (Phase 9).

JSON array fields (preferred_roles, etc.) are stored as JSON strings in the
database but exposed as list[str] here. The service layer handles the
serialisation round-trip via json.loads / json.dumps.

Uses model_config = ConfigDict(from_attributes=True) instead of the deprecated
class-based Config to avoid Pydantic v2 DeprecationWarnings.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Profile schemas
# ---------------------------------------------------------------------------

class ProfileOut(BaseModel):
    """Response schema for GET /api/profile.

    Combines UserProfile fields with the immutable user identity fields (id,
    name, email) so the frontend only needs one call to render the profile page.
    """

    model_config = ConfigDict(from_attributes=True)

    # User identity (read-only — never editable via this endpoint)
    user_id: int
    name: str
    email: str

    # Editable profile fields
    headline: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    profile_source: Optional[str] = "manual"
    updated_at: Optional[str] = None  # ISO datetime string


class ProfileUpdate(BaseModel):
    """Request body for PATCH /api/profile.

    All fields are optional — only provided fields are updated (partial update).
    """

    headline: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None


# ---------------------------------------------------------------------------
# Preferences schemas
# ---------------------------------------------------------------------------

class PreferencesOut(BaseModel):
    """Response schema for GET /api/profile/preferences."""

    model_config = ConfigDict(from_attributes=True)

    user_id: int

    # List fields (deserialized from JSON strings in DB)
    preferred_roles: list[str] = []
    preferred_skills: list[str] = []
    preferred_work_modes: list[str] = []
    preferred_employment_types: list[str] = []
    preferred_industries: list[str] = []

    # Salary
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = "USD"

    # Level & relocation
    career_level: Optional[str] = None
    open_to_relocate: Optional[bool] = None

    # Legacy fields (exposed for completeness)
    preferred_location: Optional[str] = None


class PreferencesUpdate(BaseModel):
    """Request body for PATCH /api/profile/preferences.

    All fields are optional — only provided fields are updated.
    """

    preferred_roles: Optional[list[str]] = None
    preferred_skills: Optional[list[str]] = None
    preferred_work_modes: Optional[list[str]] = None
    preferred_employment_types: Optional[list[str]] = None
    preferred_industries: Optional[list[str]] = None

    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = None

    career_level: Optional[str] = None
    open_to_relocate: Optional[bool] = None

    # Allow updating the legacy preferred_location as well
    preferred_location: Optional[str] = None
