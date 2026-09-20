"""Small text-processing helpers shared across resume/matching services."""

import re


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def to_lower_set(items: list[str]) -> set[str]:
    return {item.strip().lower() for item in items if item and item.strip()}
