"""Job ingestion (upsert) service.

Fetches jobs from a provider, normalizes every record, and upserts them into
``jobs`` keyed on the unique ``(source, external_id)`` pair. Returns a stats
object describing what happened so callers (CLI seeds, tests, future
scheduled syncs) can report accurate numbers:

    fetched   - records returned by the provider
    inserted  - new jobs written to the database
    updated   - existing jobs whose data changed
    skipped   - existing jobs that were already up-to-date
    failed    - records that could not be normalized/validated
"""

from dataclasses import dataclass, field

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.job import Job, JobQualification, JobSkill
from app.services.job_normalizer import (
    JobNormalizationError,
    NormalizedJob,
    normalize_provider_job,
    qualification_keys,
    skill_keys,
)
from app.services.providers.base import JobProvider
from app.utils.job_fields import is_expired
from datetime import datetime


class JobIngestionError(Exception):
    """Raised when the provider itself fails to deliver jobs."""


@dataclass
class IngestionStats:
    """Outcome of a single ingest run."""

    fetched: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


_MUTABLE_FIELDS = (
    "title",
    "company",
    "description",
    "location",
    "city",
    "country",
    "work_mode",
    "employment_type",
    "salary_min",
    "salary_max",
    "currency",
    "application_url",
    "posted_at",
    "expires_at",
    "minimum_experience_years",
    "maximum_experience_years",
)


def ingest_jobs(db: Session, provider: JobProvider, *, now: datetime | None = None):
    """Fetch, normalize, and upsert all jobs from ``provider``.

    Raises :class:`JobIngestionError` if the provider call itself fails.
    Per-record normalization failures are counted in ``stats.failed`` and do
    not stop the rest of the batch. A successful ingestion is committed.
    """
    try:
        provider_jobs = provider.fetch_jobs()
    except Exception as exc:  # noqa: BLE001 - provider bugs must surface loudly
        raise JobIngestionError(
            f"Provider '{provider.name}' failed while fetching jobs: {exc}"
        ) from exc

    now = now or datetime.utcnow()
    stats = IngestionStats(fetched=len(provider_jobs))

    for provider_job in provider_jobs:
        try:
            normalized = normalize_provider_job(provider_job)
        except (JobNormalizationError, ValidationError) as exc:
            stats.failed += 1
            stats.errors.append(str(exc))
            continue

        result = _upsert_job(db, normalized, now)
        setattr(stats, result, getattr(stats, result) + 1)

    try:
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise JobIngestionError(f"Failed to persist ingested jobs: {exc}") from exc

    return stats


def _upsert_job(db: Session, normalized: NormalizedJob, now: datetime) -> str:
    """Insert or update one job. Returns ``inserted`` | ``updated`` | ``skipped``."""
    job = (
        db.query(Job)
        .filter(
            Job.source == normalized.source,
            Job.external_id == normalized.external_id,
        )
        .first()
    )

    is_active = not is_expired(normalized.expires_at, now)
    scalar_values = {
        field_name: getattr(normalized, field_name) for field_name in _MUTABLE_FIELDS
    }
    skills = _build_skills(normalized.required_skills)
    qualifications = _build_qualifications(normalized.qualifications)

    if job is None:
        job = Job(
            source=normalized.source,
            external_id=normalized.external_id,
            is_active=is_active,
            fetched_at=now,
            **scalar_values,
        )
        db.add(job)
        db.flush()
        job.skills = skills
        job.qualifications = qualifications
        return "inserted"

    signature = _changed_signature(scalar_values, skills, qualifications, is_active)
    if signature == _current_signature(job, skills, qualifications):
        return "skipped"

    for field_name, value in scalar_values.items():
        setattr(job, field_name, value)
    job.is_active = is_active
    job.fetched_at = now
    job.updated_at = now
    # De-associate existing children and flush so their rows are deleted before
    # the replacement rows are inserted (avoids (job_id, normalized_*) unique
    # constraint collisions during the same flush).
    job.skills = []
    job.qualifications = []
    db.flush()
    job.skills = skills
    job.qualifications = qualifications
    return "updated"


def _build_skills(required_skills: list[str]) -> list[JobSkill]:
    return [
        JobSkill(skill_name=label, normalized_name=key)
        for key, label in skill_keys(required_skills).items()
    ]


def _build_qualifications(qualifications: list[str]) -> list[JobQualification]:
    return [
        JobQualification(qualification=label, normalized_qualification=key)
        for key, label in qualification_keys(qualifications).items()
    ]


def _changed_signature(scalar_values, skills, qualifications, is_active) -> tuple:
    """Represent the desired end-state so it can be compared with the current row."""
    return (
        tuple(_to_comparable(scalar_values[name]) for name in _MUTABLE_FIELDS),
        tuple(sorted((s.skill_name, s.normalized_name) for s in skills)),
        tuple(sorted((q.qualification, q.normalized_qualification) for q in qualifications)),
        is_active,
    )


def _current_signature(job: Job, skills, qualifications) -> tuple:
    return (
        tuple(_to_comparable(getattr(job, name)) for name in _MUTABLE_FIELDS),
        tuple(sorted((s.skill_name, s.normalized_name) for s in job.skills)),
        tuple(sorted((q.qualification, q.normalized_qualification) for q in job.qualifications)),
        job.is_active,
    )


def _to_comparable(value):
    """Convert values for equality comparison (datetimes are naive UTC)."""
    if isinstance(value, datetime):
        return value.replace(microsecond=0)
    return value