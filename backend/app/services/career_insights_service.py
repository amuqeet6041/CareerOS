"""Deterministic career insights service (Phase 7).

Analyzes an authenticated user's stored resume/profile against a bounded set of
active jobs and returns: verified profile summary, strengths (verified skills
that appear across relevant jobs), skill gaps (required skills absent from the
verified skill set, ranked by demand), and potential career directions grouped
from available job titles.

Design rules:
- Deterministic analysis is the source of truth. AI (when enabled) may only
  explain, prioritize, and suggest next steps; it never changes match scores or
  invents facts.
- Everything is computed on the fly from existing data: nothing is persisted,
  so no database migration is required.
- Skill normalization reuses util.job_fields.normalize_skill so the insights
  service, matching engine, and job normalization agree.
- Bounded: at most ACTIVE_JOB_FETCH_LIMIT active jobs are fetched through the
  existing job-search service, and at most RELEVANT_JOB_CAP are analyzed
  (no N+1; relations are eager-loaded by job_search).
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.resume import Resume
from app.services.job_search import search_jobs
from app.services.matching_service import match_resume_to_job
from app.utils.job_fields import normalize_skill, normalize_text

logger = logging.getLogger("careeros.career_insights")

# Fetching caps keep the endpoint bounded.
ACTIVE_JOB_FETCH_LIMIT = 30
RELEVANT_JOB_CAP = 20
MAX_CAREER_DIRECTIONS = 6
MAX_DIRECTION_MISSING_SKILLS = 5

# AI payload caps (protect against runaway generated content).
AI_SUMMARY_MAX_CHARS = 800
AI_REASON_MAX_CHARS = 300
AI_SKILL_DEVELOPMENT_MAX = 8
AI_DIRECTIONS_MAX = 6
AI_SUGGESTIONS_MAX = 8

# Gap priority thresholds as fractions of the highest gap frequency.
GAP_PRIORITY_HIGH_RATIO = 0.6
GAP_PRIORITY_MEDIUM_RATIO = 0.33

GAP_PRIORITY_HIGH = "high"
GAP_PRIORITY_MEDIUM = "medium"
GAP_PRIORITY_LOW = "low"

AI_STATUS_AVAILABLE = "available"
AI_STATUS_DISABLED = "disabled"
AI_STATUS_FAILED = "failed"


def dedupe_skills(names: list[str]) -> list[str]:
    """Deduplicate skills case/whitespace-insensitively.

    Keeps the first-seen display spelling while collapsing "Python", "python",
    and " PYTHON " into one entry, matching the deterministic parse pipeline.
    """
    result: list[str] = []
    seen: set[str] = set()
    for name in names or []:
        display = (name or "").strip()
        key = normalize_skill(display)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(display)
    return result


def _profile_summary(resume: Resume) -> dict:
    """Verified profile facts derived only from the stored resume."""
    education = [
        {
            "institution": entry.institution,
            "degree": entry.degree,
            "field_of_study": entry.field_of_study,
        }
        for entry in resume.education
    ]
    certifications = [
        cert.name for cert in resume.certifications if cert.name and cert.name.strip()
    ]
    return {
        "skills": dedupe_skills([s.name for s in resume.skills]),
        "total_experience_years": resume.total_experience_years,
        "education": education,
        "certifications": certifications,
        "experience_entries": len(resume.experience),
    }


def fetch_active_jobs(db: Session, limit: int = ACTIVE_JOB_FETCH_LIMIT) -> list[Job]:
    """Fetch a bounded set of active, non-expired jobs with eager-loaded
    skills/qualifications using the existing job-search service (no N+1)."""
    _, items = search_jobs(
        db,
        include_inactive=False,
        sort="date_newest",
        page=1,
        page_size=limit,
    )
    return items


def _is_job_relevant(result, profile_skill_count: int) -> bool:
    """Deterministic relevance rule.

    A job is relevant when its skill component is resolved (the job requires
    skills, giving a demand signal) and the user shares at least one required
    skill or qualification — unless the user's verified skill set is empty, in
    which case any skill-requiring job is relevant so current skill demand can
    still be surfaced honestly.
    """
    if result.skill_match_percentage is None:
        return False
    if profile_skill_count == 0:
        return True
    if result.skill_match_percentage > 0:
        return True
    return (result.qualification_match_percentage or 0) > 0


def _required_skill_keys(job: Job) -> set[str]:
    return {
        normalize_skill(skill.skill_name)
        for skill in job.skills
        if normalize_skill(skill.skill_name)
    }


def _user_skill_keys(user_skills: list[str]) -> set[str]:
    return {normalize_skill(skill) for skill in user_skills if normalize_skill(skill)}


def _gap_priority(count: int, max_count: int) -> str:
    if max_count <= 0:
        return GAP_PRIORITY_LOW
    if count >= max_count * GAP_PRIORITY_HIGH_RATIO:
        return GAP_PRIORITY_HIGH
    if count >= max_count * GAP_PRIORITY_MEDIUM_RATIO:
        return GAP_PRIORITY_MEDIUM
    return GAP_PRIORITY_LOW


def _build_directions(
    relevant_jobs: list[tuple[Job, object]],
    user_skill_keys: set[str],
    user_display_skills: list[str],
) -> list[dict]:
    """Group relevant jobs by normalized title into potential career paths."""
    display_by_key: dict[str, str] = {}
    groups: dict[str, dict] = {}
    for job, result in relevant_jobs:
        for skill in job.skills:
            key = normalize_skill(skill.skill_name)
            if key and key not in display_by_key:
                display_by_key[key] = skill.skill_name
        key = normalize_text(job.title) or str(job.id)
        if key not in groups:
            groups[key] = {
                "title": job.title,
                "job_count": 0,
                "scores": [],
                "supporting_counts": {},
                "missing_counts": {},
            }
        group = groups[key]
        group["job_count"] += 1
        if result.overall_match_percentage is not None:
            group["scores"].append(result.overall_match_percentage)
        for req_key in _required_skill_keys(job):
            bucket = (
                group["supporting_counts"] if req_key in user_skill_keys else group["missing_counts"]
            )
            bucket[req_key] = bucket.get(req_key, 0) + 1

    directions: list[dict] = []
    for group in groups.values():
        supporting = [
            display
            for display in sorted(
                user_display_skills,
                key=lambda d: (
                    -group["supporting_counts"].get(normalize_skill(d), 0),
                    d.lower(),
                ),
            )
            if group["supporting_counts"].get(normalize_skill(display), 0) > 0
        ]
        missing = [
            display_by_key.get(req_key, req_key)
            for req_key, _count in sorted(
                group["missing_counts"].items(), key=lambda item: (-item[1], item[0])
            )
        ][:MAX_DIRECTION_MISSING_SKILLS]
        average_match = (
            round(sum(group["scores"]) / len(group["scores"]), 2) if group["scores"] else None
        )
        directions.append(
            {
                "title": group["title"],
                "matching_job_count": group["job_count"],
                "average_match": average_match,
                "supporting_skills": supporting,
                "missing_skills": missing,
            }
        )

    directions.sort(
        key=lambda d: (-d["matching_job_count"], -(d["average_match"] or -1), d["title"].lower())
    )
    return directions[:MAX_CAREER_DIRECTIONS]


def _deterministic_payload(
    summary: dict,
    strengths: list[dict],
    skill_gaps: list[dict],
    career_directions: list[dict],
    relevant_job_count: int,
) -> dict:
    """Structured verified data handed to the AI provider.

    Contains only facts derived from the user's resume and the deterministic
    job analysis — no salaries, no fabricated labor-market statistics.
    """
    return {
        "profile_summary": summary,
        "strengths": strengths,
        "skill_gaps": skill_gaps,
        "career_directions": career_directions,
        "relevant_job_count": relevant_job_count,
    }


def _ai_insights_fallback() -> dict:
    return {
        "status": AI_STATUS_FAILED,
        "summary": "",
        "career_directions": [],
        "skill_development": [],
        "resume_suggestions": [],
        "action_plan": [],
    }


def _trim_ai_insights(insights: dict, allowed_skill_keys: set[str]) -> dict:
    """Cap lengths/counts of validated AI output to keep payloads bounded and
    drop any skill the model was not allowed to reference."""
    skill_development = [
        {
            "skill": item.get("skill", ""),
            "reason": (item.get("reason") or "")[:AI_REASON_MAX_CHARS],
            "priority": item.get("priority", "medium"),
        }
        for item in insights.get("skill_development", [])
        if normalize_skill(item.get("skill", "")) in allowed_skill_keys
    ][:AI_SKILL_DEVELOPMENT_MAX]
    return {
        "status": AI_STATUS_AVAILABLE,
        "summary": (insights.get("summary") or "")[:AI_SUMMARY_MAX_CHARS],
        "career_directions": [
            {
                "title": item.get("title", ""),
                "reason": (item.get("reason") or "")[:AI_REASON_MAX_CHARS],
                "next_steps": [str(step) for step in item.get("next_steps", [])][:AI_SUGGESTIONS_MAX],
            }
            for item in insights.get("career_directions", [])
            if (item.get("title") or "").strip()
        ][:AI_DIRECTIONS_MAX],
        "skill_development": skill_development,
        "resume_suggestions": [
            str(s) for s in insights.get("resume_suggestions", [])
        ][:AI_SUGGESTIONS_MAX],
        "action_plan": [str(s) for s in insights.get("action_plan", [])][:AI_SUGGESTIONS_MAX],
    }


def _run_ai_career_insights(deterministic_payload: dict) -> dict:
    """Ask the configured provider for explanatory career insights.

    Returns an ``ai_insights``-shaped dict with status available|disabled|failed.
    Never raises and never blocks the deterministic result: any provider,
    validation, or sanitization failure degrades to ``failed`` with empty
    content (the page keeps showing deterministic data).
    """
    from app.services.ai import provider as ai_provider
    from app.services.ai.base import AIProviderError
    from app.services.ai.career_insights_prompts import build_career_insights_messages
    from app.services.ai.schemas import AICareerInsights
    from pydantic import ValidationError

    try:
        provider = ai_provider.get_ai_provider()
    except AIProviderError as exc:
        logger.warning("Careers AI provider unavailable (category=%s).", exc.category)
        return _ai_insights_fallback()

    if provider is None:
        return {**_ai_insights_fallback(), "status": AI_STATUS_DISABLED}

    try:
        payload = provider.generate_career_insights(
            build_career_insights_messages(deterministic_payload)
        )
        insights = AICareerInsights.model_validate(payload)
    except (AIProviderError, ValidationError, ValueError, TypeError):
        logger.warning("Careers AI output failed validation; using deterministic analysis.")
        return _ai_insights_fallback()
    except Exception:
        logger.error("Careers AI provider raised an unexpected error.", exc_info=True)
        return _ai_insights_fallback()

    allowed = {normalize_skill(d) for d in deterministic_payload["profile_summary"]["skills"]}
    allowed |= {normalize_skill(g["skill"]) for g in deterministic_payload["skill_gaps"]}
    return _trim_ai_insights(insights.model_dump(), allowed)


def _deterministic_action_plan(
    strengths: list[dict], skill_gaps: list[dict], relevant_job_count: int, summary: dict
) -> tuple[list[str], list[str]]:
    """Evidence-based action plan and resume suggestions (AI-free)."""
    action_plan: list[str] = []
    if relevant_job_count == 0:
        action_plan.append("We need relevant job data to identify current skill demand.")
    else:
        for gap in skill_gaps[:3]:
            action_plan.append(
                f"Focus on developing {gap['skill']} — it appears in "
                f"{gap['relevance_count']} relevant jobs."
            )
        if strengths:
            top = strengths[0]
            action_plan.append(
                f"Lean into {top['skill']}, your strongest verified skill, used across "
                f"{top['relevance_count']} relevant jobs."
            )

    resume_suggestions: list[str] = []
    if summary["experience_entries"] == 0:
        resume_suggestions.append(
            "Add your work experience with dates so your experience level can be assessed."
        )
    if not summary["education"]:
        resume_suggestions.append("Add your education details to strengthen qualification matches.")
    if len(summary["skills"]) < 3:
        resume_suggestions.append(
            "Listing more of your verified skills can improve which jobs are considered relevant."
        )
    return action_plan, resume_suggestions


def analyze_career_insights(db: Session, resume: Resume) -> dict:
    """Build the complete career-insights payload for a stored resume."""
    summary = _profile_summary(resume)
    user_skills = summary["skills"]
    user_keys = _user_skill_keys(user_skills)

    jobs = fetch_active_jobs(db)
    matches = [(job, match_resume_to_job(resume, job)) for job in jobs]

    relevant = [
        (job, result)
        for job, result in matches
        if _is_job_relevant(result, len(user_skills))
    ]
    relevant.sort(key=lambda pair: (-(pair[1].overall_match_percentage or -1), pair[0].id))
    relevant = relevant[:RELEVANT_JOB_CAP]

    # Strengths: verified user skills required by relevant jobs.
    strength_counter: dict[str, int] = {}
    for job, _result in relevant:
        required = _required_skill_keys(job)
        for display in user_skills:
            if normalize_skill(display) in required:
                strength = normalize_skill(display)
                strength_counter[strength] = strength_counter.get(strength, 0) + 1
    strengths = [
        {"skill": display, "relevance_count": strength_counter[key]}
        for display in user_skills
        for key in [normalize_skill(display)]
        if key in strength_counter and strength_counter[key] > 0
    ]
    strengths.sort(key=lambda s: (-s["relevance_count"], s["skill"].lower()))

    # Skill gaps: required skills absent from the verified skill set, ranked by
    # how many relevant jobs require them.
    gap_counter: dict[str, int] = {}
    gap_display: dict[str, str] = {}
    for job, _result in relevant:
        for skill in job.skills:
            key = normalize_skill(skill.skill_name)
            if not key or key in user_keys:
                continue
            gap_counter[key] = gap_counter.get(key, 0) + 1
            gap_display.setdefault(key, skill.skill_name)
    max_gap = max(gap_counter.values()) if gap_counter else 0
    skill_gaps = [
        {
            "skill": skill_display,
            "relevance_count": count,
            "priority": _gap_priority(count, max_gap),
        }
        for key, count in sorted(gap_counter.items(), key=lambda item: (-item[1], item[0]))
        for skill_display in [gap_display[key]]
    ]

    directions = _build_directions(relevant, user_keys, user_skills)

    relevant_job_count = len(relevant)
    action_plan, resume_suggestions = _deterministic_action_plan(
        strengths, skill_gaps, relevant_job_count, summary
    )

    ai_insights = _run_ai_career_insights(
        _deterministic_payload(
            summary, strengths, skill_gaps, directions, relevant_job_count
        )
    )

    gap_evidence = (
        f"Required by {{}} of {relevant_job_count} relevant jobs analyzed."
        if relevant_job_count
        else "No relevant jobs analyzed yet."
    )
    for gap in skill_gaps:
        gap["why_it_matters"] = (
            gap_evidence.format(gap["relevance_count"]) if relevant_job_count else gap_evidence
        )
    for direction in directions:
        direction["explanation"] = (
            f"Supported by {direction['matching_job_count']} relevant job(s); "
            f"you already match {len(direction['supporting_skills'])} of the "
            "required skills."
        )

    return {
        "has_resume": True,
        "profile_summary": summary,
        "strengths": strengths,
        "skill_gaps": skill_gaps,
        "career_directions": directions,
        "action_plan": action_plan,
        "resume_suggestions": resume_suggestions,
        "fetched_job_count": len(jobs),
        "relevant_job_count": relevant_job_count,
        "ai_insights": ai_insights,
    }