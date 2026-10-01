"""Tests for bounded AI provider retry behaviour (Phase 8).

Real Gemini/OpenAI traffic produces HTTP 429 (rate limit) and 503 (model
overloaded) and occasional connection resets. Before this change every one of
those became an immediate upload failure path, and a valid API key could not
recover from a momentary blip. These tests pin the retry contract:

- Transient failures (429/408/5xx, timeout, transport) retry a bounded number
  of times and then either succeed or surface the last typed error.
- Permanent failures (invalid key, bad request, unusable output) fail on the
  first attempt with no retry.
- Backoff is exponential, capped, and injectable so no test ever sleeps.

No real API key or network access is used; httpx is patched.
"""

import httpx
import pytest

from app.core.config import Settings, settings
from app.services.ai.base import (
    AIOutputError,
    AIRequestError,
    is_transient_category,
)
from app.services.ai.provider import (
    RETRYABLE_STATUS_CODES,
    MockAIProvider,
    OpenAICompatibleProvider,
    get_ai_provider,
)

SUCCESS_BODY = {"choices": [{"message": {"content": '{"skills": ["Python"]}'}}]}


def _response(status_code, body=None):
    class FakeResponse:
        def __init__(self):
            self.status_code = status_code
            self._body = body

        def json(self):
            if self._body is None:
                return {}
            return self._body

    return FakeResponse()


def _provider(monkeypatch, *, max_retries=2, sleep=None):
    slept: list[float] = []
    provider = OpenAICompatibleProvider(
        api_key="sk-test",
        max_retries=max_retries,
        retry_base_delay=0.5,
        retry_max_delay=4.0,
        sleep=slept.append if sleep is None else sleep,
    )
    return provider, slept


def _script_post(monkeypatch, script):
    """Patch httpx.post with a list of statuses (or exceptions) consumed in
    order; the last entry repeats if more calls happen."""
    calls = {"n": 0}

    def _post(*args, **kwargs):
        index = min(calls["n"], len(script) - 1)
        calls["n"] += 1
        item = script[index]
        if isinstance(item, Exception):
            raise item
        return _response(item, SUCCESS_BODY if item == 200 else None)

    monkeypatch.setattr("app.services.ai.provider.httpx.post", _post)
    return calls


# ---------------------------------------------------------------------------
# Category classification
# ---------------------------------------------------------------------------


def test_transient_categories_are_exactly_the_retryable_ones():
    for category in ("timeout", "rate_limit", "provider_unavailable"):
        assert is_transient_category(category) is True
    for category in (
        "invalid_key",
        "provider_error",
        "configuration",
        "output_error",
        "ai_error",
    ):
        assert is_transient_category(category) is False


def test_retryable_status_codes_exclude_permanent_client_errors():
    assert {408, 429, 500, 502, 503, 504} <= RETRYABLE_STATUS_CODES
    assert 400 not in RETRYABLE_STATUS_CODES
    assert 401 not in RETRYABLE_STATUS_CODES
    assert 404 not in RETRYABLE_STATUS_CODES
    assert 422 not in RETRYABLE_STATUS_CODES


@pytest.mark.parametrize("status", [401, 403])
def test_invalid_key_fails_immediately_without_retry(monkeypatch, status):
    calls = _script_post(monkeypatch, [status])
    provider, slept = _provider(monkeypatch, max_retries=3)
    with pytest.raises(AIRequestError) as excinfo:
        provider.extract_resume_information("hi")
    assert excinfo.value.category == "invalid_key"
    assert calls["n"] == 1
    assert slept == []


@pytest.mark.parametrize("status", [400, 404, 422])
def test_permanent_client_errors_fail_without_retry(monkeypatch, status):
    calls = _script_post(monkeypatch, [status])
    provider, slept = _provider(monkeypatch, max_retries=3)
    with pytest.raises(AIRequestError) as excinfo:
        provider.extract_resume_information("hi")
    assert excinfo.value.category == "provider_error"
    assert calls["n"] == 1
    assert slept == []


def test_output_error_does_not_retry(monkeypatch):
    """A 200 with an unusable body is not fixed by calling again."""
    calls = {"n": 0}

    def _post(*args, **kwargs):
        calls["n"] += 1
        return _response(200, {"choices": []})

    monkeypatch.setattr("app.services.ai.provider.httpx.post", _post)
    provider, slept = _provider(monkeypatch, max_retries=3)
    with pytest.raises(AIOutputError):
        provider.extract_resume_information("hi")
    assert calls["n"] == 1
    assert slept == []


# ---------------------------------------------------------------------------
# Retry on transient failures
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("status", [429, 503, 500, 502, 504, 408])
def test_transient_status_is_retried_then_succeeds(monkeypatch, status):
    calls = _script_post(monkeypatch, [status, 200])
    provider, slept = _provider(monkeypatch, max_retries=2)
    assert provider.extract_resume_information("hi") == {"skills": ["Python"]}
    assert calls["n"] == 2
    assert len(slept) == 1


def test_rate_limit_then_success_keeps_real_category_on_exhaustion(monkeypatch):
    calls = _script_post(monkeypatch, [429])
    provider, _ = _provider(monkeypatch, max_retries=2)
    with pytest.raises(AIRequestError) as excinfo:
        provider.extract_resume_information("hi")
    # 1 initial attempt + 2 retries.
    assert calls["n"] == 3
    assert excinfo.value.category == "rate_limit"


def test_timeout_is_retried(monkeypatch):
    calls = _script_post(monkeypatch, [httpx.TimeoutException("slow"), 200])
    provider, slept = _provider(monkeypatch, max_retries=2)
    assert provider.extract_resume_information("hi") == {"skills": ["Python"]}
    assert calls["n"] == 2
    assert len(slept) == 1


def test_connection_error_is_retried(monkeypatch):
    calls = _script_post(monkeypatch, [httpx.ConnectError("reset"), 200])
    provider, _ = _provider(monkeypatch, max_retries=2)
    assert provider.extract_resume_information("hi") == {"skills": ["Python"]}
    assert calls["n"] == 2


def test_timeout_exhaustion_raises_timeout_category(monkeypatch):
    calls = _script_post(monkeypatch, [httpx.TimeoutException("slow")])
    provider, _ = _provider(monkeypatch, max_retries=2)
    with pytest.raises(AIRequestError) as excinfo:
        provider.extract_resume_information("hi")
    assert excinfo.value.category == "timeout"
    assert calls["n"] == 3


def test_retry_count_is_bounded(monkeypatch):
    """A permanently throttled provider must not be hammered."""
    calls = _script_post(monkeypatch, [503])
    provider, _ = _provider(monkeypatch, max_retries=2)
    with pytest.raises(AIRequestError) as excinfo:
        provider.extract_resume_information("hi")
    assert excinfo.value.category == "provider_unavailable"
    assert calls["n"] == 3


def test_max_retries_zero_means_single_attempt(monkeypatch):
    calls = _script_post(monkeypatch, [429])
    provider, slept = _provider(monkeypatch, max_retries=0)
    with pytest.raises(AIRequestError):
        provider.extract_resume_information("hi")
    assert calls["n"] == 1
    assert slept == []


def test_backoff_is_exponential_and_capped(monkeypatch):
    _script_post(monkeypatch, [503])
    provider, slept = _provider(monkeypatch, max_retries=5)
    with pytest.raises(AIRequestError):
        provider.extract_resume_information("hi")
    # base 0.5 doubling to the 4.0 cap: 0.5, 1.0, 2.0, 4.0, 4.0
    assert slept == [0.5, 1.0, 2.0, 4.0, 4.0]
    assert sum(slept) == pytest.approx(11.5)


def test_retry_loop_cannot_sleep_when_delays_disabled(monkeypatch):
    calls = _script_post(monkeypatch, [429, 200])
    provider = OpenAICompatibleProvider(
        api_key="sk-test",
        max_retries=2,
        retry_base_delay=0.0,
        retry_max_delay=0.0,
        sleep=lambda _: pytest.fail("should not sleep with zero delay"),
    )
    assert provider.extract_resume_information("hi") == {"skills": ["Python"]}
    assert calls["n"] == 2


def test_provider_clamps_absurd_retry_settings(monkeypatch):
    """A misconfigured environment cannot create an unbounded loop."""
    provider = OpenAICompatibleProvider(
        api_key="sk-test", max_retries=10_000, retry_base_delay=10_000.0
    )
    assert provider._max_retries == 5
    assert provider._retry_base_delay == 10_000.0
    assert provider._backoff_delay(1) == provider._retry_max_delay


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def test_retry_defaults_are_bounded():
    cfg = Settings(ENVIRONMENT="development", JWT_SECRET="k" * 64, _env_file=None)
    assert cfg.AI_MAX_RETRIES == 2
    assert cfg.AI_RETRY_BASE_DELAY_SECONDS == 0.5
    assert cfg.AI_RETRY_MAX_DELAY_SECONDS == 4.0


def test_retry_settings_are_clamped():
    cfg = Settings(
        ENVIRONMENT="development",
        JWT_SECRET="k" * 64,
        AI_MAX_RETRIES=99,
        AI_RETRY_BASE_DELAY_SECONDS=-5,
        _env_file=None,
    )
    assert cfg.AI_MAX_RETRIES == 5
    assert cfg.AI_RETRY_BASE_DELAY_SECONDS == 0.0
    assert cfg.AI_RETRY_MAX_DELAY_SECONDS == 4.0


def test_get_ai_provider_passes_retry_settings(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "AI_API_KEY", "AIza-test")
    monkeypatch.setattr(settings, "AI_MAX_RETRIES", 3)
    monkeypatch.setattr(settings, "AI_RETRY_BASE_DELAY_SECONDS", 0.25)
    provider = get_ai_provider()
    assert provider._max_retries == 3
    assert provider._retry_base_delay == 0.25


# ---------------------------------------------------------------------------
# Graceful degradation: the pipeline still falls back after retries fail
# ---------------------------------------------------------------------------


def test_pipeline_recovers_when_provider_recovers(monkeypatch):
    """The real-world scenario: a 429 on the first call, success on the retry.
    The upload must be ai_analyzed, not ai_failed."""
    from tests.conftest import TestingSessionLocal, client
    from tests.test_ai_resume_pipeline import auth_headers, login_user, register_user
    from tests.test_resume import DOCX_CT, make_docx

    _script_post(monkeypatch, [429, 200])
    provider, _ = _provider(monkeypatch, max_retries=2)
    monkeypatch.setattr(
        "app.services.ai.provider.get_ai_provider", lambda: provider
    )

    register_user(email="retry.recovers@example.com")
    token = login_user(email="retry.recovers@example.com").json()["access_token"]
    response = client.post(
        "/api/resume/upload",
        files={"file": ("retry.docx", make_docx(), DOCX_CT)},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    assert response.json()["analysis_status"] == "ai_analyzed"

    from app.models.resume import Resume
    from app.models.user import User

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "retry.recovers@example.com").first()
        assert db.query(Resume).filter(Resume.user_id == user.id).first() is not None
    finally:
        db.close()


def test_pipeline_falls_back_gracefully_when_retries_exhausted(monkeypatch):
    """Exhausted retries must behave exactly like any other provider failure:
    201, ai_failed, deterministic data intact."""
    from tests.conftest import client
    from tests.test_ai_resume_pipeline import auth_headers, login_user, register_user
    from tests.test_resume import DOCX_CT, make_docx

    _script_post(monkeypatch, [503])
    provider, _ = _provider(monkeypatch, max_retries=2)
    monkeypatch.setattr(
        "app.services.ai.provider.get_ai_provider", lambda: provider
    )

    register_user(email="retry.exhausted@example.com")
    token = login_user(email="retry.exhausted@example.com").json()["access_token"]
    response = client.post(
        "/api/resume/upload",
        files={"file": ("retry.docx", make_docx(), DOCX_CT)},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["analysis_status"] == "ai_failed"
    assert "Python" in [s["name"] for s in body["skills"]]


def test_upload_never_leaks_key_after_retries(monkeypatch):
    """Retry logs and errors must not surface the key."""
    from tests.conftest import client
    from tests.test_ai_resume_pipeline import auth_headers, login_user, register_user
    from tests.test_resume import DOCX_CT, make_docx

    _script_post(monkeypatch, [429])
    provider, _ = _provider(monkeypatch, max_retries=1)
    provider._api_key = "sk-super-secret-value"
    monkeypatch.setattr(
        "app.services.ai.provider.get_ai_provider", lambda: provider
    )

    register_user(email="retry.noleak@example.com")
    token = login_user(email="retry.noleak@example.com").json()["access_token"]
    response = client.post(
        "/api/resume/upload",
        files={"file": ("retry.docx", make_docx(), DOCX_CT)},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    assert "sk-super-secret-value" not in response.text


def test_retry_applies_to_career_insights_path(monkeypatch):
    """The shared _chat call means insights get the same resilience."""
    _script_post(monkeypatch, [429, 200])
    provider, _ = _provider(monkeypatch, max_retries=2)
    result = provider.generate_career_insights([{"role": "user", "content": "hi"}])
    assert result == {"skills": ["Python"]}


def test_mock_provider_is_unchanged():
    provider = MockAIProvider(response={"skills": []})
    assert provider.extract_resume_information("x") == {"skills": []}