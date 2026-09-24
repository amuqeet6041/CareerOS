"""Profile & Preferences service layer (Phase 9).

Handles all database interactions for user profiles and career preferences.
JSON list fields (preferred_roles, preferred_skills, etc.) are stored as JSON
strings in SQLite/PostgreSQL TEXT columns and converted to/from list[str] here.

Security note: every public function accepts user_id directly — callers MUST
source user_id from get_current_user(), never from client-supplied input.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.profile import UserProfile
from app.models.application import UserPreference
from app.schemas.profile import ProfileUpdate, PreferencesUpdate


# ---------------------------------------------------------------------------
# JSON helpers for list fields stored as TEXT
# ---------------------------------------------------------------------------

def _encode_list(value: Optional[list[str]]) -> Optional[str]:
    """Serialize a list to a JSON string for storage, or None if None."""
    if value is None:
        return None
    return json.dumps(value)


def _decode_list(value: Optional[str]) -> list[str]:
    """Deserialize a JSON string back to a list, returning [] on failure."""
    if not value:
        return []
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


# ---------------------------------------------------------------------------
# Profile functions
# ---------------------------------------------------------------------------

def get_profile(db: Session, user_id: int) -> Optional[UserProfile]:
    """Return the UserProfile row for this user, or None if not yet created."""
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()


def upsert_profile(db: Session, user_id: int, data: ProfileUpdate) -> UserProfile:
    """Create or update the UserProfile for this user.

    Only the fields explicitly provided in `data` are written — omitted
    (None) fields are left unchanged on an existing row.

    The profile_source is always set to "manual" when a user explicitly
    edits their profile, so future AI processes know not to overwrite it.
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if profile is None:
        # First save — create the row
        profile = UserProfile(user_id=user_id, profile_source="manual")
        db.add(profile)

    # Partial update: only overwrite non-None fields
    if data.headline is not None:
        profile.headline = data.headline
    if data.bio is not None:
        profile.bio = data.bio
    if data.location is not None:
        profile.location = data.location
    if data.country is not None:
        profile.country = data.country

    profile.profile_source = "manual"
    profile.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(profile)
    return profile


# ---------------------------------------------------------------------------
# Preferences functions
# ---------------------------------------------------------------------------

def get_preferences(db: Session, user_id: int) -> Optional[UserPreference]:
    """Return the UserPreference row for this user, or None if not created."""
    return db.query(UserPreference).filter(UserPreference.user_id == user_id).first()


def upsert_preferences(db: Session, user_id: int, data: PreferencesUpdate) -> UserPreference:
    """Create or update career preferences for this user.

    List fields are JSON-encoded before storage.
    Salary min/max are stored as strings.
    Boolean open_to_relocate is stored as "true"/"false" string for SQLite compat.
    """
    prefs = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()

    if prefs is None:
        prefs = UserPreference(user_id=user_id)
        db.add(prefs)

    # List fields (JSON-encoded)
    if data.preferred_roles is not None:
        prefs.preferred_roles = _encode_list(data.preferred_roles)
    if data.preferred_skills is not None:
        prefs.preferred_skills = _encode_list(data.preferred_skills)
    if data.preferred_work_modes is not None:
        prefs.preferred_work_modes = _encode_list(data.preferred_work_modes)
    if data.preferred_employment_types is not None:
        prefs.preferred_employment_types = _encode_list(data.preferred_employment_types)
    if data.preferred_industries is not None:
        prefs.preferred_industries = _encode_list(data.preferred_industries)

    # Salary (store as string)
    if data.salary_min is not None:
        prefs.salary_min = str(data.salary_min)
    if data.salary_max is not None:
        prefs.salary_max = str(data.salary_max)
    if data.currency is not None:
        prefs.currency = data.currency

    # Career level
    if data.career_level is not None:
        prefs.career_level = data.career_level

    # Relocation (store as string "true"/"false")
    if data.open_to_relocate is not None:
        prefs.open_to_relocate = "true" if data.open_to_relocate else "false"

    # Legacy preferred_location
    if data.preferred_location is not None:
        prefs.preferred_location = data.preferred_location

    db.commit()
    db.refresh(prefs)
    return prefs


# ---------------------------------------------------------------------------
# Helper: build PreferencesOut-compatible dict from a UserPreference ORM row
# ---------------------------------------------------------------------------

def preference_to_dict(prefs: UserPreference) -> dict:
    """Convert a UserPreference ORM object to a dict ready for PreferencesOut.

    The API route uses this to build the response because PreferencesOut
    exposes list[str] for JSON-encoded fields, which SQLAlchemy can't do
    automatically with from_attributes.
    """
    open_to_relocate = None
    if prefs.open_to_relocate == "true":
        open_to_relocate = True
    elif prefs.open_to_relocate == "false":
        open_to_relocate = False

    salary_min = float(prefs.salary_min) if prefs.salary_min else None
    salary_max = float(prefs.salary_max) if prefs.salary_max else None

    return {
        "user_id": prefs.user_id,
        "preferred_roles": _decode_list(prefs.preferred_roles),
        "preferred_skills": _decode_list(prefs.preferred_skills),
        "preferred_work_modes": _decode_list(prefs.preferred_work_modes),
        "preferred_employment_types": _decode_list(prefs.preferred_employment_types),
        "preferred_industries": _decode_list(prefs.preferred_industries),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "currency": prefs.currency or "USD",
        "career_level": prefs.career_level,
        "open_to_relocate": open_to_relocate,
        "preferred_location": prefs.preferred_location,
    }


def profile_to_dict(profile: Optional[UserProfile], user) -> dict:
    """Build a ProfileOut-compatible dict from a UserProfile row + user object."""
    updated_at = None
    if profile and profile.updated_at:
        updated_at = profile.updated_at.isoformat()

    return {
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "headline": profile.headline if profile else None,
        "bio": profile.bio if profile else None,
        "location": profile.location if profile else None,
        "country": profile.country if profile else None,
        "profile_source": profile.profile_source if profile else None,
        "updated_at": updated_at,
    }
