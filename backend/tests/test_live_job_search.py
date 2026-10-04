"""Live, resume-driven job recommendations (JSearch provider + endpoint)."""

import httpx
import pytest

from tests.conftest import TestingSessionLocal, client
from tests.test_job_match_api import auth_headers, login_user, register_user

from app.core.config import settings
from app.models.resume import Experience, Resume, Skill
from app.services import live_job_search
from app.services.live_job_search import build_search_terms
from app.services.matching_engine import skill_match, skill_match_key
from app.services.providers.jsearch import (
    JSearchError,
    JSearchProvider,
    extract_skills,
    map_posting,
)
from app.services.providers import jobicy
from app.services.providers.jobicy import JobicyProvider, region_allowed
from app.services.resume_parser import parse_sections


def _posting(job_id, title, description, **extra):
    return {
        "job_id": job_id,
        "job_title": title,
        "employer_name": "Acme Analytics",
        "job_description": description,
        "job_apply_link": f"https://jobs.example/{job_id}",
        "job_city": "Lahore",
        "job_country": "PK",
        "job_employment_type": "FULLTIME",
        "job_posted_at_datetime_utc": "2026-10-01T00:00:00.000Z",
        **extra,
    }


def _transport(postings_by_query, status=200):
    def handler(request: httpx.Request):
        assert request.url.path == "/search-v2"
        query = request.url.params["query"]
        jobs = postings_by_query.get(query, [])
        return httpx.Response(status, json={"status": "OK", "data": {"jobs": jobs, "cursor": None}})

    return httpx.MockTransport(handler)


# --- Resume parser: designed PDF templates ---------------------------------


def test_parser_reads_letter_spaced_headings_and_middle_dot_skills():
    text = "\n".join(
        [
            "P R O F E S S I O N AL S U M M AR Y",
            "Data student with Python skills.",
            "T E C H N I C AL S K I L L S",
            "Languages & Tools: Python (Intermediate) · Stata · SPSS . Power BI",
            "P R O J E C T S",
            "▸ Built a dashboard in Excel.",
            "C E R T I F I C A T I O N S & AC H I E V E M E N T S",
            "▸ MS Word Associate — Microsoft Office Specialist",
        ]
    )
    sections = parse_sections(text)
    assert sections["skills"] == ["Python (Intermediate)", "Stata", "SPSS", "Power BI"]
    assert [c["name"] for c in sections["certifications"]] == ["MS Word Associate"]


def test_skill_match_key_ignores_parenthetical_qualifiers():
    assert skill_match_key("Python (Intermediate)") == skill_match_key("Python")
    assert skill_match_key("MS Excel (Certified)") == skill_match_key("Excel")


def test_specific_analytics_skills_cover_general_requirements():
    result = skill_match(
        ["Statistical Analysis", "Exploratory Data Analysis", "Power BI"],
        ["Statistics", "Data Analysis", "Data Visualization", "SQL"],
    )
    assert result.matched_skills == ["Statistics", "Data Analysis", "Data Visualization"]
    assert result.missing_skills == ["SQL"]


# --- JSearch provider --------------------------------------------------------


def test_extract_skills_uses_word_boundaries():
    text = "We need SQL, Power BI and C++. Rust is a plus. Excellent communication."
    found = extract_skills(text, ["SQL", "Power BI", "C++", "C", "R", "Excel"])
    assert found == ["SQL", "Power BI", "C++"]


def test_extract_skills_short_names_are_case_sensitive():
    prose = "Own our go to market plan and partner with R&D on every launch."
    assert extract_skills(prose, ["Go", "R"]) == []
    assert extract_skills("Services in Go; models in R.", ["Go", "R"]) == ["Go", "R"]


def test_map_posting_maps_fields_and_infers_skills():
    job = map_posting(
        _posting(
            "abc",
            "Data Analyst",
            "Use SQL and Power BI to build dashboards.",
            job_is_remote=True,
            job_employment_type="CONTRACTOR",
            job_required_experience={"required_experience_in_months": 24},
            job_required_education={"bachelors_degree": True},
        ),
        ["SQL", "Power BI", "Tableau"],
    )
    assert job.source == "jsearch"
    assert job.external_id == "abc"
    assert job.employment_type == "contract"
    assert job.work_mode == "remote"
    assert job.required_skills == ["SQL", "Power BI"]
    assert job.qualifications == ["Bachelor's degree"]
    assert job.minimum_experience_years == 2.0
    assert job.posted_at.year == 2026


def test_map_posting_skips_records_without_identity():
    assert map_posting({"job_title": "Analyst"}, []) is None


def test_provider_dedupes_across_queries():
    shared = _posting("same", "Data Analyst", "SQL")
    provider = JSearchProvider(
        api_key="k",
        queries=["a", "b"],
        client=httpx.Client(transport=_transport({"a": [shared], "b": [shared]})),
    )
    jobs = provider.fetch_jobs()
    assert [j.external_id for j in jobs] == ["same"]


def test_provider_raises_when_every_query_fails():
    provider = JSearchProvider(
        api_key="bad",
        queries=["a"],
        client=httpx.Client(transport=_transport({}, status=403)),
    )
    with pytest.raises(JSearchError, match="API key"):
        provider.fetch_jobs()


# --- Query building ---------------------------------------------------------


def _resume(titles, skills=()):
    resume = Resume(user_id=0, file_name="r.pdf")
    resume.experience = [
        Experience(company="X", title=t, currently_employed=(i == 0)) for i, t in enumerate(titles)
    ]
    resume.skills = [Skill(name=s) for s in skills]
    return resume


def test_search_terms_from_titles_drop_founder_and_fragments():
    resume = _resume(
        [
            "Sales Executive",
            "Collaborated with cross-functional teams",
            "Founder & Business Analyst",
            "Data Analyst",
        ]
    )
    assert build_search_terms(resume) == ["Sales Executive", "Business Analyst", "Data Analyst"]


def test_search_terms_prefer_profile_roles_then_fall_back_to_skills():
    resume = _resume(["Data Analyst"])
    assert build_search_terms(resume, ["BI Analyst"])[:2] == ["BI Analyst", "Data Analyst"]
    assert build_search_terms(_resume([], ["Python (Intermediate)", "SQL"])) == ["Python SQL"]


# --- Endpoint ---------------------------------------------------------------


@pytest.fixture
def live_user(monkeypatch):
    live_job_search.clear_cache()
    monkeypatch.setattr(settings, "JOBS_API_KEY", "test-key")
    email = "live.recs@example.com"
    register_user(email)
    token = login_user(email).json()["access_token"]
    user = client.get("/api/auth/me", headers=auth_headers(token)).json()
    db = TestingSessionLocal()
    try:
        old = db.query(Resume).filter(Resume.user_id == user["id"]).first()
        if old is None:
            resume = Resume(user_id=user["id"], file_name="cv.pdf", raw_text="x")
            db.add(resume)
            db.flush()
            for name in ("Python (Intermediate)", "Power BI", "MS Excel (Certified)"):
                db.add(Skill(resume_id=resume.id, name=name))
            db.add(Experience(resume_id=resume.id, company="NESPAK", title="Data Analyst", currently_employed=True))
            db.commit()
    finally:
        db.close()
    yield auth_headers(token)
    live_job_search.clear_cache()


def _fake_factory(calls):
    postings = {
        "Data Analyst in Pakistan": [
            _posting("live-1", "Data Analyst", "Python, Power BI and Excel dashboards."),
            _posting("live-2", "Senior Data Engineer", "Spark, Airflow, Kubernetes, Python."),
        ]
    }

    def factory(source, queries, resume):
        assert source == "jsearch"
        calls.append(list(queries))
        return JSearchProvider(
            api_key="test-key",
            queries=queries,
            extra_skills=[s.name for s in resume.skills],
            client=httpx.Client(transport=_transport(postings)),
        )

    return factory


def test_recommendations_unconfigured_when_no_key_and_no_fallback(live_user, monkeypatch):
    monkeypatch.setattr(settings, "JOBS_API_KEY", "")
    monkeypatch.setattr(settings, "JOBS_FALLBACK_PROVIDER", "")
    response = client.get("/api/jobs/recommendations", headers=live_user)
    assert response.status_code == 503
    assert "JOBS_API_KEY" in response.json()["detail"]


def test_recommendations_rank_live_jobs_and_cache(live_user, monkeypatch):
    calls = []
    monkeypatch.setattr(live_job_search, "_make_provider", _fake_factory(calls))

    body = client.get("/api/jobs/recommendations", headers=live_user).json()
    assert body["source"] == "jsearch"
    assert body["queries"] == ["Data Analyst in Pakistan"]
    titles = [item["job"]["title"] for item in body["items"]]
    assert titles == ["Data Analyst", "Senior Data Engineer"]
    top = body["items"][0]["match"]
    assert top["skill_match_percentage"] == 100.0
    assert set(top["matched_skills"]) == {"Python", "Power BI", "Excel"}

    client.get("/api/jobs/recommendations", headers=live_user)
    assert len(calls) == 1  # served from cache
    client.get("/api/jobs/recommendations?refresh=true", headers=live_user)
    assert len(calls) == 2


def test_recommendations_report_provider_failure(live_user, monkeypatch):
    def failing(source, queries, resume):
        return JSearchProvider(
            api_key="k", queries=queries, client=httpx.Client(transport=_transport({}, status=429))
        )

    monkeypatch.setattr(live_job_search, "_make_provider", failing)
    response = client.get("/api/jobs/recommendations", headers=live_user)
    assert response.status_code == 502
    assert "quota" in response.json()["detail"]


# --- Jobicy keyless fallback ------------------------------------------------


def _jobicy_job(job_id, title, description, geo="Anywhere", job_type="Full-Time", **extra):
    return {
        "id": job_id,
        "url": f"https://jobicy.com/jobs/{job_id}-x",
        "jobTitle": title,
        "companyName": "Remote &amp; Co",
        "jobType": [job_type],
        "jobGeo": geo,
        "pubDate": "2026-10-04T05:35:56+05:00",
        "jobDescription": f"<p>{description}</p><ul><li>Remote &amp; async</li></ul>",
        **extra,
    }


def _jobicy_transport(jobs, calls=None):
    def handler(request: httpx.Request):
        if calls is not None:
            calls.append(dict(request.url.params))
        return httpx.Response(200, json={"jobCount": len(jobs), "jobs": jobs})

    return httpx.MockTransport(handler)


def test_region_filter_uses_whole_words():
    allowed = ["anywhere", "apac", "asia", "pakistan"]
    assert region_allowed("Anywhere", allowed)
    assert region_allowed("APAC,  EMEA,  USA", allowed)
    assert region_allowed("", allowed)
    assert not region_allowed("USA", allowed)
    assert not region_allowed("Caucasia", ["asia"])


def test_jobicy_maps_strips_html_filters_regions_and_caches_queries():
    jobicy.clear_cache()
    calls = []
    transport = _jobicy_transport(
        [
            _jobicy_job(1, "Data Analyst", "SQL and Power BI reporting.", job_type="Contract",
                        salaryMin="40000", salaryMax="60000", salaryCurrency="USD", salaryPeriod="yearly"),
            _jobicy_job(2, "Data Analyst (US)", "SQL", geo="USA"),
            _jobicy_job(3, "Hourly Analyst", "Excel", salaryMin="30", salaryMax="32", salaryPeriod="hourly"),
        ],
        calls,
    )
    provider = JobicyProvider(
        queries=["Data Analyst"],
        allowed_regions=["anywhere"],
        client=httpx.Client(transport=transport),
    )
    jobs = {j.external_id: j for j in provider.fetch_jobs()}
    assert sorted(jobs) == ["1", "3"]  # USA-only posting dropped
    job = jobs["1"]
    assert job.source == "jobicy"
    assert job.company == "Remote & Co"
    assert job.work_mode == "remote"
    assert job.employment_type == "contract"
    assert job.location == "Remote (Anywhere)"
    assert (job.salary_min, job.salary_max, job.currency) == (40000.0, 60000.0, "USD")
    assert job.posted_at.hour == 0  # 05:35+05:00 -> 00:35 UTC
    assert job.application_url.startswith("https://jobicy.com/")
    assert "<p>" not in job.description and "Remote & async" in job.description
    assert job.required_skills == ["SQL", "Power BI"]
    assert jobs["3"].salary_min is None  # hourly figures are not stored as salary
    assert calls == [{"count": "50", "tag": "Data Analyst", "geo": "apac"}]

    provider.fetch_jobs()
    assert len(calls) == 1  # second call served from the shared cache
    jobicy.clear_cache()


def test_recommendations_fall_back_to_jobicy_without_key(live_user, monkeypatch):
    monkeypatch.setattr(settings, "JOBS_API_KEY", "")
    monkeypatch.setattr(settings, "JOBS_FALLBACK_PROVIDER", "jobicy")
    seen = {}

    def factory(source, queries, resume):
        seen["source"], seen["queries"] = source, queries
        return JobicyProvider(
            queries=queries,
            extra_skills=[s.name for s in resume.skills],
            client=httpx.Client(
                transport=_jobicy_transport(
                    [_jobicy_job("j-1", "Remote Data Analyst", "Python, Power BI, Excel.")]
                )
            ),
        )

    jobicy.clear_cache()
    monkeypatch.setattr(live_job_search, "_make_provider", factory)
    body = client.get("/api/jobs/recommendations", headers=live_user).json()
    assert seen == {"source": "jobicy", "queries": ["Data Analyst"]}
    assert body["source"] == "jobicy"
    assert body["location"] == "Remote"
    assert [item["job"]["title"] for item in body["items"]] == ["Remote Data Analyst"]
    assert body["items"][0]["match"]["skill_match_percentage"] == 100.0
    jobicy.clear_cache()
