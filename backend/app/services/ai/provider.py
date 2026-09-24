"""
Provider implementations and the factory that selects one from settings.

- ``OpenAICompatibleProvider`` talks to any OpenAI-compatible
  ``/chat/completions`` endpoint over httpx. It raises typed
  :class:`app.services.ai.base.AIProviderError` subclasses so the pipeline can
  fall back to deterministic parsing without exposing provider internals.
- ``MockAIProvider`` is for development/tests and is refused in production by
  config validation.
- ``get_ai_provider()`` returns ``None`` when AI is disabled, the configured
  provider, or raises :class:`AIConfigurationError` for invalid configuration.
"""

from __future__ import annotations

import json
import logging

import httpx

from app.core.config import settings
from app.services.ai.base import (
    AIOutputError,
    AIProvider,
    AIRequestError,
    AIConfigurationError,
)
from app.services.ai.prompts import build_messages

logger = logging.getLogger("careeros.ai")

SUPPORTED_PROVIDERS = {"openai", "gemini"}


def parse_json_payload(content: str) -> dict:
    """Parse a provider response into a JSON object dict.

    Tolerates a small amount of provider noise (e.g. a markdown code fence)
    but never evals or executes anything.
    """
    text = (content or "").strip()
    if not text:
        raise AIOutputError("AI provider returned an empty response.")

    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise AIOutputError("AI provider returned non-JSON output.")
        try:
            data = json.loads(text[start : end + 1])
        except (ValueError, TypeError):
            raise AIOutputError("AI provider returned malformed JSON output.")

    if not isinstance(data, dict):
        raise AIOutputError("AI provider returned a non-object JSON payload.")
    return data


class OpenAICompatibleProvider(AIProvider):
    """OpenAI-compatible chat-completions provider using httpx directly."""

    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: int = 30,
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def _chat(self, messages: list[dict]) -> dict:
        """Call the chat-completions endpoint and return a parsed JSON object."""
        url = f"{self._base_url}/chat/completions"
        payload = {
            "model": self._model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0,
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}

        try:
            response = httpx.post(
                url,
                json=payload,
                headers=headers,
                timeout=self._timeout_seconds,
            )
        except httpx.TimeoutException as exc:
            raise AIRequestError(
                "AI provider request timed out.", category="timeout"
            ) from exc
        except httpx.HTTPError as exc:
            raise AIRequestError(
                "AI provider request failed (network/transport).",
                category="provider_unavailable",
            ) from exc

        if response.status_code in (401, 403):
            raise AIRequestError(
                "AI provider rejected the API key.", category="invalid_key"
            )
        if response.status_code == 429:
            raise AIRequestError(
                "AI provider rate limit exceeded.", category="rate_limit"
            )
        if response.status_code != 200:
            # Body is deliberately not included: it may echo the request.
            raise AIRequestError(
                f"AI provider returned HTTP {response.status_code}.",
                category="provider_error",
            )

        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise AIOutputError(
                "AI provider response was missing the expected payload shape."
            ) from exc

        return parse_json_payload(content)

    def extract_resume_information(self, text: str) -> dict:
        return self._chat(build_messages(text))

    def generate_career_insights(self, messages: list[dict]) -> dict:
        return self._chat(messages)


class MockAIProvider(AIProvider):
    """Deterministic provider for development and tests."""

    name = "mock"

    def __init__(self, response: dict | None = None, error: Exception | None = None):
        self._response = response if response is not None else {}
        self._error = error

    def extract_resume_information(self, text: str) -> dict:
        if self._error is not None:
            raise self._error
        return self._response

    def generate_career_insights(self, messages: list[dict]) -> dict:
        if self._error is not None:
            raise self._error
        return self._response


PROVIDER_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GEMINI_DEFAULT_MODEL = "gemini-3.6-flash"


def get_ai_provider() -> AIProvider | None:
    """Select the provider from settings, or None when AI is disabled."""
    name = (settings.AI_PROVIDER or "").strip().lower()
    if not name:
        return None

    if name == "mock":
        return MockAIProvider()

    if name not in SUPPORTED_PROVIDERS:
        raise AIConfigurationError(
            f"Unsupported AI_PROVIDER {name!r}; supported: {sorted(SUPPORTED_PROVIDERS or [])}"
        )

    base_url = (settings.AI_BASE_URL or "").strip()
    model = (settings.AI_MODEL or "").strip()

    if name == "gemini":
        # Google's OpenAI-compatible chat-completions endpoint. Uses the same
        # provider class as OpenAI — no separate bespoke provider. If the
        # operator did not pick a different base URL/model, use Gemini's own
        # defaults.
        if not base_url:
            base_url = PROVIDER_GEMINI_BASE_URL
        if not model:
            model = GEMINI_DEFAULT_MODEL

    if not base_url:
        base_url = "https://api.openai.com/v1"
    if not model:
        model = "gpt-4o-mini"

    if not (settings.AI_API_KEY or "").strip():
        raise AIConfigurationError(
            "AI_PROVIDER is configured but AI_API_KEY is not set."
        )

    return OpenAICompatibleProvider(
        api_key=settings.AI_API_KEY,
        model=model,
        base_url=base_url,
        timeout_seconds=settings.AI_TIMEOUT_SECONDS,
    )