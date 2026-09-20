"""Job provider contracts.

A provider adapts an external job source into :class:`ProviderJob` records
(the raw provider DTO). Providers never touch the database or SQLAlchemy;
they only produce structured data. The normalization layer (see
``app.services.job_normalizer``) converts those records into the canonical
CareerOS job shape before ingestion.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pydantic import BaseModel, Field


class ProviderJob(BaseModel):
    """A job as reported by a provider, before normalization.

    ``title``, ``company``, ``external_id``, and ``source`` are mandatory.
    Everything else is optional at the DTO layer; the normalizer enforces the
    stricter requirements (e.g. a canonical employment type) instead.
    """

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


class JobProvider(ABC):
    """Interface every job data provider must implement."""

    name: str = "base"

    @abstractmethod
    def fetch_jobs(self) -> list[ProviderJob]:
        """Return every job currently available from this provider.

        Providers must not raise for a single bad record; they should still
        return the rest and let normalization/ingestion record the failure.
        """
        raise NotImplementedError

    def fetch_job(self, external_id: str) -> ProviderJob | None:
        """Return one job by its source-specific ID, if supported."""
        raise NotImplementedError

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<{self.__class__.__name__} name={self.name!r}>"