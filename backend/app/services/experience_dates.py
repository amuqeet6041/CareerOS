"""
Deterministic extraction of employment date ranges from human resume text.

The deterministic parser used to leave every ``start_date``/``end_date`` null,
which meant a resume whose AI call failed (rate limit, timeout, 503) fell back
to a profile with no total experience at all — even when the PDF plainly said
"Jan 2022 - Present". This module closes that gap with strict, testable
patterns.

Design rules (deliberately conservative):

- Only explicit, unambiguous ranges produce dates. A lone year, a month with no
  year, or a reversed range yields nothing.
- Output is always the canonical ``YYYY-MM`` form the rest of the app stores.
- A year-only boundary resolves to January for a start and December for an end,
  so the whole named year is counted. It never reaches beyond the years the
  resume itself states.
- An end token like ``Present``/``Current``/``Till now`` marks the role as
  ongoing; the end month is left to the duration calculator (which clamps to
  the current month) rather than written as a hardcoded date.
- ``end_date`` holds the *last month worked*, matching
  :mod:`app.services.experience_duration`'s end-exclusive arithmetic.
- Malformed input returns ``None`` instead of raising, so parsing can never
  fail an upload.
"""

from __future__ import annotations

import re

from app.services.experience_duration import MonthYear

_MONTHS: dict[str, int] = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

_MONTH_ALTERNATION = "|".join(sorted(_MONTHS, key=len, reverse=True))

# "Jan 2022", "January 2022", "Sept 2020" — month name followed by a year.
_MONTH_NAME_YEAR_RE = re.compile(
    r"\b(" + _MONTH_ALTERNATION + r")\.?\s+((?:19|20)\d{2})\b",
    re.IGNORECASE,
)

# "2022-01", "2022/01", "2022.01" — canonical plus common separators.
_NUMERIC_MONTH_YEAR_RE = re.compile(r"\b((?:19|20)\d{2})[-/.](0?[1-9]|1[0-2])\b")

# "2022-13", "2022-00", "2022-99" — a year followed by a month number that
# cannot exist. Detected so such a token is rejected outright instead of
# silently degrading to a bare year ("2022-13" must not become Jan 2022).
_IMPOSSIBLE_MONTH_YEAR_RE = re.compile(r"\b((?:19|20)\d{2})[-/.](\d{1,2})\b")


def _has_impossible_month(text: str) -> bool:
    """True when the text contains a year/month pair with an invalid month."""
    for match in _IMPOSSIBLE_MONTH_YEAR_RE.finditer(text):
        if not 1 <= int(match.group(2)) <= 12:
            return True
    return False

# A bare year, used only when it forms one end of an explicit range.
_YEAR_RE = re.compile(r"\b((?:19|20)\d{2})\b")

# Separators between the two ends of a range. A word separator must be
# surrounded by whitespace, otherwise "Toronto" would split mid-word.
_RANGE_SEP_RE = re.compile(r"(?:\s*(?:-{1,2}|[–—−])\s*|\s+to\s+)", re.IGNORECASE)
_RANGE_SEP_ONLY_RE = re.compile(r"^(?:\s*(?:-{1,2}|[–—−])\s*|\s+to\s+)$", re.IGNORECASE)

# Tokens meaning "still in this role". Word-bounded so a company named
# "Currental" is not mistaken for an ongoing marker.
_ONGOING_RE = re.compile(
    r"\b(?:present|current(?:ly)?|till\s+(?:date|now|present|current)"
    r"|to\s+(?:date|present)|ongoing|now)\b",
    re.IGNORECASE,
)

_MIN_YEAR = 1900
_MAX_YEAR = 2100

_CLOSING_PAREN_RE = re.compile(r"\s*[)\]]")


def _parse_endpoint(text: str, *, is_start: bool) -> tuple[MonthYear, int, int] | None:
    """Parse one end of a range into ``(MonthYear, span_start, span_end)``.

    Returns None when the endpoint is missing or ambiguous. The span locates
    the token inside ``text`` so :func:`strip_date_text` can cut exactly the
    date out of a combined header line.

    ``is_start`` controls only how a year-only boundary resolves: a start
    defaults to January, an end to December.
    """
    if not text:
        return None

    numeric = _NUMERIC_MONTH_YEAR_RE.search(text)
    if numeric:
        year, month = int(numeric.group(1)), int(numeric.group(2))
        if _MIN_YEAR <= year <= _MAX_YEAR:
            return MonthYear(year, month), numeric.start(), numeric.end()

    if _has_impossible_month(text):
        # A broken numeric date is a formatting error, not a bare year.
        return None

    named = _MONTH_NAME_YEAR_RE.search(text)
    if named:
        year = int(named.group(2))
        month = _MONTHS.get(named.group(1).rstrip(".").lower())
        if month and _MIN_YEAR <= year <= _MAX_YEAR:
            return MonthYear(year, month), named.start(), named.end()

    year_only = _YEAR_RE.search(text)
    if year_only:
        year = int(year_only.group(1))
        if _MIN_YEAR <= year <= _MAX_YEAR:
            return (
                MonthYear(year, 1 if is_start else 12),
                year_only.start(),
                year_only.end(),
            )

    return None


def parse_date_range(text: str) -> dict | None:
    """Extract an employment date range from one line of resume text.

    Returns ``{"start_date", "end_date", "currently_employed"}`` with canonical
    ``YYYY-MM`` strings, or ``None`` when no unambiguous range is present.
    ``end_date`` is ``None`` exactly when ``currently_employed`` is ``True``.

    Supported shapes, among others::

        Jan 2022 - Present          -> 2022-01 .. ongoing
        January 2022 – Dec 2023     -> 2022-01 .. 2023-12
        2020 to 2022                -> 2020-01 .. 2022-12
        2021/05 - 2023/06           -> 2021-05 .. 2023-06
        2019 - Present              -> 2019-01 .. ongoing
    """
    if not text or not isinstance(text, str):
        return None
    match = _match_range(text)
    if match is None:
        return None
    start, end, currently = match
    return {
        "start_date": f"{start.year:04d}-{start.month:02d}",
        "end_date": None if currently else f"{end.year:04d}-{end.month:02d}",
        "currently_employed": currently,
    }


def _match_range(text: str) -> tuple[MonthYear, MonthYear, bool] | None:
    """Locate a ``(start, end, currently_employed)`` range inside ``text``."""

    # A broken numeric date anywhere in the line ("2020-13") rejects the whole
    # line. Checked up front because the separator scan would otherwise split
    # "2020-13" at the hyphen and read a bare "2020" as a January start.
    if _has_impossible_month(text):
        return None

    # 1. An ongoing marker ends the range; only the text before it can supply
    #    the start.
    ongoing = _ONGOING_RE.search(text)
    if ongoing:
        parsed = _parse_endpoint(text[: ongoing.start()], is_start=True)
        if parsed is not None:
            return parsed[0], MonthYear(0, 0), True
        return None

    # 2. Otherwise look for two dated endpoints joined by a range separator.
    for sep in _RANGE_SEP_RE.finditer(text):
        if not _RANGE_SEP_ONLY_RE.match(sep.group(0)):
            continue
        start = _parse_endpoint(text[: sep.start()], is_start=True)
        if start is None:
            continue
        end = _parse_endpoint(text[sep.end():], is_start=False)
        if end is None:
            continue
        # Reject reversed ranges rather than returning a negative span.
        if (end[0].year, end[0].month) < (start[0].year, start[0].month):
            continue
        return start[0], end[0], False

    return None


def _range_span(text: str) -> tuple[int, int] | None:
    """Character span covering the whole date range, separator included.

    Used by :func:`strip_date_text` so the date is cut out of a header line
    without leaving orphan tokens behind.
    """
    if _has_impossible_month(text):
        return None

    ongoing = _ONGOING_RE.search(text)
    if ongoing and _match_range(text) is not None:
        start = _parse_endpoint(text[: ongoing.start()], is_start=True)
        if start is not None:
            end = ongoing.end()
            closing = _CLOSING_PAREN_RE.match(text, end)
            if text[: ongoing.start()].rstrip().endswith("(") and closing is not None:
                end = closing.end()
            return start[1], end

    for sep in _RANGE_SEP_RE.finditer(text):
        if not _RANGE_SEP_ONLY_RE.match(sep.group(0)):
            continue
        left = _parse_endpoint(text[: sep.start()], is_start=True)
        if left is None:
            continue
        right = _parse_endpoint(text[sep.end():], is_start=False)
        if right is None:
            continue
        if (right[0].year, right[0].month) < (left[0].year, left[0].month):
            continue
        end = sep.end() + right[2]
        closing = _CLOSING_PAREN_RE.match(text, end)
        if text[: sep.start()].rstrip().endswith("(") and closing is not None:
            end = closing.end()
        return left[1], end

    return None


def strip_date_text(text: str) -> str:
    """Remove a recognized date range from a line, keeping the rest readable.

    Lets a date range be pulled off a combined header line
    ("Data Analyst | Acme Inc. | Jan 2022 - Present") without leaving stray
    punctuation, parentheses, or connector words inside the company name.
    """
    if not text or not isinstance(text, str):
        return text
    span = _range_span(text)
    if span is None:
        return text
    start, end = span
    return re.sub(r"\s{2,}", " ", f"{text[:start]} {text[end:]}").strip(
        " ,;|·•–—-()[]"
    )