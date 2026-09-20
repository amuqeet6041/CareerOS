"""Career insights API (Phase 7).

``GET /api/career-insights`` analyzes the authenticated user's OWN stored
resume against a bounded set of active jobs. It never accepts a user id from
the client, so no user can read another user's profile.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.career_insights import CareerInsightsResponse
from app.services.career_insights_service import analyze_career_insights
from app.services.resume_service import get_resume_for_user

router = APIRouter()


@router.get("", response_model=CareerInsightsResponse)
def get_career_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deterministic career analysis plus optional AI explanations."""
    resume = get_resume_for_user(db, current_user.id)
    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="No resume uploaded yet. Upload a resume to unlock Career Insights.",
        )
    return analyze_career_insights(db, resume)