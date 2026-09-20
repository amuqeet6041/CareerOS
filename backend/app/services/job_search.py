"""Database-backed job search with filtering, pagination, and sorting.

Jobs are browsable without authentication. Active-only filtering is the
default: ``expires_at`` in the past OR ``is_active=false`` excludes a job.
Inactive/expired jobs can be included via ``include_inactive=True``.
"""

from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models.job import Job, JobSkill

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

SORT_NEWEST = "date_newest"
SORT_OLDEST = "date_oldest"
SORT_SALARY_DESC = "salary_desc"
SORT_OPTIONS = {SORT_NEWEST, SORT_OLDEST, SORT_SALARY_DESC}

LIKE_ESCAPE = "\\"
LIKE_PREFIX = "%"
LIKE_SUFFIX = "%"


def search_jobs(
    db: Session,
    *,
    search: str | None = None,
    location: str | None = None,
    city: str | None = None,
    work_mode: str | None = None,
    employment_type: str | None = None,
    salary_min: float | None = None,
    salary_max: float | None = None,
    source: str | None = None,
    include_inactive: bool = False,
    sort: str = SORT_NEWEST,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[int, list[Job]]:
    """Return ``(total_count, page_items)`` for the given filters.

    ``salary_min`` matches jobs whose maximum salary is at or above the value;
    ``salary_max`` matches jobs whose minimum salary is at or below it.
    """
    now = datetime.utcnow()
    query = db.query(Job)

    if not include_inactive:
        query = query.filter(
            or_(Job.expires_at.is_(None), Job.expires_at > now),
            or_(Job.is_active.is_(None), Job.is_active.is_(True)),
        )

    if search and search.strip():
        pattern = LIKE_PREFIX + _like_pattern(search.strip()) + LIKE_SUFFIX
        skill_matches = (
            db.query(JobSkill.id)
            .filter(
                JobSkill.job_id == Job.id,
                JobSkill.skill_name.ilike(pattern, escape=LIKE_ESCAPE),
            )
            .exists()
        )
        query = query.filter(
            or_(
                Job.title.ilike(pattern, escape=LIKE_ESCAPE),
                Job.company.ilike(pattern, escape=LIKE_ESCAPE),
                Job.description.ilike(pattern, escape=LIKE_ESCAPE),
                Job.location.ilike(pattern, escape=LIKE_ESCAPE),
                skill_matches,
            )
        )

    if location and location.strip():
        pattern = LIKE_PREFIX + _like_pattern(location.strip()) + LIKE_SUFFIX
        query = query.filter(Job.location.ilike(pattern, escape=LIKE_ESCAPE))

    if city and city.strip():
        pattern = LIKE_PREFIX + _like_pattern(city.strip()) + LIKE_SUFFIX
        query = query.filter(Job.city.ilike(pattern, escape=LIKE_ESCAPE))

    if work_mode:
        query = query.filter(Job.work_mode == work_mode)

    if employment_type:
        query = query.filter(Job.employment_type == employment_type)

    if salary_min is not None:
        query = query.filter(Job.salary_max >= float(salary_min))

    if salary_max is not None:
        query = query.filter(Job.salary_min <= float(salary_max))

    if source and source.strip():
        query = query.filter(Job.source == source.strip())

    total = query.count()

    if sort == SORT_SALARY_DESC:
        order = [Job.salary_max.is_(None), Job.salary_max.desc(), Job.id.desc()]
    elif sort == SORT_OLDEST:
        order = [Job.posted_at.is_(None), Job.posted_at.asc(), Job.id.asc()]
    else:  # SORT_NEWEST
        order = [Job.posted_at.is_(None), Job.posted_at.desc(), Job.id.desc()]

    items = (
        query.order_by(*order)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .options(selectinload(Job.skills), selectinload(Job.qualifications))
        .all()
    )
    return total, items


def _like_pattern(term: str) -> str:
    """Escape LIKE wildcards so user input matches literally."""
    return (
        term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )