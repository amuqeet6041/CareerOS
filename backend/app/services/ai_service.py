"""
AI service module.

Designed as a provider-agnostic interface for LLM-based resume analysis.
No provider is hard-coded here; configure LLM_API_KEY and implement the
provider call in `_call_llm` when ready.

IMPORTANT: This module must never return fabricated data disguised as a
real AI response. Until implemented, functions raise NotImplementedError.
"""

from app.core.config import settings


def _call_llm(prompt: str) -> str:
    """
    Placeholder for the actual LLM API call.
    Use `settings.LLM_API_KEY` and whichever provider is chosen later.
    """
    raise NotImplementedError("LLM provider integration is not configured yet.")


def analyze_resume_text(raw_text: str) -> dict:
    """
    Analyze resume text and return a structured profile:
    { skills: [...], education: [...], experience: [...], certifications: [...] }

    Placeholder: replace with a real prompt + LLM call + response parsing.
    """
    raise NotImplementedError("Resume analysis via AI is not implemented yet.")
