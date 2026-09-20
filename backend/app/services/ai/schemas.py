"""
Pydantic models the AI pipeline validates provider output against.

Validation enforces the "no guessing" rule: unknown values stay null/empty and
the deterministic duration calculation (not the model) decides whether the
overall total is unknown.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

_MONTH_YEAR_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
_FULL_DATE_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])-\d{2}$")
_MONTH_SLASH_YEAR_RE = re.compile(r"^(0[1-9]|1[0-2])/(\d{4})$")


def normalize_month_year(value) -> str | None:
    """Normalize a date to strict ``YYYY-MM``.

    Accepts ``YYYY-MM``, ``YYYY-MM-DD`` (truncated), and ``MM/YYYY``. Anything
    else (including None or outright garbage) stays None so downstream code
    treats it as missing rather than guessing.
    """
    if value is None:
        return None
    if isinstance(value, int):
        return None
    text = str(value).strip()
    match = _MONTH_YEAR_RE.match(text)
    if match:
        return text
    match = _FULL_DATE_RE.match(text)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    match = _MONTH_SLASH_YEAR_RE.match(text)
    if match:
        return f"{match.group(2)}-{match.group(1)}"
    return None


class AIEducation(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_year: int | None = Field(default=None, ge=1900, le=2100)
    end_year: int | None = Field(default=None, ge=1900, le=2100)


class AICertification(BaseModel):
    name: str
    issuer: str | None = None
    issue_year: int | None = Field(default=None, ge=1900, le=2100)
    expiry_year: int | None = Field(default=None, ge=1900, le=2100)


class AIExperience(BaseModel):
    company: str
    job_title: str | None = None
    description: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    currently_employed: bool = False

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def _validate_date(cls, value):
        normalized = normalize_month_year(value)
        if value is not None and normalized is None:
            raise ValueError(
                "Unsupported date format; expected YYYY-MM, YYYY-MM-DD, or MM/YYYY"
            )
        return normalized


class AIResumeExtraction(BaseModel):
    """The full structured shape providers are requested to return."""

    skills: list[str] = []
    education: list[AIEducation] = []
    certifications: list[AICertification] = []
    experience: list[AIExperience] = []