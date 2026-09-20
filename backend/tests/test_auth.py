"""Tests for the authentication flow and protected routes.

Uses the shared in-memory SQLite test database defined in conftest.py.
"""

from datetime import datetime, timedelta

from jose import jwt

from tests.conftest import client, TestingSessionLocal

from app.core.config import settings
from app.core.security import create_access_token
from app.models.application import Application
from app.models.job import Job


# Applications reference jobs by foreign key, so seed a handful of job rows.
def _seed_jobs():
    db = TestingSessionLocal()
    try:
        for job_id in range(1, 6):
            if db.query(Job).filter(Job.id == job_id).first() is None:
                db.add(Job(id=job_id, title=f"Job {job_id}", company="Acme"))
        db.commit()
    finally:
        db.close()


_seed_jobs()


def register_user(name="Test User", email="test@example.com", password="secret123"):
    return client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password},
    )


def login_user(email="test@example.com", password="secret123"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_creates_user():
    response = register_user(email="register@example.com")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "register@example.com"
    assert "password" not in data
    assert "id" in data


def test_register_duplicate_email_rejected():
    register_user(email="duplicate@example.com")
    response = register_user(email="duplicate@example.com")
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_returns_token():
    register_user(email="login@example.com")
    response = login_user(email="login@example.com")
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"


def test_login_wrong_password_rejected():
    register_user(email="wrongpass@example.com")
    response = login_user(email="wrongpass@example.com", password="not-the-password")
    assert response.status_code == 401


def test_login_unknown_email_rejected():
    response = login_user(email="nobody@example.com")
    assert response.status_code == 401


def test_get_me_with_valid_token():
    register_user(email="me@example.com")
    token = login_user(email="me@example.com").json()["access_token"]
    response = client.get("/api/auth/me", headers=auth_headers(token))
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_get_me_without_token_rejected():
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_get_me_with_invalid_token_rejected():
    response = client.get("/api/auth/me", headers=auth_headers("not-a-real-token"))
    assert response.status_code == 401


def test_protected_applications_require_auth():
    response = client.get("/api/applications")
    assert response.status_code == 401

    response = client.post("/api/applications", json={"job_id": 1})
    assert response.status_code == 401


def test_applications_scoped_to_current_user():
    register_user(email="alice@example.com", name="Alice")
    alice_token = login_user(email="alice@example.com").json()["access_token"]

    register_user(email="bob@example.com", name="Bob")
    bob_token = login_user(email="bob@example.com").json()["access_token"]

    created = client.post(
        "/api/applications",
        json={"job_id": 1},
        headers=auth_headers(alice_token),
    )
    assert created.status_code == 201

    alice_apps = client.get("/api/applications", headers=auth_headers(alice_token))
    assert alice_apps.status_code == 200
    assert len(alice_apps.json()) == 1

    bob_apps = client.get("/api/applications", headers=auth_headers(bob_token))
    assert bob_apps.status_code == 200
    assert bob_apps.json() == []


def test_patch_application_own_only():
    register_user(email="owner@example.com")
    owner_token = login_user(email="owner@example.com").json()["access_token"]

    register_user(email="other@example.com")
    other_token = login_user(email="other@example.com").json()["access_token"]

    created = client.post(
        "/api/applications",
        json={"job_id": 2},
        headers=auth_headers(owner_token),
    ).json()

    updated = client.patch(
        f"/api/applications/{created['id']}",
        json={"status": "interview"},
        headers=auth_headers(owner_token),
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "interview"

    tampered = client.patch(
        f"/api/applications/{created['id']}",
        json={"status": "offer"},
        headers=auth_headers(other_token),
    )
    assert tampered.status_code == 404


def test_patch_application_invalid_status_rejected():
    register_user(email="status@example.com")
    token = login_user(email="status@example.com").json()["access_token"]

    created = client.post(
        "/api/applications",
        json={"job_id": 3},
        headers=auth_headers(token),
    ).json()

    response = client.patch(
        f"/api/applications/{created['id']}",
        json={"status": "not-a-status"},
        headers=auth_headers(token),
    )
    assert response.status_code == 422


def test_apply_to_nonexistent_job_rejected():
    register_user(email="nojob@example.com")
    token = login_user(email="nojob@example.com").json()["access_token"]

    response = client.post(
        "/api/applications",
        json={"job_id": 999999},
        headers=auth_headers(token),
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_duplicate_application_rejected():
    register_user(email="dupapply@example.com")
    token = login_user(email="dupapply@example.com").json()["access_token"]

    first = client.post(
        "/api/applications",
        json={"job_id": 4},
        headers=auth_headers(token),
    )
    assert first.status_code == 201

    second = client.post(
        "/api/applications",
        json={"job_id": 4},
        headers=auth_headers(token),
    )
    assert second.status_code == 409
    assert second.json()["detail"] == "Application already exists for this job"


def test_different_users_can_apply_to_same_job():
    register_user(email="multia1@example.com", name="Alic2e")
    token_a = login_user(email="multia1@example.com").json()["access_token"]
    register_user(email="multia2@example.com", name="Bobb2")
    token_b = login_user(email="multia2@example.com").json()["access_token"]

    response_a = client.post(
        "/api/applications",
        json={"job_id": 5},
        headers=auth_headers(token_a),
    )
    response_b = client.post(
        "/api/applications",
        json={"job_id": 5},
        headers=auth_headers(token_b),
    )
    assert response_a.status_code == 201
    assert response_b.status_code == 201


def test_application_links_to_job_via_relationship():
    register_user(email="relexample@example.com")
    token = login_user(email="relexample@example.com").json()["access_token"]

    created = client.post(
        "/api/applications",
        json={"job_id": 5},
        headers=auth_headers(token),
    ).json()

    db = TestingSessionLocal()
    try:
        application = db.query(Application).filter(Application.id == created["id"]).first()
        assert application is not None
        assert application.job is not None
        assert application.job.id == 5
        assert application.job.title == "Job 5"
    finally:
        db.close()


def test_get_me_with_malformed_authorization_header_rejected():
    # Wrong scheme (Basic instead of Bearer).
    response = client.get("/api/auth/me", headers={"Authorization": "Basic Zm9vOmJhcg=="})
    assert response.status_code == 401

    # Bearer scheme with no credentials.
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer"})
    assert response.status_code == 401


def test_get_me_with_expired_token_rejected():
    registered = register_user(email="expired@example.com")
    user_id = registered.json()["id"]
    token = create_access_token(subject=str(user_id), expires_delta=timedelta(seconds=-1))
    response = client.get("/api/auth/me", headers=auth_headers(token))
    assert response.status_code == 401


def test_token_for_nonexistent_user_rejected():
    token = create_access_token(subject="99999999", expires_delta=timedelta(minutes=5))
    response = client.get("/api/auth/me", headers=auth_headers(token))
    assert response.status_code == 401


def test_token_with_missing_subject_rejected():
    payload = {"exp": datetime.utcnow() + timedelta(minutes=5)}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    response = client.get("/api/auth/me", headers=auth_headers(token))
    assert response.status_code == 401


def test_access_token_is_lean():
    registered = register_user(email="lean@example.com")
    user_id = registered.json()["id"]
    token = login_user(email="lean@example.com").json()["access_token"]

    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == str(user_id)
    assert "exp" in payload
    assert "password" not in payload
    assert "hashed_password" not in payload


def test_save_job_requires_auth():
    response = client.post("/api/jobs/1/save")
    assert response.status_code == 401


def test_resume_upload_requires_auth():
    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert response.status_code == 401


def test_jobs_browse_is_public():
    # Job discovery must not require auth. The listing is paginated; the page
    # returned should always be internally consistent regardless of how many
    # jobs earlier tests seeded (the old `/api/jobs` returned a bare []).
    response = client.get("/api/jobs")
    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert isinstance(body["items"], list)
    assert body["total"] >= 0
    assert body["total_pages"] == (body["total"] + body["page_size"] - 1) // body["page_size"]
    if body["items"]:
        first = body["items"][0]
        assert first["title"]
        assert first["company"]