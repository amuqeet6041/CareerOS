"""
Deprecated. Superseded in Phase 3 by the provider-agnostic AI resume
intelligence package in :mod:`app.services.ai` (``base.py``, ``provider.py``,
``pipeline.py``).

This module exists only so legacy imports keep working. New code must use
:func:`app.services.ai.pipeline.run_resume_analysis` instead, which is wired
into ``POST /api/resume/upload`` and ``POST /api/resume/analyze``.
"""

from app.core.config import settings  # noqa: F401


def _call_llm(prompt: str) -> str:
    """Legacy placeholder, superseded by app.services.ai.provider."""
    raise NotImplementedError(
        "LLM provider integration moved to app.services.ai.provider."
    )


def analyze_resume_text(raw_text: str) -> dict:
    """Legacy placeholder, superseded by app.services.ai.pipeline."""
    raise NotImplementedError(
        "Resume analysis via AI moved to app.services.ai.pipeline."
    )