"""Tests for the ingestion/upsert service (dedup, stats, error handling)."""

from datetime import datetime

import pytest
from sqlalchemy.orm import selectinload

from tests.conftest import TestingSessionLocal

from app.models.job import Job, JobSkill, JobQualification
from app.services.job_ingestion import (
    IngestionStats,
    JobIngestionError,
    ingest_jobs,
)
from app.services.providers.base import JobProvider, ProviderJob


class StaticProvider(JobProvider):
    """Test provider yielding a fixed list of raw jobs."""

    name = "static-test"

    def __init__(self, jobs):
        self._jobs = jobs

    def fetch_jobs(self):
        return list(self._jobs)


class FailingProvider(JobProvider):
    name = "failing-test"

    def fetch_jobs(self):
        raise RuntimeError("upstream is down")


def _job(source="ingest-1", external_id="i-1", **overrides) -> ProviderJob:
    defaults = dict(
        source=source,
        external_id=external_id,
        title="Analyst",
        company="TestCorp",
        location="Lahore, Pakistan",
        work_mode="remote",
        employment_type="full-time",
        salary_min=100,
        salary_max=200,
        currency="USD",
        required_skills=["Python", "Excel"],
        qualifications=["Bachelor's in CS"],
    )
    defaults.update(overrides)
    return ProviderJob(**defaults)


def _get_job(source, external_id):
    db = TestingSessionLocal()
    try:
        return (
            db.query(Job)
            .options(selectinload(Job.skills), selectinload(Job.qualifications))
            .filter(Job.source == source, Job.external_id == external_id)
            .first()
        )
    finally:
        db.close()


def _count_jobs_for(source):
    db = TestingSessionLocal()
    try:
        return db.query(Job).filter(Job.source == source).count()
    finally:
        db.close()


def test_ingest_inserts_new_jobs_with_children():
    stats = ingest_jobs(TestingSessionLocal(), StaticProvider([_job(source="ingest-1", external_id="a-1")]))

    assert isinstance(stats, IngestionStats)
    assert stats.fetched == 1
    assert stats.inserted == 1
    assert stats.updated == 0
    assert stats.skipped == 0
    assert stats.failed == 0

    job = _get_job("ingest-1", "a-1")
    assert job is not None
    assert job.employment_type == "full-time"
    assert job.work_mode == "remote"
    assert job.city == "Lahore"
    assert job.country == "Pakistan"
    assert job.is_active is True
    assert {s.skill_name for s in job.skills} == {"Python", "Excel"}
    assert {q.qualification for q in job.qualifications} == {"Bachelor's in CS"}


def test_ingest_is_idempotent():
    provider = StaticProvider([_job(source="ingest-2", external_id="a-1")])
    ingest_jobs(TestingSessionLocal(), provider)
    stats = ingest_jobs(TestingSessionLocal(), provider)

    assert stats.fetched == 1
    assert stats.inserted == 0
    assert stats.updated == 0
    assert stats.skipped == 1
    assert _count_jobs_for("ingest-2") == 1


def test_ingest_updates_changed_job_and_replaces_children():
    provider = StaticProvider([_job(source="ingest-3", external_id="a-1", salary_max=200)])
    ingest_jobs(TestingSessionLocal(), provider)

    provider._jobs = [
        _job(
            source="ingest-3",
            external_id="a-1",
            salary_max=350,
            title="Senior Analyst",
            required_skills=["Python", "Python", "Spark"],  # dup casing + new skill
        )
    ]
    stats = ingest_jobs(TestingSessionLocal(), provider)

    assert stats.updated == 1
    assert stats.skipped == 0
    job = _get_job("ingest-3", "a-1")
    assert job.salary_max == 350
    assert job.title == "Senior Analyst"
    assert {s.normalized_name for s in job.skills} == {"python", "spark"}
    assert len(job.skills) == 2  # duplicates collapsed, old row replaced


def test_ingest_counts_failed_records_and_keeps_valid_ones():
    provider = StaticProvider(
        [
            _job(source="ingest-4", external_id="ok"),
            _job(source="ingest-4", external_id="bad", employment_type="permanent"),
        ]
    )
    stats = ingest_jobs(TestingSessionLocal(), provider)

    assert stats.fetched == 2
    assert stats.inserted == 1
    assert stats.failed == 1
    assert len(stats.errors) == 1
    assert "employment_type" in stats.errors[0]
    assert _get_job("ingest-4", "ok") is not None
    assert _get_job("ingest-4", "bad") is None


def test_ingest_provider_failure_raises():
    with pytest.raises(JobIngestionError, match="fetching jobs"):
        ingest_jobs(TestingSessionLocal(), FailingProvider())


def test_ingest_marks_expired_jobs_inactive():
    provider = StaticProvider(
        [_job(source="ingest-5", external_id="old", expires_at=datetime(2025, 1, 1))]
    )
    ingest_jobs(TestingSessionLocal(), provider)
    assert _get_job("ingest-5", "old").is_active is False


def test_ingest_reactivates_expired_job_when_expiry_extends():
    expired = _job(source="ingest-6", external_id="x", expires_at=datetime(2025, 1, 1))
    fresh = _job(source="ingest-6", external_id="x", expires_at=datetime(2027, 1, 1))
    provider = StaticProvider([expired])
    ingest_jobs(TestingSessionLocal(), provider)
    assert _get_job("ingest-6", "x").is_active is False

    provider._jobs = [fresh]
    stats = ingest_jobs(TestingSessionLocal(), provider)
    assert stats.updated == 1
    assert _get_job("ingest-6", "x").is_active is True


def test_ingest_counts_fetched_across_multiple_jobs():
    provider = StaticProvider(
        [
            _job(source="ingest-7", external_id="a"),
            _job(source="ingest-7", external_id="b"),
            _job(source="ingest-7", external_id="c"),
        ]
    )
    stats = ingest_jobs(TestingSessionLocal(), provider)
    assert stats.fetched == 3
    assert stats.inserted == 3
    assert _count_jobs_for("ingest-7") == 3