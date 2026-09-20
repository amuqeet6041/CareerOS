"""
Matching service.

Orchestrates matching between a user's stored resume and a job listing:

- Legacy placeholder functions (``calculate_skill_match``,
  ``calculate_qualification_match``) are preserved for backward compatibility
  with the old ``POST /api/matching`` endpoint and its tests. They return a
  simple percentage (``0.0`` when there are no requirements) and do NOT
  represent the unknown/no-requirement policy.
- The production matching engine lives in :mod:`app.services.matching_engine`
  and is used by ``GET /api/jobs/{job_id}/match``. It distinguishes real 0%
  from "not enough information" (``None``).
"""

from app.models.job import Job
from app.models.resume import Resume
from app.services.matching_engine import (
    CandidateProfile,
    JobMatchResult,
    build_summary,
    calculate_overall_match,
    experience_match,
    match_candidate_to_job,
    qualification_match,
    skill_match,
)

__all__ = [
    "calculate_skill_match",
    "calculate_qualification_match",
    "calculate_overall_match",
    "build_summary",
    "experience_match",
    "qualification_match",
    "skill_match",
    "CandidateProfile",
    "JobMatchResult",
    "build_candidate_profile",
    "match_resume_to_job",
]


def calculate_skill_match(user_skills: list[str], job_required_skills: list[str]) -> float:
    """Legacy placeholder: percentage (0-100) of required skills the user has.

    Returns ``0.0`` when the job has no skill requirements. Kept unchanged for
    backward compatibility; use :func:`skill_match` for the production engine.
    """
    if not job_required_skills:
        return 0.0

    user_set = {s.strip().lower() for s in user_skills}
    required_set = {s.strip().lower() for s in job_required_skills}

    matched = user_set.intersection(required_set)
    return round((len(matched) / len(required_set)) * 100, 2)


def calculate_qualification_match(
    user_education: list[str], job_required_education: list[str]
) -> float:
    """Legacy placeholder: percentage (0-100) of required qualifications the
    user has. Returns ``0.0`` when there are no requirements."""
    if not job_required_education:
        return 0.0

    user_set = {e.strip().lower() for e in user_education}
    required_set = {e.strip().lower() for e in job_required_education}

    matched = user_set.intersection(required_set)
    return round((len(matched) / len(required_set)) * 100, 2)


def build_candidate_profile(resume: Resume) -> CandidateProfile:
    """Derive a normalized candidate profile from a stored resume.

    Qualification tokens come only from stored data: each education entry
    contributes its ``degree``, its ``field_of_study``, and (when both exist) a
    combined ``"{degree} in {field_of_study}"`` token; each certification
    contributes its name. No qualifications are invented.
    """
    qualifications: list[str] = []
    for entry in resume.education:
        if entry.degree:
            qualifications.append(entry.degree)
        if entry.field_of_study:
            qualifications.append(entry.field_of_study)
        if entry.degree and entry.field_of_study:
            qualifications.append(f"{entry.degree} in {entry.field_of_study}")

    for cert in resume.certifications:
        if cert.name:
            qualifications.append(cert.name)

    # The current resume schema stores company/title/description but no
    # employment dates, so candidate experience years cannot be derived
    # deterministically. It is intentionally left unknown rather than assumed 0.
    experience_years: float | None = None

    return CandidateProfile(
        skills=[s.name for s in resume.skills if s.name],
        qualifications=qualifications,
        experience_years=experience_years,
    )


def match_resume_to_job(resume: Resume, job: Job) -> JobMatchResult:
    """Match a user's resume against a job listing (skills + qualifications +
    experience expected to be loaded on ``job``)."""
    profile = build_candidate_profile(resume)
    return match_candidate_to_job(
        profile,
        job_required_skills=[skill.skill_name for skill in job.skills],
        job_required_qualifications=[qual.qualification for qual in job.qualifications],
        minimum_experience_years=job.minimum_experience_years,
        maximum_experience_years=job.maximum_experience_years,
    )