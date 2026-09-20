"""End-to-end tests for the public jobs API (list, detail, filters, pagination)."""

from datetime import datetime

from tests.conftest import TestingSessionLocal, client

from app.models.job import Job, JobQualification, JobSkill


def _add_job(source, external_id, **overrides):
    """Insert a job directly into the shared test database and return its id."""
    fields = dict(
        source=source,
        external_id=external_id,
        title="Data Analyst",
        company="TestCorp",
        location="Lahore, Pakistan",
        city="Lahore",
        country="Pakistan",
        work_mode="hybrid",
        employment_type="full-time",
        salary_min=100_000,
        salary_max=200_000,
        currency="PKR",
        posted_at=datetime(2026, 9, 1),
        is_active=True,
        skills={"Excel", "SQL"},
        qualifications={"Bachelor's in CS"},
    )
    fields.update(overrides)
    skill_names = fields.pop("skills", set())
    qualification_names = fields.pop("qualifications", set())

    db = TestingSessionLocal()
    try:
        job = Job(**fields)
        for name in skill_names:
            job.skills.append(JobSkill(skill_name=name, normalized_name=name.lower()))
        for name in qualification_names:
            job.qualifications.append(
                JobQualification(qualification=name, normalized_qualification=name.lower())
            )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job.id
    finally:
        db.close()


def test_jobs_list_is_paginated():
    source = "api-pagination"
    for i in range(3):
        _add_job(source, f"p-{i}", title=f"Job {i}", posted_at=datetime(2026, 9, 1 + i))

    response = client.get(f"/api/jobs?source={source}&page_size=2&sort=date_oldest")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total_pages"] == 2
    assert len(body["items"]) == 2
    assert body["items"][0]["title"] == "Job 0"

    page2 = client.get(f"/api/jobs?source={source}&page_size=2&page=2&sort=date_oldest").json()
    assert page2["items"][0]["title"] == "Job 2"


def test_jobs_list_filters_work_mode_and_employment_type():
    source = "api-filters"
    _add_job(source, "f-1", work_mode="remote", employment_type="contract")
    _add_job(source, "f-2", work_mode="onsite", employment_type="full-time")

    remote = client.get(f"/api/jobs?source={source}&work_mode=remote").json()
    assert [j["external_id"] for j in remote["items"]] == ["f-1"]

    contract = client.get(f"/api/jobs?source={source}&employment_type=contract").json()
    assert [j["external_id"] for j in contract["items"]] == ["f-1"]

    neither = client.get(f"/api/jobs?source={source}&employment_type=internship").json()
    assert neither["total"] == 0


def test_jobs_list_filters_city_location_and_source():
    source = "api-loc"
    _add_job(source, "l-1", city="Karachi", location="Karachi, Pakistan")
    _add_job(source, "l-2", city="Lahore", location="Lahore, Pakistan")

    karachi = client.get(f"/api/jobs?source={source}&city=Karachi").json()
    assert [j["external_id"] for j in karachi["items"]] == ["l-1"]

    lahore_substring = client.get(f"/api/jobs?source={source}&city=lahore").json()
    assert [j["external_id"] for j in lahore_substring["items"]] == ["l-2"]

    mixed = client.get(
        f"/api/jobs?source={source}&location=Pakistan&page_size=50"
    ).json()
    assert mixed["total"] == 2


def test_jobs_list_salary_filters():
    source = "api-salary"
    _add_job(source, "s-1", salary_min=500_000, salary_max=800_000)
    _add_job(source, "s-2", salary_min=900_000, salary_max=1_200_000)

    # salary_max >= 850k means only the second job qualifies.
    high_min = client.get(f"/api/jobs?source={source}&salary_min=850000").json()
    assert [j["external_id"] for j in high_min["items"]] == ["s-2"]

    # salary_min <= 1M means both jobs (their min salaries are below).
    capped = client.get(f"/api/jobs?source={source}&salary_max=1000000").json()
    assert capped["total"] == 2


def test_jobs_search_matches_title_company_and_skills_case_insensitively():
    source = "api-search"
    _add_job(source, "r-1", title="Senior Backend Engineer", company="TechNova", skills={"Python"})
    _add_job(source, "r-2", title="BI Analyst", company="DataWorks", skills={"Power BI"})

    by_title = client.get(f"/api/jobs?source={source}&search=backend").json()
    assert [j["external_id"] for j in by_title["items"]] == ["r-1"]

    by_company = client.get(f"/api/jobs?source={source}&search=dataworks").json()
    assert [j["external_id"] for j in by_company["items"]] == ["r-2"]

    by_skill = client.get(f"/api/jobs?source={source}&search=power bi").json()
    assert [j["external_id"] for j in by_skill["items"]] == ["r-2"]

    no_match = client.get(f"/api/jobs?source={source}&search=quantum").json()
    assert no_match["total"] == 0


def test_jobs_search_escapes_like_wildcards():
    source = "api-escaping"
    _add_job(source, "e-1", title="100% Remote Developer")

    literal = client.get(f"/api/jobs?source={source}&search=100%25").json()
    assert literal["total"] == 1

    # A bare % must match literal '%' only, not every job.
    wildcard = client.get(f"/api/jobs?source={source}&search=%25").json()
    assert [j["external_id"] for j in wildcard["items"]] == ["e-1"]


def test_jobs_expired_excluded_by_default_and_included_on_request():
    source = "api-expiry"
    _add_job(source, "x-1", is_active=True, expires_at=None)
    _add_job(source, "x-2", is_active=False, expires_at=datetime(2025, 1, 1))

    default = client.get(f"/api/jobs?source={source}").json()
    assert [j["external_id"] for j in default["items"]] == ["x-1"]

    including = client.get(f"/api/jobs?source={source}&include_inactive=true").json()
    assert {j["external_id"] for j in including["items"]} == {"x-1", "x-2"}


def test_jobs_sorting():
    source = "api-sort"
    _add_job(source, "o-1", title="Newest", posted_at=datetime(2026, 9, 10), salary_max=300_000)
    _add_job(source, "o-2", title="Mid", posted_at=datetime(2026, 9, 5), salary_max=500_000)
    _add_job(source, "o-3", title="Oldest", posted_at=datetime(2026, 9, 1), salary_max=100_000)

    newest = client.get(f"/api/jobs?source={source}&sort=date_newest").json()
    assert [j["title"] for j in newest["items"]] == ["Newest", "Mid", "Oldest"]

    oldest = client.get(f"/api/jobs?source={source}&sort=date_oldest").json()
    assert [j["title"] for j in oldest["items"]] == ["Oldest", "Mid", "Newest"]

    by_salary = client.get(f"/api/jobs?source={source}&sort=salary_desc").json()
    assert [j["title"] for j in by_salary["items"]] == ["Mid", "Newest", "Oldest"]


def test_jobs_detail_returns_full_payload_with_children():
    job_id = _add_job("api-detail", "d-1", title="Full Stack Developer", skills={"React", "Node.js"})

    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == job_id
    assert body["title"] == "Full Stack Developer"
    assert body["employment_type"] == "full-time"
    assert body["application_url"] is None
    assert {s["skill_name"] for s in body["skills"]} == {"React", "Node.js"}
    assert {q["qualification"] for q in body["qualifications"]} == {"Bachelor's in CS"}


def test_jobs_detail_returns_404_for_missing_job():
    response = client.get("/api/jobs/999999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_jobs_detail_returns_inactive_job():
    job_id = _add_job("api-inactive-detail", "i-1", is_active=False, expires_at=datetime(2025, 1, 1))
    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_jobs_invalid_filter_values_return_400():
    assert client.get("/api/jobs?work_mode=space").status_code == 400
    assert client.get("/api/jobs?employment_type=permanent").status_code == 400
    assert client.get("/api/jobs?sort=bogus").status_code == 400


def test_jobs_out_of_range_params_return_422():
    assert client.get("/api/jobs?page=0").status_code == 422
    assert client.get("/api/jobs?page_size=101").status_code == 422


def test_save_job_requires_auth_and_persists():
    assert client.get("/api/jobs/saved").status_code == 401
    assert client.post("/api/jobs/1/save").status_code == 401
    assert client.delete("/api/jobs/1/save").status_code == 401

    job_id = _add_job("api-save", "s-1", title="Saved Role")

    client.post(
        "/api/auth/register",
        json={"name": "Job Saver", "email": "saver@example.com", "password": "secret123"},
    )
    login = client.post(
        "/api/auth/login",
        json={"email": "saver@example.com", "password": "secret123"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(f"/api/jobs/{job_id}/save", headers=headers)
    assert response.status_code == 201
    assert response.json()["job_id"] == job_id

    saved = client.get("/api/jobs/saved", headers=headers)
    assert saved.status_code == 200
    assert [item["job_id"] for item in saved.json()] == [job_id]