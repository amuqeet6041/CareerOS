"""End-to-end tests for saved jobs (save, unsave, list)."""

from tests.conftest import client

from tests.test_jobs_api import _add_job


def _register_and_login(email: str) -> dict:
    client.post(
        "/api/auth/register",
        json={"name": "Saved Jobs Tester", "email": email, "password": "secret123"},
    )
    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "secret123"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_saved_jobs_endpoints_require_auth():
    assert client.get("/api/jobs/saved").status_code == 401
    assert client.post("/api/jobs/1/save").status_code == 401
    assert client.delete("/api/jobs/1/save").status_code == 401


def test_save_job_returns_created_record_with_embedded_job():
    job_id = _add_job("api-saved-create", "sc-1", title="Saved Analyst")
    headers = _register_and_login("saved-create@example.com")

    response = client.post(f"/api/jobs/{job_id}/save", headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert body["job_id"] == job_id
    assert body["job"]["id"] == job_id
    assert body["job"]["title"] == "Saved Analyst"
    assert {s["skill_name"] for s in body["job"]["skills"]} >= {"Excel", "SQL"}


def test_save_missing_job_returns_404():
    headers = _register_and_login("saved-missing@example.com")
    response = client.post("/api/jobs/999999999/save", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_save_duplicate_returns_409():
    job_id = _add_job("api-saved-duplicate", "sd-1")
    headers = _register_and_login("saved-duplicate@example.com")

    assert client.post(f"/api/jobs/{job_id}/save", headers=headers).status_code == 201
    response = client.post(f"/api/jobs/{job_id}/save", headers=headers)
    assert response.status_code == 409
    assert response.json()["detail"] == "Job already saved"


def test_saved_jobs_are_scoped_to_the_authenticated_user():
    job_id = _add_job("api-saved-scope", "ss-1")
    alice = _register_and_login("saved-alice@example.com")
    bob = _register_and_login("saved-bob@example.com")

    assert client.post(f"/api/jobs/{job_id}/save", headers=alice).status_code == 201
    assert client.get("/api/jobs/saved", headers=bob).json() == []

    listed = client.get("/api/jobs/saved", headers=alice)
    assert listed.status_code == 200
    assert [item["job_id"] for item in listed.json()] == [job_id]


def test_unsave_removes_record_and_is_idempotent():
    job_id = _add_job("api-saved-unsave", "su-1")
    headers = _register_and_login("saved-unsave@example.com")

    assert client.post(f"/api/jobs/{job_id}/save", headers=headers).status_code == 201
    assert client.delete(f"/api/jobs/{job_id}/save", headers=headers).status_code == 204
    assert client.get("/api/jobs/saved", headers=headers).json() == []
    assert client.delete(f"/api/jobs/{job_id}/save", headers=headers).status_code == 204


def test_unsave_missing_job_returns_404():
    headers = _register_and_login("saved-unsave-missing@example.com")
    response = client.delete("/api/jobs/999999999/save", headers=headers)
    assert response.status_code == 404


def test_saved_list_newest_first_with_job_data():
    first_id = _add_job("api-saved-order", "so-1", title="First Saved")
    second_id = _add_job("api-saved-order", "so-2", title="Second Saved")
    headers = _register_and_login("saved-order@example.com")

    client.post(f"/api/jobs/{first_id}/save", headers=headers)
    client.post(f"/api/jobs/{second_id}/save", headers=headers)

    listed = client.get("/api/jobs/saved", headers=headers)
    assert listed.status_code == 200
    items = listed.json()
    assert [item["job_id"] for item in items] == [second_id, first_id]
    assert all(item["job"] is not None for item in items)