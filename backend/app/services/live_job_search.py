"""Live, resume-driven job recommendations.

Builds search queries from the user's resume (preferred roles first, then
experience titles), fetches matching postings from the live job provider
(JSearch when ``JOBS_API_KEY`` is set, otherwise the keyless Jobicy
fallback),
upserts them through the normal ingestion pipeline, and ranks them with the
deterministic matching engine.

Provider quotas are small, so each user's result set is cached in-process,
keyed on a resume fingerprint, for ``JOBS_CACHE_MINUTES``.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.job import Job
from app.models.resume import Resume
from app.services.job_ingestion import JobIngestionError, ingest_jobs
from app.services.matching_engine import JobMatchResult
from app.services.matching_service import match_resume_to_job
from app.services.profile_service import get_preferences, preference_to_dict
from app.services.providers.base import JobProvider, ProviderJob
from app.services.providers.jsearch import JSearchError, JSearchProvider
from app.services.providers.jobicy import JobicyError, JobicyProvider
from app.utils.job_fields import is_expired


class LiveSearchNotConfigured(Exception):
    """Raised when no key is set and the keyless fallback is disabled."""


class LiveSearchFailed(Exception):
    """Raised when the live provider could not deliver any jobs."""


class NoSearchableProfile(Exception):
    """Raised when the resume has nothing to build a search query from."""


@dataclass
class LiveRecommendations:
    source: str
    queries: list[str]
    location: str | None
    fetched_at: datetime
    ranked: list[tuple[Job, JobMatchResult]] = field(default_factory=list)


# user_id -> (source, resume fingerprint, fetched_at, queries, location, job ids)
_cache: dict[int, tuple[str, tuple, datetime, list[str], str | None, list[int]]] = {}

# Words that make a title a job role rather than a sentence fragment.
_ROLE_WORDS = re.compile(
    r"\b(analyst|engineer|developer|scientist|manager|designer|executive|intern|"
    r"officer|specialist|consultant|assistant|coordinator|accountant|associate|"
    r"administrator|architect|lead|representative|teacher|lecturer|researcher|"
    r"marketer|writer|editor|technician|programmer|tester|auditor|advisor|"
    r"strategist|agent|supervisor)\b",
    re.IGNORECASE,
)
# Ownership titles that do not describe a searchable role on their own.
_NON_ROLE_PARTS = re.compile(
    r"^(co-?founder|founder|owner|ceo|chief .*officer|director|partner|freelancer?|self-employed)$",
    re.IGNORECASE,
)


def clear_cache() -> None:
    _cache.clear()


def _role_titles(title: str | None) -> list[str]:
    """"Founder & Business Analyst" -> ["Business Analyst"]."""
    if not title or len(title) > 60:
        return []
    roles = []
    for part in re.split(r"\s*(?:&|/|,|\band\b)\s*", title):
        part = re.sub(r"\s+", " ", part).strip(" .-")
        if not part or len(part.split()) > 5 or _NON_ROLE_PARTS.match(part):
            continue
        if _ROLE_WORDS.search(part):
            roles.append(part)
    return roles


def build_search_terms(resume: Resume, preferred_roles: list[str] | None = None) -> list[str]:
    """Distinct role titles to search for, most relevant first."""
    terms: list[str] = []
    seen: set[str] = set()

    def add(term: str) -> None:
        key = term.lower()
        if key not in seen:
            seen.add(key)
            terms.append(term)

    for role in preferred_roles or []:
        if role and role.strip():
            add(role.strip())

    experiences = sorted(resume.experience, key=lambda e: not e.currently_employed)
    for entry in experiences:
        for role in _role_titles(entry.title):
            add(role)

    if not terms:
        # No usable titles: fall back to the strongest skills.
        skills = [re.sub(r"\([^)]*\)", "", s.name).strip() for s in resume.skills if s.name]
        if skills:
            add(" ".join(skills[:2]))
    return terms


def _fingerprint(resume: Resume) -> tuple:
    """Changes on re-upload and on re-analysis (new skills/titles)."""
    return (
        resume.id,
        resume.uploaded_at,
        tuple(sorted(s.name for s in resume.skills if s.name)),
        tuple(e.title or "" for e in resume.experience),
    )


def active_source() -> str | None:
    """The live provider in use: "jsearch" with a key, else the fallback."""
    if settings.JOBS_API_KEY:
        return "jsearch"
    fallback = (settings.JOBS_FALLBACK_PROVIDER or "").strip().lower()
    return fallback if fallback == "jobicy" else None


def _cached(user_id: int, source: str, resume: Resume, now: datetime):
    entry = _cache.get(user_id)
    if not entry:
        return None
    cached_source, fingerprint, fetched_at, queries, location, job_ids = entry
    if cached_source != source or fingerprint != _fingerprint(resume):
        return None
    if now - fetched_at > timedelta(minutes=settings.JOBS_CACHE_MINUTES):
        return None
    return fetched_at, queries, location, job_ids


class _FetchedJobs(JobProvider):
    """Feeds already-fetched postings into the ingestion pipeline."""

    def __init__(self, name: str, jobs: list[ProviderJob]):
        self.name = name
        self._jobs = jobs

    def fetch_jobs(self) -> list[ProviderJob]:
        return self._jobs


def _make_provider(source: str, queries: list[str], resume: Resume) -> JobProvider:
    skills = [re.sub(r"\([^)]*\)", "", s.name).strip() for s in resume.skills if s.name]
    if source == "jobicy":
        return JobicyProvider(
            queries=queries,
            extra_skills=skills,
            geo=settings.JOBICY_GEO or None,
            allowed_regions=settings.JOBICY_ALLOWED_REGIONS.split(","),
            cache_minutes=settings.JOBICY_CACHE_MINUTES,
            timeout=settings.JOBS_TIMEOUT_SECONDS,
        )
    return JSearchProvider(
        api_key=settings.JOBS_API_KEY,
        queries=queries,
        country=settings.JOBS_DEFAULT_COUNTRY or None,
        date_posted=settings.JOBS_DATE_POSTED,
        extra_skills=skills,
        host=settings.JOBS_API_HOST,
        timeout=settings.JOBS_TIMEOUT_SECONDS,
    )


def _build_queries(source: str, terms: list[str], location: str | None) -> list[str]:
    terms = terms[: max(1, settings.JOBS_MAX_QUERIES)]
    if source == "jobicy":
        # Remote-only board searched by tag; region is filtered separately.
        return terms
    return [
        f"{term} in {location}" if location else term
        for term in terms
    ]


def recommend_live_jobs(
    db: Session,
    user_id: int,
    resume: Resume,
    *,
    refresh: bool = False,
    limit: int = 20,
    provider_factory=None,
) -> LiveRecommendations:
    """Fetch (or reuse) live jobs for this resume and rank them by match."""
    source = active_source()
    if source is None:
        raise LiveSearchNotConfigured(
            "Live job search is not configured. Set JOBS_API_KEY in backend/.env "
            "or enable JOBS_FALLBACK_PROVIDER=jobicy."
        )

    now = datetime.utcnow()
    cached = None if refresh else _cached(user_id, source, resume, now)
    if cached:
        fetched_at, queries, location, job_ids = cached
    else:
        prefs = get_preferences(db, user_id)
        prefs_dict = preference_to_dict(prefs) if prefs else {}
        terms = build_search_terms(resume, prefs_dict.get("preferred_roles"))
        if not terms:
            raise NoSearchableProfile(
                "Your resume has no job titles or skills to search with. "
                "Add a preferred role in your profile or re-analyze your resume."
            )
        location = prefs_dict.get("preferred_location") or settings.JOBS_DEFAULT_LOCATION or None
        if source == "jobicy":
            location = "Remote"
        queries = _build_queries(source, terms, location)

        provider = (provider_factory or _make_provider)(source, queries, resume)
        try:
            postings = provider.fetch_jobs()
            ingest_jobs(db, _FetchedJobs(provider.name, postings), now=now)
        except (JSearchError, JobicyError, JobIngestionError) as exc:
            raise LiveSearchFailed(str(exc)) from exc

        external_ids = [p.external_id for p in postings]
        rows = (
            db.query(Job.id, Job.external_id)
            .filter(Job.source == provider.name, Job.external_id.in_(external_ids))
            .all()
        ) if external_ids else []
        job_ids = [row.id for row in rows]
        fetched_at = now
        _cache[user_id] = (source, _fingerprint(resume), fetched_at, queries, location, job_ids)

    jobs = (
        db.query(Job)
        .options(selectinload(Job.skills), selectinload(Job.qualifications))
        .filter(Job.id.in_(job_ids))
        .all()
    ) if job_ids else []
    jobs = [job for job in jobs if job.is_active is not False and not is_expired(job.expires_at, now)]

    ranked = [(job, match_resume_to_job(resume, job)) for job in jobs]
    ranked.sort(
        key=lambda pair: (
            pair[1].overall_match_percentage is None,
            -(pair[1].overall_match_percentage or 0),
            -(pair[0].posted_at.timestamp() if pair[0].posted_at else 0),
        )
    )
    return LiveRecommendations(
        source=source,
        queries=queries,
        location=location,
        fetched_at=fetched_at,
        ranked=ranked[:limit],
    )
