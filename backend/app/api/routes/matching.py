from fastapi import APIRouter
from pydantic import BaseModel

from app.services.matching_service import calculate_skill_match, calculate_qualification_match

router = APIRouter()


class MatchRequest(BaseModel):
    user_skills: list[str] = []
    job_required_skills: list[str] = []
    user_education: list[str] = []
    job_required_education: list[str] = []


class MatchResponse(BaseModel):
    skill_match_percentage: float
    qualification_match_percentage: float


@router.post("", response_model=MatchResponse)
def calculate_match(payload: MatchRequest):
    skill_match = calculate_skill_match(payload.user_skills, payload.job_required_skills)
    qualification_match = calculate_qualification_match(
        payload.user_education, payload.job_required_education
    )
    return MatchResponse(
        skill_match_percentage=skill_match,
        qualification_match_percentage=qualification_match,
    )
