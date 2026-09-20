"""Tests for GET /api/career-insights (Phase 7).

Isolation strategy: the whole suite shares one in-memory SQLite database, and
career insights aggregate across ALL active jobs. So every test seeds a resume
whose skills are unique tokens that can only match the jobs that test creates
(matching requires an exact, normalized skill-name overlap). This keeps every
count/order assertion deterministic regardless of what other tests have seeded.

AI provider is always MockAIProvider (or None / raising) — never a real key.
"""

from tests.conftest import TestingSessionLocal, client
from tests.test_jobs_api import _add_job

from app.models.resume import Resume, Skill
from app.services.ai.base import AIConfigurationError, AIRequestError
from app.services.ai.provider import MockAIProvider


def register_user(email):
    return client.post(
        "/api/auth/register",
        json={"name": "Insights Tester", "email": email, "password": "secret123"},
    )


def login_user(email):
    return client.post("/api/auth/login", json={"email": email, "password": "secret123"})


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_resume(user_id, skills):
    """Insert a resume directly into the shared test database."""
    db = TestingSessionLocal()
    try:
        resume = Resume(user_id=user_id, file_name="resume.pdf", raw_text="x")
        db.add(resume)
        db.flush()
        for name in skills:
            db.add(Skill(resume_id=resume.id, name=name))
        db.commit()
        db.refresh(resume)
        return resume.id
    finally:
        db.close()


def add_skills_job(source, external_id, title, skills):
    """Add an active job that only requires skills (no qualifications)."""
    return _add_job(
        source,
        external_id,
        title=title,
        skills=skills,
        qualifications=set(),
        minimum_experience_years=None,
        maximum_experience_years=None,
    )


def login_and_return_token(email):
    return login_user(email).json()["access_token"]


def patch_provider(monkeypatch, response=None, error=None):
    fake = MockAIProvider(response=response, error=error)
    monkeypatch.setattr("app.services.ai.provider.get_ai_provider", lambda: fake)
    return fake


def no_provider(monkeypatch):
    monkeypatch.setattr("app.services.ai.provider.get_ai_provider", lambda: None)


def raising_provider(monkeypatch, exc):
    def _raise():
        raise exc

    monkeypatch.setattr("app.services.ai.provider.get_ai_provider", _raise)


# ---------------------------------------------------------------------------
# Auth / resume state
# ---------------------------------------------------------------------------


def test_insights_requires_auth():
    response = client.get("/api/career-insights")
    assert response.status_code == 401


def test_insights_without_resume_returns_404():
    register_user(email="ci.noresume@example.com")
    token = login_and_return_token("ci.noresume@example.com")
    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 404
    assert "resume" in response.json()["detail"].lower()


def test_authentication_isolation():
    register_user(email="ci.alice@example.com")
    alice_token = login_and_return_token("ci.alice@example.com")
    alice_id = client.get("/api/auth/me", headers=auth_headers(alice_token)).json()["id"]
    create_resume(alice_id, skills=["ci-isoa", "ci-isob"])

    register_user(email="ci.bob@example.com")
    bob_token = login_and_return_token("ci.bob@example.com")

    add_skills_job("ci-isolation", "iso-1", "Data Analyst", {"ci-isoa", "ci-isob", "ci-isog"})

    alice = client.get("/api/career-insights", headers=auth_headers(alice_token))
    assert alice.status_code == 200
    alice_skills = {s["skill"] for s in alice.json()["strengths"]}
    assert "ci-isoa" in alice_skills or "ci-isob" in alice_skills

    bob = client.get("/api/career-insights", headers=auth_headers(bob_token))
    assert bob.status_code == 404


# ---------------------------------------------------------------------------
# Deterministic career analysis
# ---------------------------------------------------------------------------


def test_resume_with_no_skills_surfaces_demand():
    register_user(email="ci.noskills@example.com")
    token = login_and_return_token("ci.noskills@example.com")
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]
    create_resume(user_id, skills=[])

    add_skills_job("ci-noskills", "ns-1", "t3role-a", {"ci-ns-a", "ci-ns-b"})
    add_skills_job("ci-noskills", "ns-2", "t3role-b", {"ci-ns-b", "ci-ns-c"})

    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["strengths"] == []
    assert body["relevant_job_count"] >= 2
    gap_names = {g["skill"] for g in body["skill_gaps"]}
    assert "ci-ns-c" in gap_names
    titles = {d["title"] for d in body["career_directions"]}
    assert "t3role-a" in titles


def test_resume_with_skills_builds_strengths_gaps_and_directions():
    register_user(email="ci.skills@example.com")
    token = login_and_return_token("ci.skills@example.com")
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]
    create_resume(user_id, skills=["t4a", "t4b", "t4c"])

    add_skills_job("ci-skills", "sk-1", "Data Analyst", {"t4a", "t4b", "t4g1"})
    add_skills_job("ci-skills", "sk-2", "Data Analyst", {"t4c", "t4b", "t4g2"})
    add_skills_job("ci-skills", "sk-3", "BI Analyst", {"t4g1", "t4b"})

    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["has_resume"] is True

    strengths = {s["skill"]: s["relevance_count"] for s in body["strengths"]}
    assert strengths == {"t4a": 1, "t4b": 3, "t4c": 1}

    gaps = {g["skill"]: g for g in body["skill_gaps"]}
    assert gaps["t4g1"]["relevance_count"] == 2
    assert body["skill_gaps"][0]["skill"] == "t4g1"

    directions = {d["title"]: d for d in body["career_directions"]}
    assert directions["Data Analyst"]["matching_job_count"] == 2
    assert directions["Data Analyst"]["average_match"] == 66.67
    assert "t4b" in directions["Data Analyst"]["supporting_skills"]
    assert "t4g1" in directions["Data Analyst"]["missing_skills"]
    assert directions["BI Analyst"]["matching_job_count"] == 1


def test_skill_normalization_deduplicates_case_and_space():
    register_user(email="ci.norm@example.com")
    token = login_and_return_token("ci.norm@example.com")
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]
    create_resume(user_id, skills=["t5x", "t5x", " T5X "])

    add_skills_job("ci-norm", "n-1", "Developer", {"t5x"})

    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["profile_summary"]["skills"] == ["t5x"]
    assert len(body["strengths"]) == 1
    assert body["strengths"][0]["skill"] == "t5x"
    assert body["strengths"][0]["relevance_count"] == 1


def test_duplicate_user_skills_count_job_once():
    register_user(email="ci.dup@example.com")
    token = login_and_return_token("ci.dup@example.com")
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]
    create_resume(user_id, skills=["t6a", "t6b", "t6b", "t6a"])

    add_skills_job("ci-dup", "d-1", "Analyst", {"t6a", "t6b"})
    add_skills_job("ci-dup", "d-2", "Engineer", {"t6a", "t6b"})

    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 200
    strengths = {s["skill"]: s["relevance_count"] for s in response.json()["strengths"]}
    assert strengths == {"t6a": 2, "t6b": 2}


def test_skill_gap_detection_counts_relevant_jobs():
    register_user(email="ci.gap@example.com")
    token = login_and_return_token("ci.gap@example.com")
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]
    create_resume(user_id, skills=["t7a"])

    add_skills_job("ci-gap", "g-1", "Data Analyst", {"t7a", "t7g"})

    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 200
    gaps = {g["skill"]: g for g in response.json()["skill_gaps"]}
    assert gaps["t7g"]["relevance_count"] == 1
    assert "1 of 1 relevant jobs" in gaps["t7g"]["why_it_matters"]


def test_skill_gap_frequency_orders_priority():
    register_user(email="ci.freq@example.com")
    token = login_and_return_token("ci.freq@example.com")
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]
    create_resume(user_id, skills=["t8a", "t8b"])

    add_skills_job("ci-freq", "f-1", "Analyst", {"t8a", "t8g"})
    add_skills_job("ci-freq", "f-2", "Analyst", {"t8b", "t8g"})
    add_skills_job("ci-freq", "f-3", "Analyst", {"t8a", "t8h"})

    response = client.get("/api/career-insights", headers=auth_headers(token))
    body = response.json()
    assert body["skill_gaps"][0]["skill"] == "t8g"
    assert body["skill_gaps"][0]["priority"] == "high"
    gaps = {g["skill"]: g for g in body["skill_gaps"]}
    assert gaps["t8g"]["priority"] == "high"
    assert gaps["t8g"]["relevance_count"] == 2
    assert gaps["t8h"]["priority"] == "medium"
    assert gaps["t8h"]["relevance_count"] == 1


def test_relevant_job_fetch_and_analysis_bounds():
    register_user(email="ci.bounds@example.com")
    token = login_and_return_token("ci.bounds@example.com")
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]
    create_resume(user_id, skills=["tBo"])

    for i in range(35):
        add_skills_job("ci-bounds", f"b-{i}", "Developer", {"tBo"})

    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["fetched_job_count"] == 30
    assert body["relevant_job_count"] <= 20


def test_deterministic_analysis_with_ai_disabled(monkeypatch):
    no_provider(monkeypatch)
    register_user(email="ci.det@example.com")
    token = login_and_return_token("ci.det@example.com")
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]
    create_resume(user_id, skills=["tDa", "tDb"])

    add_skills_job("ci-det", "det-1", "Data Analyst", {"tDa", "tDb"})

    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["ai_insights"]["status"] == "disabled"
    strengths = {s["skill"]: s["relevance_count"] for s in body["strengths"]}
    assert strengths == {"tDa": 1, "tDb": 1}
    assert body["ai_insights"]["summary"] == ""


def test_no_relevant_jobs_is_graceful(monkeypatch):
    no_provider(monkeypatch)
    register_user(email="ci.empty@example.com")
    token = login_and_return_token("ci.empty@example.com")
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]
    create_resume(user_id, skills=["tNa", "tNb"])

    add_skills_job("ci-unrelated", "u-1", "Data Analyst", {"tNg1", "tNg2"})

    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["strengths"] == []
    assert body["skill_gaps"] == []
    assert body["career_directions"] == []
    assert any("job data" in line for line in body["action_plan"])


def test_empty_job_dataset_is_graceful(monkeypatch):
    no_provider(monkeypatch)
    monkeypatch.setattr(
        "app.services.career_insights_service.search_jobs", lambda db, **kw: (0, [])
    )
    register_user(email="ci.nojobs@example.com")
    token = login_and_return_token("ci.nojobs@example.com")
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]
    create_resume(user_id, skills=["tE"])

    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["fetched_job_count"] == 0
    assert body["relevant_job_count"] == 0
    assert body["strengths"] == []
    assert body["skill_gaps"] == []
    assert body["career_directions"] == []
    assert body["ai_insights"]["status"] in {"disabled", "failed"}


# ---------------------------------------------------------------------------
# AI career insights
# ---------------------------------------------------------------------------


def _ai_user_with_resume_and_job(email, source, external_id):
    """Create a user with tokens {tAa, tAb} and one relevant job requiring
    {tAa, tAb} plus gap token tAg (the AI-allowed skill vocabulary)."""
    register_user(email=email)
    token = login_and_return_token(email)
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]
    create_resume(user_id, skills=["tAa", "tAb"])
    add_skills_job(source, external_id, "Data Analyst", {"tAa", "tAb", "tAg"})
    return token


def test_ai_success_returns_status_available(monkeypatch):
    patch_provider(
        monkeypatch,
        response={
            "summary": "Your strongest area is data analysis and reporting.",
            "career_directions": [
                {
                    "title": "Data Analyst",
                    "reason": "You already match several required skills.",
                    "next_steps": ["Try a portfolio dashboard project."],
                }
            ],
            "skill_development": [
                {"skill": "tAg", "reason": "Required across relevant jobs.", "priority": "high"}
            ],
            "resume_suggestions": ["Add measurable project outcomes."],
            "action_plan": ["Build a dashboard project using your strengths."],
        },
    )
    token = _ai_user_with_resume_and_job("ci.aiok@example.com", "ci-ai-ok", "ai-ok")

    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 200
    ai = response.json()["ai_insights"]
    assert ai["status"] == "available"
    assert "data analysis" in ai["summary"]
    assert ai["career_directions"][0]["title"] == "Data Analyst"
    assert ai["skill_development"][0]["skill"] == "tAg"
    assert ai["skill_development"][0]["priority"] == "high"
    assert ai["resume_suggestions"]
    assert ai["action_plan"]


def test_ai_failure_falls_back_to_deterministic(monkeypatch):
    patch_provider(
        monkeypatch,
        error=AIRequestError("provider down", category="provider_unavailable"),
    )
    token = _ai_user_with_resume_and_job("ci.aifail@example.com", "ci-ai-fail", "ai-fail")

    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["ai_insights"]["status"] == "failed"
    assert body["strengths"] or body["skill_gaps"]
    assert body["career_directions"]


def test_ai_configuration_error_is_failure(monkeypatch):
    raising_provider(monkeypatch, AIConfigurationError("missing key"))
    token = _ai_user_with_resume_and_job("ci.aicfg@example.com", "ci-ai-cfg", "ai-cfg")

    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["ai_insights"]["status"] == "failed"


def test_invalid_ai_response_is_failure(monkeypatch):
    patch_provider(monkeypatch, response={"summary": 12345, "skill_development": "nope"})
    token = _ai_user_with_resume_and_job("ci.aiinvalid@example.com", "ci-ai-inv", "ai-inv")

    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["ai_insights"]["status"] == "failed"


def test_ai_invalid_priority_is_failure(monkeypatch):
    patch_provider(
        monkeypatch,
        response={
            "summary": "ok",
            "skill_development": [{"skill": "tAg", "priority": "urgent"}],
        },
    )
    token = _ai_user_with_resume_and_job("ci.aiprio@example.com", "ci-ai-prio", "ai-prio")

    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["ai_insights"]["status"] == "failed"


def test_ai_unknown_skill_rejected_from_vocabulary(monkeypatch):
    patch_provider(
        monkeypatch,
        response={
            "summary": "Keep building on your data skills.",
            "skill_development": [
                {"skill": "tAg", "reason": "In demand.", "priority": "high"},
                {"skill": "Golang", "reason": "Not in your profile.", "priority": "low"},
            ],
        },
    )
    token = _ai_user_with_resume_and_job("ci.aibad@example.com", "ci-ai-bad", "ai-bad")

    response = client.get("/api/career-insights", headers=auth_headers(token))
    assert response.status_code == 200
    ai = response.json()["ai_insights"]
    assert ai["status"] == "available"
    skills = [item["skill"] for item in ai["skill_development"]]
    assert skills == ["tAg"]
    assert "Golang" not in skills