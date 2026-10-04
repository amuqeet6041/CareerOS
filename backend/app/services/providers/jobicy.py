"""Jobicy job provider (keyless fallback).

Jobicy's public API serves real remote postings without an API key. Its terms
ask clients to credit Jobicy with a link to the source and send applicants to
the original job URL, so jobs are stored with ``source="jobicy"`` and the
Jobicy posting URL as the apply link. Results are cached per query for every
user (``JOBICY_CACHE_MINUTES``) to keep request volume low.

Most postings are restricted to specific countries ("USA", "UK"). Only those
open to one of ``allowed_regions`` (e.g. "Anywhere", "APAC") are kept.
"""

import html
import re
from datetime import datetime, timedelta, timezone

import httpx

from app.services.providers.base import JobProvider, ProviderJob
from app.services.providers.jsearch import COMMON_SKILLS, extract_skills

SOURCE = "jobicy"
API_URL = "https://jobicy.com/api/v2/remote-jobs"

_JOB_TYPES = {
    "full-time": "full-time",
    "part-time": "part-time",
    "contract": "contract",
    "freelance": "freelance",
    "internship": "internship",
    "temporary": "temporary",
}

# query -> (fetched_at, postings); shared across users.
_query_cache: dict[str, tuple[datetime, list[dict]]] = {}


class JobicyError(Exception):
    """Raised when the Jobicy API cannot be reached or rejects a request."""


def clear_cache() -> None:
    _query_cache.clear()


def html_to_text(value: str) -> str:
    text = re.sub(r"<\s*(br|/p|/li|/h\d)\s*/?>", "\n", value or "", flags=re.IGNORECASE)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def _parse_datetime(value) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def region_allowed(geo: str | None, allowed_regions: list[str]) -> bool:
    """True when the posting is open to one of ``allowed_regions``."""
    if not allowed_regions:
        return True
    text = (geo or "").lower()
    if not text.strip():
        return True
    return any(re.search(rf"\b{re.escape(region)}\b", text) for region in allowed_regions)


def _employment_type(value) -> str:
    types = value if isinstance(value, list) else [value]
    raw = str(types[0] if types else "").strip().lower()
    return _JOB_TYPES.get(raw, "full-time")


def _salary(item: dict) -> tuple[float | None, float | None, str | None]:
    # Hourly/monthly figures would be misread as annual salaries; keep yearly only.
    if str(item.get("salaryPeriod") or "").lower() not in ("yearly", "annual"):
        return None, None, None

    def number(value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None
        return value if value > 0 else None

    low, high = number(item.get("salaryMin")), number(item.get("salaryMax"))
    if low and high and low > high:
        low, high = high, low
    return low, high, (item.get("salaryCurrency") if (low or high) else None)


def map_posting(item: dict, vocabulary: list[str]) -> ProviderJob | None:
    job_id = item.get("id")
    title = html.unescape((item.get("jobTitle") or "").strip())
    company = html.unescape((item.get("companyName") or "").strip())
    if not job_id or not title or not company:
        return None

    description = html_to_text(item.get("jobDescription") or item.get("jobExcerpt") or "")
    salary_min, salary_max, currency = _salary(item)
    geo = (item.get("jobGeo") or "").strip()

    return ProviderJob(
        source=SOURCE,
        external_id=str(job_id),
        title=title,
        company=company,
        description=description or None,
        location=f"Remote ({geo})" if geo else "Remote",
        work_mode="remote",
        employment_type=_employment_type(item.get("jobType")),
        salary_min=salary_min,
        salary_max=salary_max,
        currency=currency,
        application_url=item.get("url"),
        posted_at=_parse_datetime(item.get("pubDate")),
        required_skills=extract_skills(f"{title}\n{description}", vocabulary),
    )


class JobicyProvider(JobProvider):
    """Fetch live remote postings for a set of search terms (no key needed)."""

    name = SOURCE

    def __init__(
        self,
        *,
        queries: list[str],
        extra_skills: list[str] | None = None,
        geo: str | None = "apac",
        allowed_regions: list[str] | None = None,
        count: int = 50,
        cache_minutes: int = 360,
        timeout: float = 20,
        client: httpx.Client | None = None,
    ):
        self.queries = queries
        self.vocabulary = [*(extra_skills or []), *COMMON_SKILLS]
        self.geo = geo
        self.allowed_regions = [r.strip().lower() for r in (allowed_regions or []) if r.strip()]
        self.count = count
        self.cache_ttl = timedelta(minutes=cache_minutes)
        self.timeout = timeout
        self.client = client

    def _search(self, client: httpx.Client, query: str) -> list[dict]:
        params = {"count": str(self.count), "tag": query}
        if self.geo:
            params["geo"] = self.geo
        key = "|".join(f"{k}={v}" for k, v in sorted(params.items())).lower()
        now = datetime.utcnow()
        cached = _query_cache.get(key)
        if cached and now - cached[0] < self.cache_ttl:
            return cached[1]
        try:
            response = client.get(API_URL, params=params, timeout=self.timeout)
        except httpx.HTTPError as exc:
            raise JobicyError(f"Jobicy request failed: {exc}") from exc
        if response.status_code == 429:
            raise JobicyError("Jobicy rate limit reached; try again later.")
        if response.status_code >= 400:
            raise JobicyError(f"Jobicy returned HTTP {response.status_code}.")
        jobs = response.json().get("jobs")
        jobs = jobs if isinstance(jobs, list) else []
        _query_cache[key] = (now, jobs)
        return jobs

    def fetch_jobs(self) -> list[ProviderJob]:
        client = self.client or httpx.Client()
        jobs: dict[str, ProviderJob] = {}
        errors: list[str] = []
        try:
            for query in self.queries:
                try:
                    postings = self._search(client, query)
                except JobicyError as exc:
                    errors.append(str(exc))
                    continue
                for item in postings:
                    if not region_allowed(item.get("jobGeo"), self.allowed_regions):
                        continue
                    job = map_posting(item, self.vocabulary)
                    if job and job.external_id not in jobs:
                        jobs[job.external_id] = job
        finally:
            if self.client is None:
                client.close()
        if errors and len(errors) == len(self.queries):
            raise JobicyError(errors[0])
        return list(jobs.values())
