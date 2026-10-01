"""
AI resume-intelligence pipeline.

``run_resume_analysis(raw_text)`` is the single entry point used by the upload
and re-analysis flows. It returns ``(structured | None, status)`` where:

- ``structured`` is the validated, deduplicated, ready-to-persist dict (skills,
  education, certifications, experience, total_experience_years), or ``None``
  when no AI result is available.
- ``status`` is one of ``"ai_analyzed"``, ``"parsed"`` (AI disabled), or
  ``"ai_failed"`` (fallback to deterministic parsing).

The pipeline never raises for provider/validation issues: every failure falls
back to the deterministic parse so uploads never break because of AI.
"""

from __future__ import annotations

import logging
import re

from pydantic import ValidationError

from app.core.config import settings
from app.services.ai import provider as ai_provider
from app.services.ai.base import AIProviderError
from app.services.ai.prompts import truncate_resume_text
from app.services.ai.schemas import AIResumeExtraction
from app.services.experience_duration import calculate_total_experience_years
from app.utils.job_fields import normalize_skill

logger = logging.getLogger("careeros.ai")


def structured_to_persist(
    extraction: AIResumeExtraction,
    deterministic_experience: list[dict] | None = None,
) -> dict:
    """Turn validated AI output into the persistence shape.

    Deduplicates skills by the same normalized key used by the matching engine,
    keeps AI spelling for display, and computes the deterministic total
    experience rather than asking the model for a number.

    ``deterministic_experience`` is the already-parsed experience list from the
    same document. It is used only to supply dates the AI did not return, under
    the conservative rules in :func:`_merge_deterministic_dates`.
    """
    skills: list[str] = []
    seen: set[str] = set()
    for skill in extraction.skills:
        display = (skill or "").strip()
        if not display:
            continue
        key = normalize_skill(display)
        if not key or key in seen:
            continue
        seen.add(key)
        skills.append(display)

    education = [
        {
            "institution": entry.institution,
            "degree": entry.degree,
            "field_of_study": entry.field_of_study,
            "start_year": entry.start_year,
            "end_year": entry.end_year,
        }
        for entry in extraction.education
    ]

    certifications = [
        {
            "name": cert.name,
            "issuer": cert.issuer,
            "issue_year": cert.issue_year,
            "expiry_year": cert.expiry_year,
        }
        for cert in extraction.certifications
    ]

    experience = []
    for entry in extraction.experience:
        if not (entry.company or "").strip():
            continue
        experience.append(
            {
                "company": entry.company.strip(),
                "title": entry.job_title,
                "description": entry.description,
                "location": entry.location,
                "start_date": entry.start_date,
                "end_date": entry.end_date,
                "currently_employed": bool(entry.currently_employed),
            }
        )

    _merge_deterministic_dates(experience, deterministic_experience)

    return {
        "skills": skills,
        "education": education,
        "certifications": certifications,
        "experience": experience,
        "total_experience_years": calculate_total_experience_years(experience),
    }


def _company_key(value: str | None) -> str:
    """Aggressively normalized company key for matching AI vs deterministic
    entries ("Acme Inc." -> "acmeinc")."""
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _merge_deterministic_dates(
    experience: list[dict],
    deterministic_experience: list[dict] | None,
) -> None:
    """Fill missing AI experience dates from the deterministic parse.

    Conservative by construction:

    - Dates already extracted by the AI are never overwritten.
    - A deterministic date is adopted only for an AI entry with no dates at all,
      and only when exactly one deterministic entry shares a normalized company
      name. An ambiguous match (multiple same-company roles, or no company name
      on either side) is left unknown rather than guessed.
    - An adopted ongoing marker clears ``end_date`` so the duration calculator
      clamps to the current month instead of reading a stale end date.
    """
    if not deterministic_experience:
        return

    by_company: dict[str, list[dict]] = {}
    for entry in deterministic_experience:
        key = _company_key(entry.get("company"))
        if key and entry.get("start_date"):
            by_company.setdefault(key, []).append(entry)

    for item in experience:
        if item["start_date"]:
            continue
        candidates = by_company.get(_company_key(item.get("company")), [])
        if len(candidates) != 1:
            continue
        source = candidates[0]
        item["start_date"] = source["start_date"]
        if source.get("currently_employed"):
            item["currently_employed"] = True
            item["end_date"] = None
        else:
            item["end_date"] = source.get("end_date")


def run_resume_analysis(
    raw_text: str,
    deterministic_experience: list[dict] | None = None,
) -> tuple[dict | None, str]:
    """Analyze raw resume text and return ``(structured, status)``.

    Never raises: unexpected failures degrade to deterministic parsing with
    status ``"ai_failed"``. Only status/category and the sanitized provider
    error message are logged — never resume text, prompts, responses, or keys.

    ``deterministic_experience`` is the experience parsed from the same text; it
    is passed through to :func:`structured_to_persist` so a model that omitted
    dates still yields a real total experience.
    """
    try:
        provider = ai_provider.get_ai_provider()
    except AIProviderError as exc:
        logger.warning(
            "AI provider unavailable (category=%s, error=%s); using deterministic parse.",
            exc.category, exc,
        )
        return None, "ai_failed"

    if provider is None:
        return None, "parsed"

    text = truncate_resume_text(raw_text or "", settings.AI_MAX_RESUME_CHARS)
    if not text.strip():
        logger.warning("No extractable resume text; skipping AI analysis.")
        return None, "ai_failed"

    try:
        payload = provider.extract_resume_information(text)
        extraction = AIResumeExtraction.model_validate(payload)
    except AIProviderError as exc:
        logger.warning(
            "AI extraction failed (category=%s, error=%s); using deterministic parse.",
            exc.category, exc,
        )
        return None, "ai_failed"
    except (ValidationError, ValueError, TypeError):
        logger.warning("AI output failed validation; using deterministic parse.")
        return None, "ai_failed"
    except Exception:
        logger.error("AI provider raised an unexpected error; using deterministic parse.", exc_info=True)
        return None, "ai_failed"

    try:
        structured = structured_to_persist(extraction, deterministic_experience)
    except (ValueError, TypeError):
        logger.warning("AI enrichment failed; using deterministic parse.")
        return None, "ai_failed"

    return structured, "ai_analyzed"