"""Tests for the application-tracking response shape (embedded job data).

The core application behavior (create, list, patch, scoping, 409/404/422) is
covered by test_auth.py. These tests pin the ``job`` field the frontend relies
on to render the Applications dashboard without N extra detail requests.
"""

from tests.conftest import client

from tests.test_jobs_api import _add_job


def _register_and_login(email: str) -> dict:
    client.post(
        "/api/auth/register",
        json={"name": "Applications Tester", "email": email, "password": "secret123"},
    )
    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "secret123"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _apply(job_id: int, headers: dict):
    return client.post("/api/applications", json={"job_id": job_id}, headers=headers)


def test_application_create_response_embeds_job():
    job_id = _add_job("api-app-create", "ac-1", title="Embedded Role")
    headers = _register_and_login("app-create@example.com")

    response = _apply(job_id, headers)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "applied"
    assert body["job_id"] == job_id
    assert body["job"]["id"] == job_id
    assert body["job"]["title"] == "Embedded Role"
    assert {s["skill_name"] for s in body["job"]["skills"]} >= {"Excel", "SQL"}


def test_application_list_embeds_job():
    job_id = _add_job("api-app-list", "al-1", title="Listed Role")
    headers = _register_and_login("app-list@example.com")

    assert _apply(job_id, headers).status_code == 201
    listed = client.get("/api/applications", headers=headers)
    assert listed.status_code == 200
    items = listed.json()
    assert len(items) == 1
    assert items[0]["job"]["id"] == job_id
    assert items[0]["job"]["company"] == "TestCorp"