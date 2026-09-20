"""Tests for the demo job provider (provider contract + dataset shape)."""

from app.services.job_normalizer import normalize_provider_job
from app.services.providers import DemoJobProvider, get_active_provider
from app.services.providers.base import ProviderJob
from app.utils.job_fields import EMPLOYMENT_TYPES, WORK_MODES


def test_demo_provider_is_active_provider():
    assert isinstance(get_active_provider(), DemoJobProvider)


def test_demo_provider_returns_ten_jobs():
    jobs = DemoJobProvider().fetch_jobs()
    assert len(jobs) == 10
    assert all(isinstance(job, ProviderJob) for job in jobs)


def test_demo_provider_external_ids_are_unique():
    jobs = DemoJobProvider().fetch_jobs()
    external_ids = [job.external_id for job in jobs]
    assert len(external_ids) == len(set(external_ids))


def test_demo_provider_source_is_demo():
    jobs = DemoJobProvider().fetch_jobs()
    assert all(job.source == "demo" for job in jobs)


def test_demo_provider_jobs_normalize_cleanly():
    jobs = DemoJobProvider().fetch_jobs()
    for job in jobs:
        normalized = normalize_provider_job(job)
        assert normalized.employment_type in EMPLOYMENT_TYPES
        assert normalized.work_mode in WORK_MODES
        assert normalized.title
        assert normalized.company
        assert normalized.required_skills
        assert normalized.qualifications


def test_demo_titles_match_expected_roles():
    titles = {job.title for job in DemoJobProvider().fetch_jobs()}
    assert titles == {
        "Junior Data Analyst",
        "Data Analyst",
        "Business Intelligence Intern",
        "Python Developer",
        "Business Analyst",
        "Junior Software Engineer",
        "Data Science Intern",
        "Financial Data Analyst",
        "BI Analyst",
        "Research Analyst",
    }


def test_demo_application_urls_are_clearly_demo():
    jobs = DemoJobProvider().fetch_jobs()
    for job in jobs:
        assert job.application_url
        assert "careeros-demo.example" in job.application_url


def test_fetch_job_by_external_id():
    provider = DemoJobProvider()
    job = provider.fetch_job("demo-01")
    assert job is not None
    assert job.title == "Junior Data Analyst"
    assert provider.fetch_job("does-not-exist") is None