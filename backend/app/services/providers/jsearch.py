"""JSearch job provider (RapidAPI).

JSearch aggregates live postings from Google for Jobs (LinkedIn, Indeed,
Rozee, company sites, ...). The provider runs one ``/search`` request per
query and maps each posting into a :class:`ProviderJob`.

JSearch rarely returns structured skills, so required skills are inferred by
finding known skill names (a common vocabulary plus the candidate's own
skills) in the posting's title, description and highlights. Skills not in the
vocabulary are not invented.
"""

import re
from datetime import datetime

import httpx

from app.services.providers.base import JobProvider, ProviderJob

SOURCE = "jsearch"
# JSearch v5 search endpoint (the v4 "/search" path now returns 404).
SEARCH_PATH = "/search-v2"

# Skills commonly named in postings. Matched case-insensitively on word
# boundaries; the candidate's resume skills are added per search.
COMMON_SKILLS = [
    # Data / analytics
    "SQL", "Python", "R", "Excel", "Power BI", "Tableau", "Looker", "Pandas",
    "NumPy", "Matplotlib", "Statistics", "Data Analysis", "Data Visualization",
    "Data Cleaning", "Data Modeling", "ETL", "Machine Learning", "Deep Learning",
    "TensorFlow", "PyTorch", "Scikit-learn", "Stata", "SPSS", "SAS",
    "Google Analytics", "Regression Analysis", "Hypothesis Testing",
    "Business Intelligence", "Financial Modeling", "Snowflake", "BigQuery",
    "Spark", "Hadoop", "Airflow", "dbt",
    # Software
    "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "Express",
    "Angular", "Vue", "HTML", "CSS", "Tailwind CSS", "Java", "C#", "C++",
    ".NET", "PHP", "Laravel", "Django", "Flask", "FastAPI", "Go", "Kotlin",
    "Swift", "Flutter", "Dart", "React Native", "REST APIs", "GraphQL",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes", "AWS",
    "Azure", "GCP", "Linux", "Git", "CI/CD", "Selenium", "Jira",
    # Business / general
    "CRM", "Salesforce", "SEO", "Google Ads", "Social Media Marketing",
    "Content Writing", "Shopify", "Amazon Seller Central", "QuickBooks",
    "Accounting", "Financial Reporting", "Project Management", "Agile",
    "Scrum", "Figma", "Communication", "Customer Service", "Negotiation",
    "MS Office", "Recruitment",
]

_EMPLOYMENT_TYPES = {
    "FULLTIME": "full-time",
    "PARTTIME": "part-time",
    "CONTRACTOR": "contract",
    "INTERN": "internship",
    "TEMPORARY": "temporary",
    "PER_DIEM": "temporary",
}

_DEGREE_FLAGS = (
    ("postgraduate_degree", "Master's degree"),
    ("bachelors_degree", "Bachelor's degree"),
)


class JSearchError(Exception):
    """Raised when the JSearch API cannot be reached or rejects a request."""


def skill_pattern(skill: str) -> re.Pattern:
    """Word-boundary regex for a skill name ("C++" and ".NET" safe).

    Very short names ("R", "Go", "C") are matched case-sensitively, otherwise
    every "go to market" or "r&d" would count as a programming language.
    """
    name = skill.strip()
    escaped = re.escape(name)
    flags = 0 if len(name) <= 2 else re.IGNORECASE
    return re.compile(rf"(?<![\w+#.]){escaped}(?![\w+#&])", flags)


def extract_skills(text: str, vocabulary: list[str]) -> list[str]:
    """Return the vocabulary skills mentioned in ``text`` (first-seen order)."""
    found: list[str] = []
    seen: set[str] = set()
    for skill in vocabulary:
        key = skill.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        if skill_pattern(skill).search(text):
            found.append(skill.strip())
    return found


def _parse_datetime(value) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=None)


def _employment_type(item: dict) -> str:
    types = item.get("job_employment_types") or []
    raw = (types[0] if types else item.get("job_employment_type")) or ""
    raw = str(raw).split(",")[0].strip().upper()
    # Postings without a type are overwhelmingly full-time listings; the
    # normalizer requires a canonical value.
    return _EMPLOYMENT_TYPES.get(raw, "full-time")


def _location(item: dict) -> str | None:
    if item.get("job_location"):
        return item["job_location"]
    parts = [item.get("job_city"), item.get("job_state"), item.get("job_country")]
    joined = ", ".join(p for p in parts if p)
    return joined or None


def _experience_years(item: dict) -> float | None:
    required = item.get("job_required_experience") or {}
    months = required.get("required_experience_in_months")
    if isinstance(months, (int, float)) and months > 0:
        return round(months / 12, 1)
    return None


def _qualifications(item: dict) -> list[str]:
    education = item.get("job_required_education") or {}
    for flag, label in _DEGREE_FLAGS:
        if education.get(flag):
            return [label]
    return []


def _salary(item: dict, key: str) -> float | None:
    value = item.get(key)
    return float(value) if isinstance(value, (int, float)) and value > 0 else None


def map_posting(item: dict, vocabulary: list[str]) -> ProviderJob | None:
    """Map one JSearch posting to a ProviderJob; None if unusable."""
    job_id = item.get("job_id")
    title = (item.get("job_title") or "").strip()
    company = (item.get("employer_name") or "").strip()
    if not job_id or not title or not company:
        return None

    highlights = item.get("job_highlights") or {}
    highlight_text = " ".join(
        line for lines in highlights.values() if isinstance(lines, list) for line in lines
    )
    description = item.get("job_description") or ""
    structured_skills = [s for s in (item.get("job_required_skills") or []) if s]
    skills = structured_skills or extract_skills(
        f"{title}\n{description}\n{highlight_text}", vocabulary
    )

    min_salary = _salary(item, "job_min_salary")
    max_salary = _salary(item, "job_max_salary")
    return ProviderJob(
        source=SOURCE,
        external_id=str(job_id),
        title=title,
        company=company,
        description=description or None,
        location=_location(item),
        city=item.get("job_city"),
        country=item.get("job_country"),
        work_mode="remote" if item.get("job_is_remote") else None,
        employment_type=_employment_type(item),
        salary_min=min_salary,
        salary_max=max_salary,
        currency=item.get("job_salary_currency") if (min_salary or max_salary) else None,
        application_url=item.get("job_apply_link"),
        posted_at=_parse_datetime(item.get("job_posted_at_datetime_utc")),
        expires_at=_parse_datetime(item.get("job_offer_expiration_datetime_utc")),
        required_skills=skills,
        qualifications=_qualifications(item),
        minimum_experience_years=_experience_years(item),
    )


class JSearchProvider(JobProvider):
    """Fetch live postings for a set of search queries."""

    name = SOURCE

    def __init__(
        self,
        *,
        api_key: str,
        queries: list[str],
        country: str | None = None,
        date_posted: str = "month",
        extra_skills: list[str] | None = None,
        host: str = "jsearch.p.rapidapi.com",
        timeout: float = 20,
        client: httpx.Client | None = None,
    ):
        if not api_key:
            raise JSearchError("JOBS_API_KEY is not configured.")
        self.api_key = api_key
        self.queries = queries
        self.country = country
        self.date_posted = date_posted
        self.host = host
        self.timeout = timeout
        self.client = client
        # Candidate skills first so their display names win on duplicates.
        self.vocabulary = [*(extra_skills or []), *COMMON_SKILLS]

    def _search(self, client: httpx.Client, query: str) -> list[dict]:
        params = {"query": query, "page": "1", "num_pages": "1", "date_posted": self.date_posted}
        if self.country:
            params["country"] = self.country
        try:
            response = client.get(
                f"https://{self.host}{SEARCH_PATH}",
                params=params,
                headers={"X-RapidAPI-Key": self.api_key, "X-RapidAPI-Host": self.host},
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise JSearchError(f"JSearch request failed: {exc}") from exc
        if response.status_code in (401, 403):
            raise JSearchError("JSearch rejected the API key (check JOBS_API_KEY and your RapidAPI subscription).")
        if response.status_code == 429:
            raise JSearchError("JSearch rate limit or monthly quota reached.")
        if response.status_code >= 400:
            raise JSearchError(f"JSearch returned HTTP {response.status_code}: {response.text[:200]}")
        data = response.json().get("data")
        # v5 wraps postings as {"jobs": [...], "cursor": ...}; v4 used a list.
        if isinstance(data, dict):
            data = data.get("jobs")
        return data if isinstance(data, list) else []

    def fetch_jobs(self) -> list[ProviderJob]:
        client = self.client or httpx.Client()
        jobs: dict[str, ProviderJob] = {}
        errors: list[str] = []
        try:
            for query in self.queries:
                try:
                    postings = self._search(client, query)
                except JSearchError as exc:
                    errors.append(str(exc))
                    continue
                for item in postings:
                    job = map_posting(item, self.vocabulary)
                    if job and job.external_id not in jobs:
                        jobs[job.external_id] = job
        finally:
            if self.client is None:
                client.close()
        # Only fail when every query failed; partial results are still useful.
        if errors and len(errors) == len(self.queries):
            raise JSearchError(errors[0])
        return list(jobs.values())
