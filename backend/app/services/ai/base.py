"""
AI provider abstraction for resume intelligence.

The pipeline (:mod:`app.services.ai.pipeline`) asks a provider to turn raw
resume text into a structured extraction. Providers never compute match
scores, verify facts they cannot see, or invent missing information — that is
all done deterministically elsewhere.

Error categories are used for structured logging only; provider responses and
extraction text are never logged.
"""

from __future__ import annotations

import abc


class AIProviderError(Exception):
    """Base class for AI-layer failures."""

    category = "ai_error"

    def __init__(self, message: str, *, category: str | None = None):
        super().__init__(message)
        if category is not None:
            self.category = category


class AIConfigurationError(AIProviderError):
    """Provider cannot be constructed (missing key, unsupported provider)."""

    category = "configuration"


class AIRequestError(AIProviderError):
    """Provider call failed (timeout, unavailable, invalid key, rate limit)."""

    category = "provider_error"


class AIOutputError(AIProviderError):
    """Provider returned output that could not be parsed or validated."""

    category = "output_error"


class AIProvider(abc.ABC):
    """Interface every resume-intelligence provider implements."""

    name: str = "base"

    @abc.abstractmethod
    def extract_resume_information(self, text: str) -> dict:
        """Return a JSON-object-shaped dict of structured resume information.

        Raises a subclass of :class:`AIProviderError` on failure. The return
        value is an unvalidated dict; structured validation happens in the
        pipeline.
        """

    def generate_career_insights(self, messages: list[dict]) -> dict:
        """Return a JSON-object-shaped dict of career insights for verified data.

        ``messages`` is the full system+user message list built by the
        career-insights prompts module; the provider is expected to return a
        plain JSON object (never raw text or markdown).

        Defaults to raising :class:`AIOutputError` so existing providers keep
        working unchanged; providers that support explanatory insights override
        this method. Raises a subclass of :class:`AIProviderError` on failure.
        """
        raise AIOutputError("Provider does not support career insights.")