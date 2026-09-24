"""Profile & Preferences API routes (Phase 9).

Endpoints:
  GET  /api/profile                  — current user's profile
  PATCH /api/profile                 — update current user's profile
  GET  /api/profile/preferences      — current user's career preferences
  PATCH /api/profile/preferences     — update current user's career preferences

Security: all endpoints use get_current_user() — user_id is NEVER taken from
the request body or query parameters.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.profile import ProfileOut, ProfileUpdate, PreferencesOut, PreferencesUpdate
from app.services import profile_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Profile endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=ProfileOut, summary="Get current user's profile")
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the authenticated user's profile.

    If the user has not yet saved a profile, the editable fields will be null
    but user identity fields (user_id, name, email) are always present.
    """
    profile = profile_service.get_profile(db, current_user.id)
    return profile_service.profile_to_dict(profile, current_user)


@router.patch("", response_model=ProfileOut, summary="Update current user's profile")
def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Partially updates the authenticated user's profile.

    Only fields included in the request body are updated; omitted fields are
    left unchanged. The profile_source is always set to "manual" on update.
    """
    profile = profile_service.upsert_profile(db, current_user.id, payload)
    return profile_service.profile_to_dict(profile, current_user)


# ---------------------------------------------------------------------------
# Preferences endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/preferences",
    response_model=PreferencesOut,
    summary="Get current user's career preferences",
)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the authenticated user's career preferences.

    If preferences have not been saved yet, all list fields return [] and
    scalar fields return null/default values.
    """
    prefs = profile_service.get_preferences(db, current_user.id)
    if prefs is None:
        # Return an empty preferences object rather than 404
        return PreferencesOut(user_id=current_user.id)
    return profile_service.preference_to_dict(prefs)


@router.patch(
    "/preferences",
    response_model=PreferencesOut,
    summary="Update current user's career preferences",
)
def update_preferences(
    payload: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Partially updates the authenticated user's career preferences.

    Only fields included in the request body are updated.
    """
    prefs = profile_service.upsert_preferences(db, current_user.id, payload)
    return profile_service.preference_to_dict(prefs)
