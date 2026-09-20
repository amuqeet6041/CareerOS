"""
Deterministic employment-duration calculation.

Converts per-job ``YYYY-MM`` dates into an inclusive total of experienced
months, then years, without ever inventing missing information.

Policy (documented in docs/PHASE_3_REPORT.md):

- Each job counts its start month inclusive and its end month exclusive, so
  ``2024-01 -> 2025-01`` is exactly 12 months (1.0 year).
- A job marked ``currently_employed`` runs through the current month.
- Overlapping and adjacent jobs are merged so shared months are never
  double-counted.
- If ANY relevant date is missing, malformed, or inconsistent (end before
  start, start in the future), the total is ``None`` rather than a guess.
- An end date in the future is clamped to the current month.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

_MONTH_YEAR_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@dataclass(frozen=True)
class MonthYear:
    year: int
    month: int

    def index(self) -> int:
        """Zero-based absolute month count (1970-01 == 0)."""
        return (self.year - 1970) * 12 + (self.month - 1)


def parse_month_year(value) -> MonthYear | None:
    """Parse a strict ``YYYY-MM`` string. Returns None for anything else."""
    if value is None or not isinstance(value, str):
        return None
    match = _MONTH_YEAR_RE.match(value.strip())
    if not match:
        return None
    year, month = int(value[:4]), int(value[5:7])
    return MonthYear(year, month)


def current_month_year() -> MonthYear:
    now = datetime.utcnow()
    return MonthYear(now.year, now.month)


def _resolve_interval(exp: dict, now: MonthYear) -> tuple[int, int] | None:
    """Resolve one job to a closed month interval [start, end).

    Returns None when the interval cannot be derived reliably (missing or
    malformed start, missing end when not currently employed, end before start,
    or a start date in the future). End dates beyond now clamp to now.
    """
    start = parse_month_year(exp.get("start_date"))
    if start is None:
        return None

    currently = bool(exp.get("currently_employed"))
    end = now if currently else parse_month_year(exp.get("end_date"))
    if end is None:
        return None

    start_index, end_index = start.index(), end.index()
    if end_index < start_index or start_index > now.index():
        return None

    return start_index, min(end_index, now.index())


def calculate_experience_months(experiences, now: MonthYear | None = None) -> int | None:
    """Total (merged) months of experience across all jobs, or None when unknown.

    The total is None when any job lacks reliable date information, or when
    there are no jobs at all — we never present an unknown as zero.
    """
    now = now or current_month_year()
    intervals: list[tuple[int, int]] = []
    for exp in experiences:
        if not (exp.get("company") or "").strip():
            continue
        interval = _resolve_interval(exp, now)
        if interval is None:
            return None
        intervals.append(interval)

    if not intervals:
        return None

    intervals.sort()
    merged: list[tuple[int, int]] = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return sum(end - start for start, end in merged)


def calculate_total_experience_years(experiences, now: MonthYear | None = None) -> float | None:
    """Total experience in years (2-decimal), or None when unknown."""
    months = calculate_experience_months(experiences, now=now)
    if months is None:
        return None
    return round(months / 12, 2)