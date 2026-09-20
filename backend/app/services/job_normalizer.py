"""Normalizes raw provider records into the canonical CareerOS job shape.

The pipeline is:

    Provider -> ProviderJob (raw DTO) -> normalize_provider_job()
              -> NormalizedJob (canonical) -> Job service (ingest) -> DB

Normalization applies the canonical employment-type and work-mode mappings,
derives city/country when a provider only supplies a free-form location, and
rejects records that cannot be represented cleanly.
"""

from datetime import datetime
from pydantic import BaseModel, Field

from app.services.providers.base import ProviderJob
from app.utils.job_fields import (
    canonicalize_employment_type,
    canonicalize_work_mode,
    derive_city_country,
    normalize_qualification,
    normalize_skill,
    is_known_employment_type,
    is_known_work_mode,
)


class JobNormalizationError(Exception):
    """Raised when a provider record cannot be normalized into a valid job."""


class NormalizedJob(BaseModel):
    """A provider job after normalization, ready for ingestion/upsert."""

    source: str
    external_id: str
    title: str
    company: str
    description: str | None = None
    location: str | None = None
    city: str | None = None
    country: str | None = None
    work_mode: str | None = None
    employment_type: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str | None = None
    application_url: str | None = None
    posted_at: datetime | None = None
    expires_at: datetime | None = None
    required_skills: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    minimum_experience_years: float | None = None
    maximum_experience_years: float | None = None


def normalize_provider_job(provider_job: ProviderJob) -> NormalizedJob:
    """Convert a raw :class:`ProviderJob` into a :class:`NormalizedJob`.

    Raises :class:`JobNormalizationError` when the record is missing required
    fields or carries values that cannot be canonicalized (invalid employment
    type / work mode, or a salary range whose min exceeds its max).
    """
    if not provider_job.source:
        raise JobNormalizationError("Job is missing 'source'")
    if not provider_job.external_id:
        raise JobNormalizationError("Job is missing 'external_id'")
    if not (provider_job.title or "").strip():
        raise JobNormalizationError("Job is missing 'title'")
    if not (provider_job.company or "").strip():
        raise JobNormalizationError("Job is missing 'company'")

    employment_type = canonicalize_employment_type(provider_job.employment_type)
    if employment_type is None:
        given = provider_job.employment_type or "<missing>"
        raise JobNormalizationError(
            f"Invalid or missing employment_type {given!r}; expected one of: "
            f"full-time, part-time, contract, internship, temporary, freelance"
        )

    work_mode = canonicalize_work_mode(provider_job.work_mode)
    if work_mode is None and provider_job.work_mode:
        raise JobNormalizationError(
            f"Invalid work_mode {provider_job.work_mode!r}; expected one of: "
            f"remote, hybrid, onsite"
        )

    salary_min = provider_job.salary_min
    salary_max = provider_job.salary_max
    if (
        salary_min is not None
        and salary_max is not None
        and float(salary_min) > float(salary_max)
    ):
        raise JobNormalizationError(
            f"salary_min {salary_min} exceeds salary_max {salary_max}"
        )

    location = provider_job.location
    city = provider_job.city
    country = provider_job.country
    if city is None and country is None:
        derived_city, derived_country = derive_city_country(location)
        city = city or derived_city
        country = country or derived_country

    return NormalizedJob(
        source=provider_job.source,
        external_id=provider_job.external_id,
        title=provider_job.title.strip(),
        company=provider_job.company.strip(),
        description=provider_job.description,
        location=location,
        city=city,
        country=country,
        work_mode=work_mode,
        employment_type=employment_type,
        salary_min=float(salary_min) if salary_min is not None else None,
        salary_max=float(salary_max) if salary_max is not None else None,
        currency=provider_job.currency,
        application_url=provider_job.application_url,
        posted_at=provider_job.posted_at,
        expires_at=provider_job.expires_at,
        required_skills=provider_job.required_skills or [],
        qualifications=provider_job.qualifications or [],
        minimum_experience_years=_optional_float(provider_job.minimum_experience_years),
        maximum_experience_years=_optional_float(provider_job.maximum_experience_years),
    )


def _optional_float(value: float | int | None) -> float | None:
    if value is None:
        return None
    return float(value)


def skill_keys(skills: list[str]) -> dict[str, str]:
    """Map normalized skill keys to their original labels.

    Used to store both the provider's label and a dedup-friendly key while
    collapsing casing-only duplicates ("Python" and "python").
    """
    result: dict[str, str] = {}
    for skill in skills:
        key = normalize_skill(skill)
        if not key:
            continue
        if key not in result:
            result[key] = skill
    return result


def qualification_keys(qualifications: list[str]) -> dict[str, str]:
    """Same normalization/collapsing as :func:`skill_keys` for qualifications."""
    result: dict[str, str] = {}
    for qualification in qualifications:
        key = normalize_qualification(qualification)
        if not key:
            continue
        if key not in result:
            result[key] = qualification
    return result