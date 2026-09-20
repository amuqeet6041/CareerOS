"""
Job service module.

Provides a normalized interface for fetching jobs from external providers.
Add new provider adapters under this module and normalize their output to
match the `Job` model / `JobOut` schema before returning.
"""

from app.core.config import settings


class JobProvider:
    """Base class for a job data provider/adapter."""

    name: str = "base"

    def fetch_jobs(self, query: dict) -> list[dict]:
        raise NotImplementedError


class PlaceholderJobProvider(JobProvider):
    """
    Placeholder provider used until a real, approved job API is connected.
    Returns an empty list rather than fabricated job data.
    """

    name = "placeholder"

    def fetch_jobs(self, query: dict) -> list[dict]:
        return []


def get_active_provider() -> JobProvider:
    # Swap this out once JOBS_API_KEY and a real provider are configured.
    return PlaceholderJobProvider()


def search_jobs(query: dict) -> list[dict]:
    provider = get_active_provider()
    return provider.fetch_jobs(query)
