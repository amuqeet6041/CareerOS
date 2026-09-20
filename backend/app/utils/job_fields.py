"""Canonical job field definitions and normalization helpers.

Employment types and work modes are represented in the database/API as a small
set of canonical lowercase values. Providers may return free-form variants
(e.g. "Full Time", "on site") which are mapped here before persistence.
"""

import re
from datetime import datetime

EMPLOYMENT_TYPES = {
    "full-time",
    "part-time",
    "contract",
    "internship",
    "temporary",
    "freelance",
}

WORK_MODES = {"remote", "hybrid", "onsite"}

_EMPLOYMENT_TYPE_SYNONYMS = {
    "full-time": "full-time",
    "full time": "full-time",
    "fulltime": "full-time",
    "full": "full-time",
    "part-time": "part-time",
    "part time": "part-time",
    "parttime": "part-time",
    "part": "part-time",
    "contract": "contract",
    "contractual": "contract",
    "internship": "internship",
    "intern": "internship",
    "internship program": "internship",
    "temporary": "temporary",
    "temp": "temporary",
    "freelance": "freelance",
    "freelancer": "freelance",
    "independent contractor": "freelance",
}

_WORK_MODE_SYNONYMS = {
    "remote": "remote",
    "fully remote": "remote",
    "work from home": "remote",
    "wfh": "remote",
    "hybrid": "hybrid",
    "onsite": "onsite",
    "on-site": "onsite",
    "on site": "onsite",
    "in office": "onsite",
    "in-office": "onsite",
    "office": "onsite",
}


def normalize_text(value: str | None) -> str | None:
    """Lowercase, strip, and collapse inner whitespace of ``value``."""
    if value is None:
        return None
    cleaned = re.sub(r"\s+", " ", str(value)).strip().lower()
    return cleaned or None


def normalize_skill(skill: str) -> str:
    """Return a stable, case-insensitive key for a skill name."""
    return normalize_text(skill) or ""


def normalize_qualification(qualification: str) -> str:
    """Return a stable, case-insensitive key for a qualification."""
    return normalize_text(qualification) or ""


def canonicalize_employment_type(value: str | None) -> str | None:
    """Map a provider-supplied employment type to its canonical value."""
    key = normalize_text(value)
    if key is None:
        return None
    return _EMPLOYMENT_TYPE_SYNONYMS.get(key)


def canonicalize_work_mode(value: str | None) -> str | None:
    """Map a provider-supplied work mode to its canonical value."""
    key = normalize_text(value)
    if key is None:
        return None
    return _WORK_MODE_SYNONYMS.get(key)


def is_known_employment_type(value: str | None) -> bool:
    return value in EMPLOYMENT_TYPES


def is_known_work_mode(value: str | None) -> bool:
    return value in WORK_MODES


def derive_city_country(location: str | None) -> tuple[str | None, str | None]:
    """Best-effort split of a free-form ``location`` into city and country.

    Examples: "Lahore, Pakistan" -> ("Lahore", "Pakistan");
    "Remote" -> (None, None); "Karachi" -> ("Karachi", None).
    """
    if not location:
        return None, None
    parts = [part.strip() for part in location.split(",") if part.strip()]
    if not parts:
        return None, None
    if len(parts) == 1:
        return parts[0], None
    city = ", ".join(parts[:-1])
    return city or None, parts[-1]


def is_expired(expires_at: datetime | None, now: datetime | None = None) -> bool:
    """Return True when ``expires_at`` is in the past (or equal to now)."""
    if expires_at is None:
        return False
    now = now or datetime.utcnow()
    if expires_at.tzinfo is not None:
        expires_at = _to_naive_utc(expires_at)
    return expires_at <= now


def _to_naive_utc(value: datetime) -> datetime:
    """Convert an aware datetime to naive UTC so comparisons stay consistent."""
    if value.tzinfo is None:
        return value
    return value.astimezone(__import__("datetime").timezone.utc).replace(tzinfo=None)