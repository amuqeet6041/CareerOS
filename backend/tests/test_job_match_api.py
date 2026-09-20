"""End-to-end tests for ``GET /api/jobs/{job_id}/match``.

Covers auth, missing job, missing resume, valid/complete matches, jobs with no
requirements, incomplete resumes, and own-resume isolation.
"""

from tests.conftest import TestingSessionLocal, client
from tests.test_jobs_api import _add_job

from app.models.resume import Education, Resume, Skill


def register_user(email):
    return client.post(
        "/api/auth/register",
        json={"name": "Match Tester", "email": email, "password": "secret123"},
    )


def login_user(email):
    return client.post("/api/auth/login", json={"email": email, "password": "secret123"})


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_resume(user_id, skills, education=None):
    """Insert a resume directly into the shared test database."""
    db = TestingSessionLocal()
    try:
        resume = Resume(user_id=user_id, file_name="resume.pdf", raw_text="x")
        db.add(resume)
        db.flush()
        for name in skills:
            db.add(Skill(resume_id=resume.id, name=name))
        for entry in education or []:
            db.add(
                Education(
                    resume_id=resume.id,
                    institution=entry.get("institution", "Test University"),
                    degree=entry.get("degree"),
                    field_of_study=entry.get("field_of_study"),
                )
            )
        db.commit()
        db.refresh(resume)
        return resume.id
    finally:
        db.close()


def test_match_requires_auth():
    response = client.get("/api/jobs/1/match")
    assert response.status_code == 401


def test_match_missing_job_returns_404():
    register_user(email="match.missing@example.com")
    token = login_user(email="match.missing@example.com").json()["access_token"]
    response = client.get(
        "/api/jobs/999999999/match", headers=auth_headers(token)
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_match_without_resume_returns_404():
    register_user(email="match.noresume@example.com")
    token = login_user(email="match.noresume@example.com").json()["access_token"]
    job_id = _add_job("match-api", "m-noresume", skills={"Python"})

    response = client.get(f"/api/jobs/{job_id}/match", headers=auth_headers(token))
    assert response.status_code == 404
    assert "resume" in response.json()["detail"].lower()


def test_match_valid_job_with_resume():
    register_user(email="match.valid@example.com")
    token = login_user(email="match.valid@example.com").json()["access_token"]
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]

    create_resume(
        user_id,
        skills=["Python", "SQL", "Pandas", "Excel", "Power BI"],
        education=[{"degree": "Bachelor's degree", "field_of_study": "Economics"}],
    )
    job_id = _add_job(
        "match-api",
        "m-valid",
        skills={"Python", "SQL", "Pandas", "Power BI", "Tableau"},
        qualifications={"Bachelor's degree"},
        minimum_experience_years=2,
        maximum_experience_years=5,
    )

    response = client.get(f"/api/jobs/{job_id}/match", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == job_id
    assert body["skill_match_percentage"] == 80.0
    assert body["qualification_match_percentage"] == 100.0
    assert body["experience_match_percentage"] is None
    assert body["experience_status"] == "unknown"
    assert body["candidate_experience_years"] is None
    assert body["minimum_required_years"] == 2
    assert body["maximum_required_years"] == 5
    assert "Tableau" in body["missing_skills"]
    assert "Python" in body["matched_skills"]
    assert body["matched_qualifications"] == ["Bachelor's degree"]
    assert body["overall_match_percentage"] == round((80.0 * 0.5 + 100.0 * 0.3) / 0.8, 2)
    assert body["component_weights"] == {"skill": 50, "qualification": 30, "experience": 20}
    assert "Strong match." in body["summary"]


def test_match_job_without_requirements_is_unknown_not_misleading():
    register_user(email="match.noreq@example.com")
    token = login_user(email="match.noreq@example.com").json()["access_token"]
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]

    create_resume(user_id, skills=["Python"])
    job_id = _add_job(
        "match-api",
        "m-noreq",
        skills=set(),
        qualifications=set(),
        minimum_experience_years=None,
        maximum_experience_years=None,
    )

    response = client.get(f"/api/jobs/{job_id}/match", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["skill_match_percentage"] is None
    assert body["qualification_match_percentage"] is None
    assert body["experience_match_percentage"] is None
    assert body["overall_match_percentage"] is None
    assert body["experience_status"] == "no_requirement"
    assert "Insufficient information" in body["summary"]


def test_match_incomplete_resume_scores_zero_not_unknown():
    register_user(email="match.incomplete@example.com")
    token = login_user(email="match.incomplete@example.com").json()["access_token"]
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]

    create_resume(user_id, skills=[], education=[])
    job_id = _add_job(
        "match-api",
        "m-minimal",
        skills={"Python"},
        qualifications={"Bachelor's degree"},
        minimum_experience_years=2,
    )

    response = client.get(f"/api/jobs/{job_id}/match", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["skill_match_percentage"] == 0.0
    assert body["qualification_match_percentage"] == 0.0
    assert body["overall_match_percentage"] == 0.0
    assert body["missing_skills"] == ["Python"]
    assert "Poor match." in body["summary"]


def test_match_uses_only_own_resume():
    register_user(email="match.owner@example.com")
    owner_token = login_user(email="match.owner@example.com").json()["access_token"]
    owner_id = client.get("/api/auth/me", headers=auth_headers(owner_token)).json()["id"]

    register_user(email="match.viewer@example.com")
    viewer_token = login_user(email="match.viewer@example.com").json()["access_token"]

    create_resume(owner_id, skills=["Python"])
    job_id = _add_job("match-api", "m-owner", skills={"Python"})

    owner_result = client.get(f"/api/jobs/{job_id}/match", headers=auth_headers(owner_token))
    assert owner_result.json()["skill_match_percentage"] == 100.0

    viewer_result = client.get(f"/api/jobs/{job_id}/match", headers=auth_headers(viewer_token))
    assert viewer_result.status_code == 404


def test_match_with_certification_qualifications():
    register_user(email="match.cert@example.com")
    token = login_user(email="match.cert@example.com").json()["access_token"]
    user_id = client.get("/api/auth/me", headers=auth_headers(token)).json()["id"]

    from app.models.resume import Certification

    db = TestingSessionLocal()
    try:
        resume = Resume(user_id=user_id, file_name="resume.pdf", raw_text="x")
        db.add(resume)
        db.flush()
        db.add(Certification(resume_id=resume.id, name="AWS Certified Solutions Architect"))
        db.commit()
        db.refresh(resume)
        resume_id = resume.id
    finally:
        db.close()

    job_id = _add_job(
        "match-api",
        "m-cert",
        skills={"Python"},
        qualifications={"AWS Certified Solutions Architect"},
    )

    response = client.get(f"/api/jobs/{job_id}/match", headers=auth_headers(token))
    assert response.status_code == 200
    body = response.json()
    assert body["qualification_match_percentage"] == 100.0
    assert "AWS Certified Solutions Architect" in body["matched_qualifications"]
    assert resume_id > 0