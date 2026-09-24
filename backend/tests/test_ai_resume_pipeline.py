"""Tests for the AI resume-intelligence pipeline (Phase 3).

Uses the mocked AI provider (no real API key needed) and verifies: structured
extraction persistence, deduplication, deterministic total-experience, graceful
fallback to deterministic parsing on every AI failure mode, the retry endpoint,
privacy (no secrets/large text in responses), and that AI-extracted experience
now flows into the matching engine.
"""

import httpx
import pytest
from pydantic import ValidationError

from tests.conftest import TestingSessionLocal, client
from tests.test_jobs_api import _add_job
from tests.test_resume import DOCX_CT, make_docx

from app.core.config import Settings, settings
from app.models.resume import Experience, Resume, Skill
from app.models.user import User
from app.services.ai.base import AIConfigurationError, AIRequestError
from app.services.ai.pipeline import run_resume_analysis, structured_to_persist
from app.services.ai.provider import (
    GEMINI_DEFAULT_MODEL,
    PROVIDER_GEMINI_BASE_URL,
    MockAIProvider,
    OpenAICompatibleProvider,
    get_ai_provider,
    parse_json_payload,
)
from app.services.ai.schemas import AIResumeExtraction
from app.services.experience_duration import calculate_total_experience_years

VALID_EXTRACTION = {
    "skills": ["Python", "SQL", "Pandas", "Python", "Excel", "Power BI"],
    "education": [
        {
            "institution": "University of Ottawa",
            "degree": "Bachelor of Science",
            "field_of_study": "Computer Science",
            "start_year": 2015,
            "end_year": 2019,
        }
    ],
    "certifications": [
        {
            "name": "AWS Certified Solutions Architect",
            "issuer": "Amazon Web Services",
            "issue_year": 2019,
            "expiry_year": 2024,
        }
    ],
    "experience": [
        {
            "company": "Acme Inc.",
            "job_title": "Data Analyst",
            "description": "Analyzed sales data",
            "location": "Ottawa",
            "start_date": "2024-01",
            "end_date": None,
            "currently_employed": True,
        },
        {
            "company": "Old Corp",
            "job_title": "Junior Analyst",
            "description": "Reports",
            "location": None,
            "start_date": "2022-06",
            "end_date": "2023-06",
            "currently_employed": False,
        },
    ],
}


def register_user(email):
    return client.post(
        "/api/auth/register",
        json={"name": "AI Tester", "email": email, "password": "secret123"},
    )


def login_user(email):
    return client.post("/api/auth/login", json={"email": email, "password": "secret123"})


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def upload_docx(token, text=None):
    return client.post(
        "/api/resume/upload",
        files={"file": ("ai.docx", make_docx() if text is None else make_docx(text), DOCX_CT)},
        headers=auth_headers(token),
    )


def patch_provider(monkeypatch, response=None, error=None):
    fake = MockAIProvider(response=response, error=error)
    monkeypatch.setattr(
        "app.services.ai.provider.get_ai_provider", lambda: fake
    )
    return fake


def no_provider(monkeypatch):
    monkeypatch.setattr("app.services.ai.provider.get_ai_provider", lambda: None)


# ---------------------------------------------------------------------------
# Pipeline unit tests
# ---------------------------------------------------------------------------


def test_run_resume_analysis_returns_parsed_when_ai_disabled(monkeypatch):
    no_provider(monkeypatch)
    structured, status = run_resume_analysis("some resume text")
    assert structured is None
    assert status == "parsed"


def test_run_resume_analysis_empty_text(
    monkeypatch,
):
    patch_provider(monkeypatch, response=VALID_EXTRACTION)
    structured, status = run_resume_analysis("")
    assert structured is None
    assert status == "ai_failed"


def test_run_resume_analysis_valid_extraction(monkeypatch):
    patch_provider(monkeypatch, response=VALID_EXTRACTION)
    structured, status = run_resume_analysis("some resume text")
    assert status == "ai_analyzed"
    assert structured is not None
    assert structured["skills"] == ["Python", "SQL", "Pandas", "Excel", "Power BI"]
    assert structured["education"][0]["start_year"] == 2015
    assert structured["experience"][-1]["start_date"] == "2022-06"
    assert structured["total_experience_years"] == calculate_total_experience_years(
        structured["experience"]
    )


def test_run_resume_analysis_provider_error_falls_back(monkeypatch):
    patch_provider(
        monkeypatch,
        error=AIRequestError("boom", category="provider_error"),
    )
    structured, status = run_resume_analysis("some resume text")
    assert structured is None
    assert status == "ai_failed"


def test_run_resume_analysis_validation_error_falls_back(monkeypatch):
    patch_provider(monkeypatch, response={"skills": "Python", "experience": "oops"})
    structured, status = run_resume_analysis("some resume text")
    assert structured is None
    assert status == "ai_failed"


def test_run_resume_analysis_empty_payload_is_valid_empty(monkeypatch):
    patch_provider(monkeypatch, response={})
    structured, status = run_resume_analysis("some resume text")
    assert status == "ai_analyzed"
    assert structured["skills"] == []
    assert structured["total_experience_years"] is None


def test_run_resume_analysis_null_institution_no_crash(monkeypatch):
    payload = {"education": [{"institution": None, "degree": None}]}
    patch_provider(monkeypatch, response=payload)
    structured, status = run_resume_analysis("some resume text")
    assert status == "ai_analyzed"
    assert structured["education"][0]["institution"] is None


def test_run_resume_analysis_invalid_date_falls_back(monkeypatch):
    payload = {
        "experience": [
            {
                "company": "A",
                "start_date": "not-a-date",
                "end_date": "2025-01",
                "currently_employed": False,
            }
        ]
    }
    patch_provider(monkeypatch, response=payload)
    structured, status = run_resume_analysis("some resume text")
    assert structured is None
    assert status == "ai_failed"


def test_run_resume_analysis_future_start_unknown_total(monkeypatch):
    payload = {
        "experience": [
            {
                "company": "A",
                "start_date": "2030-01",
                "end_date": "2031-01",
                "currently_employed": False,
            }
        ]
    }
    patch_provider(monkeypatch, response=payload)
    structured, status = run_resume_analysis("some resume text")
    assert status == "ai_analyzed"
    assert structured["experience"][0]["start_date"] == "2030-01"
    assert structured["total_experience_years"] is None


def test_structured_to_persist_deduplicates_skills():
    extraction = AIResumeExtraction.model_validate(
        {"skills": ["Python", "python", " PYTHON ", "SQL"], "education": []}
    )
    structured = structured_to_persist(extraction)
    assert structured["skills"] == ["Python", "SQL"]


def test_structured_to_persist_keeps_ai_spelling_for_display():
    extraction = AIResumeExtraction.model_validate(
        {"skills": ["Power BI"], "experience": [{"company": "ACME Inc."}]}
    )
    structured = structured_to_persist(extraction)
    assert structured["skills"] == ["Power BI"]
    assert structured["experience"][0]["company"] == "ACME Inc."
    assert structured["experience"][0]["currently_employed"] is False


# ---------------------------------------------------------------------------
# Provider unit tests
# ---------------------------------------------------------------------------


def test_get_ai_provider_none_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "")
    monkeypatch.setattr(settings, "AI_API_KEY", "")
    assert get_ai_provider() is None


def test_get_ai_provider_returns_gemini_provider(monkeypatch):
    """AI_PROVIDER=gemini must build an OpenAI-compatible provider pointed at
    Google's OpenAI-compatible chat-completions endpoint, resolving its own
    endpoint and model defaults when nothing is explicitly configured."""
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "AI_API_KEY", "AIza-test")
    monkeypatch.setattr(settings, "AI_MODEL", "")
    monkeypatch.setattr(settings, "AI_BASE_URL", "")
    provider = get_ai_provider()
    assert isinstance(provider, OpenAICompatibleProvider)
    # The provider constructor rstrips trailing slashes; the canonical Gemini
    # constant keeps the documented trailing slash, so compare normalized.
    assert provider._base_url == PROVIDER_GEMINI_BASE_URL.rstrip("/")
    # Pin the working default explicitly so reverting to a retired Gemini model
    # (e.g. gemini-1.5-flash) fails this test even if the constant is changed.
    assert provider._model == GEMINI_DEFAULT_MODEL == "gemini-3.6-flash"


def test_get_ai_provider_gemini_explicit_url_and_model_preserved(monkeypatch):
    """An explicit AI_BASE_URL/AI_MODEL must override the Gemini defaults."""
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "AI_API_KEY", "AIza-test")
    monkeypatch.setattr(settings, "AI_MODEL", "gemini-2.0-flash")
    monkeypatch.setattr(settings, "AI_BASE_URL", "https://custom.example/v1")
    provider = get_ai_provider()
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider._base_url == "https://custom.example/v1"
    assert provider._model == "gemini-2.0-flash"


def test_get_ai_provider_returns_openai_defaults(monkeypatch):
    """AI_PROVIDER=openai with empty AI_BASE_URL/AI_MODEL must resolve the
    OpenAI endpoint and the OpenAI default model."""
    monkeypatch.setattr(settings, "AI_PROVIDER", "openai")
    monkeypatch.setattr(settings, "AI_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "AI_MODEL", "")
    monkeypatch.setattr(settings, "AI_BASE_URL", "")
    provider = get_ai_provider()
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider._base_url == "https://api.openai.com/v1"
    assert provider._model == "gpt-4o-mini"


def test_get_ai_provider_openai_explicit_base_url_preserved(monkeypatch):
    """An explicit OpenAI-compatible AI_BASE_URL must be preserved."""
    monkeypatch.setattr(settings, "AI_PROVIDER", "openai")
    monkeypatch.setattr(settings, "AI_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "AI_MODEL", "my-model")
    monkeypatch.setattr(settings, "AI_BASE_URL", "https://proxy.example.com/v1")
    provider = get_ai_provider()
    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider._base_url == "https://proxy.example.com/v1"
    assert provider._model == "my-model"


def test_get_ai_provider_mock_returns_mock(monkeypatch):
    """AI_PROVIDER=mock must return the deterministic MockAIProvider with no
    API key required."""
    monkeypatch.setattr(settings, "AI_PROVIDER", "mock")
    monkeypatch.setattr(settings, "AI_API_KEY", "")
    provider = get_ai_provider()
    assert isinstance(provider, MockAIProvider)


def test_get_ai_provider_missing_key_raises(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "openai")
    monkeypatch.setattr(settings, "AI_API_KEY", "")
    monkeypatch.setattr(settings, "AI_MODEL", "")
    monkeypatch.setattr(settings, "AI_BASE_URL", "")
    with pytest.raises(AIConfigurationError):
        get_ai_provider()


def test_get_ai_provider_unsupported_raises(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "claude")
    monkeypatch.setattr(settings, "AI_API_KEY", "sk-test")
    with pytest.raises(AIConfigurationError):
        get_ai_provider()


def test_parse_json_payload_cases():
    assert parse_json_payload('{"skills": ["a"]}') == {"skills": ["a"]}
    assert parse_json_payload('```json\n{"skills": ["a"]}\n```') == {
        "skills": ["a"]
    }
    with pytest.raises(Exception):
        parse_json_payload("")
    with pytest.raises(Exception):
        parse_json_payload("not json at all")
    with pytest.raises(Exception):
        parse_json_payload("[1, 2, 3]")
    with pytest.raises(Exception):
        parse_json_payload("__import__('os').system('echo pwned')")


def test_openai_timeout_maps_to_typed_error(monkeypatch):
    def _post(*args, **kwargs):
        raise httpx.TimeoutException("slow")

    monkeypatch.setattr("app.services.ai.provider.httpx.post", _post)
    provider = OpenAICompatibleProvider(api_key="sk-test")
    with pytest.raises(AIRequestError) as excinfo:
        provider.extract_resume_information("hi")
    assert excinfo.value.category == "timeout"


def test_openai_rate_limit_maps_to_typed_error(monkeypatch):
    class FakeResponse:
        status_code = 429

    monkeypatch.setattr(
        "app.services.ai.provider.httpx.post", lambda *a, **k: FakeResponse()
    )
    provider = OpenAICompatibleProvider(api_key="sk-test")
    with pytest.raises(AIRequestError) as excinfo:
        provider.extract_resume_information("hi")
    assert excinfo.value.category == "rate_limit"


def test_openai_malformed_success_body_maps_to_output_error(monkeypatch):
    class FakeResponse:
        status_code = 200

        def json(self):
            return {}

    monkeypatch.setattr(
        "app.services.ai.provider.httpx.post", lambda *a, **k: FakeResponse()
    )
    provider = OpenAICompatibleProvider(api_key="sk-test")
    with pytest.raises(Exception):
        provider.extract_resume_information("hi")


def test_config_ai_defaults_are_provider_agnostic():
    """AI_MODEL/AI_BASE_URL must default to empty so the provider factory (not a
    hardcoded OpenAI value in Settings) decides the endpoint/model. Without this,
    AI_PROVIDER=gemini accidentally inherits the OpenAI endpoint."""
    cfg = Settings(
        ENVIRONMENT="development",
        JWT_SECRET="k" * 64,
        _env_file=None,
    )
    assert cfg.AI_PROVIDER == ""
    assert cfg.AI_MODEL == ""
    assert cfg.AI_BASE_URL == ""


def test_config_invalid_provider_rejected():
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="development",
            JWT_SECRET="k" * 64,
            AI_PROVIDER="claude",
            AI_API_KEY="sk-test",
            _env_file=None,
        )


def test_config_production_requires_ai_key():
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET="k" * 64,
            AI_PROVIDER="openai",
            AI_API_KEY="",
            _env_file=None,
        )
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET="k" * 64,
            AI_PROVIDER="mock",
            AI_API_KEY="sk-test",
            _env_file=None,
        )
    ok = Settings(
        ENVIRONMENT="production",
        JWT_SECRET="k" * 64,
        AI_PROVIDER="openai",
        AI_API_KEY="sk-test",
        _env_file=None,
    )
    assert ok.AI_PROVIDER == "openai"


# ---------------------------------------------------------------------------
# Upload / analyze endpoint integration tests
# ---------------------------------------------------------------------------


def test_upload_with_ai_extraction_persisted(monkeypatch):
    register_user(email="ai.full@example.com")
    token = login_user(email="ai.full@example.com").json()["access_token"]
    patch_provider(monkeypatch, response=VALID_EXTRACTION)

    response = upload_docx(token)
    assert response.status_code == 201
    data = response.json()
    assert data["analysis_status"] == "ai_analyzed"
    assert data["total_experience_years"] == calculate_total_experience_years(
        (VALID_EXTRACTION["experience"])
    )

    skill_names = [skill["name"] for skill in data["skills"]]
    assert skill_names == ["Python", "SQL", "Pandas", "Excel", "Power BI"]

    assert data["education"][0]["institution"] == "University of Ottawa"
    assert data["education"][0]["start_year"] == 2015
    assert data["education"][0]["end_year"] == 2019

    assert data["certifications"][0]["name"] == "AWS Certified Solutions Architect"
    assert data["certifications"][0]["issue_year"] == 2019

    role = [e for e in data["experience"] if e["company"] == "Acme Inc."][0]
    assert role["location"] == "Ottawa"
    assert role["start_date"] == "2024-01"
    assert role["end_date"] is None
    assert role["currently_employed"] is True

    role = [e for e in data["experience"] if e["company"] == "Old Corp"][0]
    assert role["start_date"] == "2022-06"
    assert role["end_date"] == "2023-06"
    assert role["currently_employed"] is False


def test_upload_deterministic_when_ai_disabled(monkeypatch):
    register_user(email="ai.off@example.com")
    token = login_user(email="ai.off@example.com").json()["access_token"]
    no_provider(monkeypatch)

    response = upload_docx(token)
    assert response.status_code == 201
    data = response.json()
    assert data["analysis_status"] == "parsed"
    assert data["total_experience_years"] is None
    assert data["experience"][0]["start_date"] is None
    skill_names = [skill["name"] for skill in data["skills"]]
    assert "Python" in skill_names  # deterministic parse still extracts


def test_ai_failure_falls_back_to_deterministic(monkeypatch):
    register_user(email="ai.fail@example.com")
    token = login_user(email="ai.fail@example.com").json()["access_token"]
    patch_provider(monkeypatch, error=AIRequestError("nope", category="provider_error"))

    response = upload_docx(token)
    assert response.status_code == 201
    data = response.json()
    assert data["analysis_status"] == "ai_failed"
    assert data["total_experience_years"] is None
    skill_names = [skill["name"] for skill in data["skills"]]
    assert "Python" in skill_names


def test_ai_rate_limit_falls_back_to_useful_skills(monkeypatch):
    """The exact 429 scenario from production logs: the provider raises a
    rate_limit AIRequestError. The endpoint must stay successful, stay
    ai_failed, and still extract useful per-line skills through the fallback —
    not degrade to an empty/poor profile."""
    register_user(email="ai.rl@example.com")
    token = login_user(email="ai.rl@example.com").json()["access_token"]
    patch_provider(
        monkeypatch,
        error=AIRequestError("rate limit exceeded", category="rate_limit"),
    )

    text = """Technical Skills
Python
SQL
Pandas
Power BI
Excel

Education
BS Economics and Data Science
"""
    response = upload_docx(token, text=text)
    assert response.status_code == 201
    data = response.json()
    assert data["analysis_status"] == "ai_failed"
    skill_names = [skill["name"] for skill in data["skills"]]
    assert skill_names == ["Python", "SQL", "Pandas", "Power BI", "Excel"]
    assert data["education"][0]["degree"] == "BS"
    assert data["education"][0]["field_of_study"] == "Economics and Data Science"


def test_deterministic_and_ai_shapes_share_canonical_schema(monkeypatch):
    """AI output and deterministic fallback must persist through the SAME
    canonical structure. Verify both builders emit the same persistence key
    sets for every resume section so the two paths are interchangeable."""
    from app.services.resume_parser import parse_resume
    from tests.test_resume import make_docx

    patch_provider(monkeypatch, response=VALID_EXTRACTION)
    ai_structured = structured_to_persist(
        AIResumeExtraction.model_validate(VALID_EXTRACTION)
    )
    deterministic = parse_resume(make_docx(), "r.docx", DOCX_CT)

    EDUCATION_KEYS = {"institution", "degree", "field_of_study", "start_year", "end_year"}
    EXPERIENCE_KEYS = {
        "company", "title", "description", "location",
        "start_date", "end_date", "currently_employed",
    }
    CERTIFICATION_KEYS = {"name", "issuer", "issue_year", "expiry_year"}

    assert {"skills", "education", "experience", "certifications"} <= set(ai_structured)
    assert {"skills", "education", "experience", "certifications"} <= set(deterministic)

    assert set(ai_structured["education"][0]) == EDUCATION_KEYS
    assert set(deterministic["education"][0]) == EDUCATION_KEYS
    assert set(ai_structured["experience"][0]) == EXPERIENCE_KEYS
    assert set(deterministic["experience"][0]) == EXPERIENCE_KEYS
    assert set(ai_structured["certifications"][0]) == CERTIFICATION_KEYS
    assert set(deterministic["certifications"][0]) == CERTIFICATION_KEYS


def test_ai_validation_failure_falls_back(monkeypatch):
    register_user(email="ai.badschema@example.com")
    token = login_user(email="ai.badschema@example.com").json()["access_token"]
    patch_provider(monkeypatch, response={"skills": 42, "experience": "nope"})

    response = upload_docx(token)
    assert response.status_code == 201
    assert response.json()["analysis_status"] == "ai_failed"


def test_upload_response_never_leaks_secrets(monkeypatch):
    register_user(email="ai.leak@example.com")
    token = login_user(email="ai.leak@example.com").json()["access_token"]
    patch_provider(
        monkeypatch,
        error=AIRequestError("sk-super-secret-key leaked in message", category="provider_error"),
    )

    response = upload_docx(token)
    assert response.status_code == 201
    assert "sk-super-secret-key" not in response.text


def test_analyze_retry_succeeds_after_disabled_upload(monkeypatch):
    register_user(email="ai.retry@example.com")
    token = login_user(email="ai.retry@example.com").json()["access_token"]
    no_provider(monkeypatch)
    assert upload_docx(token).json()["analysis_status"] == "parsed"

    patch_provider(monkeypatch, response=VALID_EXTRACTION)
    response = client.post("/api/resume/analyze", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_status"] == "ai_analyzed"
    assert data["total_experience_years"] == calculate_total_experience_years(
        VALID_EXTRACTION["experience"]
    )
    assert "Power BI" in [skill["name"] for skill in data["skills"]]


def test_analyze_retry_failure_preserves_existing_data(monkeypatch):
    register_user(email="ai.retryfail@example.com")
    token = login_user(email="ai.retryfail@example.com").json()["access_token"]
    patch_provider(monkeypatch, response=VALID_EXTRACTION)
    first = upload_docx(token).json()
    assert first["analysis_status"] == "ai_analyzed"
    assert first["total_experience_years"] is not None

    patch_provider(monkeypatch, error=AIRequestError("still down", category="provider_error"))
    response = client.post("/api/resume/analyze", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_status"] == "ai_failed"
    assert data["total_experience_years"] == first["total_experience_years"]
    assert data["experience"] == first["experience"]


def test_analyze_requires_auth():
    response = client.post("/api/resume/analyze")
    assert response.status_code == 401


def test_analyze_without_resume_404():
    register_user(email="ai.noshow@example.com")
    token = login_user(email="ai.noshow@example.com").json()["access_token"]
    response = client.post("/api/resume/analyze", headers=auth_headers(token))
    assert response.status_code == 404
    assert "resume" in response.json()["detail"].lower()


def test_analysis_is_own_resume_scoped():
    register_user(email="ai.owner@example.com")
    owner = login_user(email="ai.owner@example.com").json()["access_token"]
    register_user(email="ai.intruder@example.com")
    intruder = login_user(email="ai.intruder@example.com").json()["access_token"]

    client.post(
        "/api/resume/upload",
        files={"file": ("o.docx", make_docx(), DOCX_CT)},
        headers=auth_headers(owner),
    )

    assert (
        client.get("/api/resume/analysis", headers=auth_headers(intruder)).status_code
        == 404
    )
    assert (
        client.post("/api/resume/analyze", headers=auth_headers(intruder)).status_code
        == 404
    )


def test_null_education_fields_are_persisted_safely(monkeypatch):
    register_user(email="ai.elleducation@example.com")
    token = login_user(email="ai.elleducation@example.com").json()["access_token"]
    patch_provider(
        monkeypatch,
        response={
            "skills": [],
            "education": [{"institution": None, "degree": None, "field_of_study": None}],
        },
    )
    response = upload_docx(token)
    assert response.status_code == 201
    assert response.json()["analysis_status"] == "ai_analyzed"
    assert response.json()["education"][0]["institution"] is None


# ---------------------------------------------------------------------------
# Matching engine integration: AI-extracted experience is now scored
# ---------------------------------------------------------------------------


def test_match_uses_ai_extracted_experience_and_skills(monkeypatch):
    register_user(email="ai.match@example.com")
    token = login_user(email="ai.match@example.com").json()["access_token"]
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]

    patch_provider(monkeypatch, response=VALID_EXTRACTION)
    upload_response = upload_docx(token)
    assert upload_response.status_code == 201
    total_years = upload_response.json()["total_experience_years"]
    assert total_years is not None

    job_id = _add_job(
        "ai-match",
        "m-ai",
        skills={"Python", "SQL", "Excel"},
        qualifications={"Bachelor of Science"},
        minimum_experience_years=2,
        maximum_experience_years=5,
    )

    response = client.get(f"/api/jobs/{job_id}/match", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["skill_match_percentage"] == 100.0
    assert body["qualification_match_percentage"] == 100.0
    assert body["experience_match_percentage"] == 100.0
    assert body["experience_status"] == "meets_requirement"
    assert body["candidate_experience_years"] == total_years
    assert body["overall_match_percentage"] == 100.0
    assert body["component_weights"] == {
        "skill": 50,
        "qualification": 30,
        "experience": 20,
    }

    db = TestingSessionLocal()
    try:
        resume = (
            db.query(Resume).filter(Resume.user_id == user_id).first()
        )
        assert resume.total_experience_years == total_years
        dated = (
            db.query(Experience)
            .filter(Experience.resume_id == resume.id, Experience.start_date.isnot(None))
            .count()
        )
        assert dated == 2
    finally:
        db.close()


def test_ai_analyzed_resume_feeds_insights_and_matching(monkeypatch):
    """End-to-end Phase 7.2 chain: AI upload -> persisted children -> career
    insights (strengths/gaps/directions) and deterministic matching both consume
    the same stored resume data."""
    register_user(email="ai.e2e@example.com")
    token = login_user(email="ai.e2e@example.com").json()["access_token"]

    patch_provider(monkeypatch, response=VALID_EXTRACTION)
    response = upload_docx(token)
    assert response.status_code == 201
    assert response.json()["analysis_status"] == "ai_analyzed"

    job_id = _add_job(
        "ai-e2e",
        "e2e-1",
        title="Data Analyst",
        skills={"Python", "SQL", "Phase72MissingSkill"},
        qualifications={"Bachelor of Science"},
        minimum_experience_years=2,
        maximum_experience_years=8,
    )

    # Career Insights uses the AI-extracted skills as its source of truth.
    insights = client.get("/api/career-insights", headers=auth_headers(token))
    assert insights.status_code == 200
    body = insights.json()
    assert body["has_resume"] is True
    summary_skills = {s.lower() for s in body["profile_summary"]["skills"]}
    assert "python" in summary_skills
    assert "sql" in summary_skills
    strength_names = {s["skill"].lower() for s in body["strengths"]}
    assert "python" in strength_names
    gap_names = {g["skill"] for g in body["skill_gaps"]}
    assert "Phase72MissingSkill" in gap_names
    titles = {d["title"] for d in body["career_directions"]}
    assert any("Data Analyst" in t for t in titles)

    # Deterministic matching scores the AI-extracted skills (2 of 3 required).
    match = client.get(f"/api/jobs/{job_id}/match", headers=auth_headers(token))
    assert match.status_code == 200
    mbody = match.json()
    assert mbody["skill_match_percentage"] == 66.67
    assert "Python" in mbody["matched_skills"]
    assert "SQL" in mbody["matched_skills"]
    assert "Phase72MissingSkill" in mbody["missing_skills"]


def test_reanalysis_never_duplicates_child_rows(monkeypatch):
    """Re-running analysis (retry) replaces children instead of appending, so
    repeated retries never create duplicate skill/education/experience rows."""
    register_user(email="ai.nodup@example.com")
    token = login_user(email="ai.nodup@example.com").json()["access_token"]
    patch_provider(monkeypatch, response=VALID_EXTRACTION)

    first = upload_docx(token)
    assert first.status_code == 201
    first_skills = first.json()["skills"]
    assert len(first_skills) == 5  # "Python" duplicated in payload, deduped

    for _ in range(2):
        assert client.post("/api/resume/analyze", headers=auth_headers(token)).status_code == 200

    refreshed = client.get("/api/resume/analysis", headers=auth_headers(token)).json()
    assert refreshed["analysis_status"] == "ai_analyzed"
    assert [s["name"] for s in refreshed["skills"]] == [s["name"] for s in first_skills]
    assert len({s["id"] for s in refreshed["skills"]}) == len(first_skills)
    assert len(refreshed["education"]) == 1


def test_match_ai_pipeline_profile_carries_experience(monkeypatch):
    """build_candidate_profile now reads resume.total_experience_years."""
    from app.services.matching_service import build_candidate_profile

    db = TestingSessionLocal()
    try:
        user = User(
            name="Profile",
            email="ai.profile@example.com",
            hashed_password="x",
        )
        db.add(user)
        db.flush()
        resume = Resume(
            user_id=user.id,
            file_name="r.pdf",
            raw_text="x",
            total_experience_years=3.5,
            analysis_status="ai_analyzed",
        )
        db.add(resume)
        db.flush()
        db.add(Skill(resume_id=resume.id, name="Python"))
        db.commit()
        db.refresh(resume)

        profile = build_candidate_profile(resume)
        assert profile.experience_years == 3.5
        assert profile.skills == ["Python"]
    finally:
        db.close()