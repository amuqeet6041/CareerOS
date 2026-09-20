"""Tests for the provider-job -> NormalizedJob normalization layer."""

import pytest

from app.services.job_normalizer import (
    JobNormalizationError,
    NormalizedJob,
    normalize_provider_job,
    qualification_keys,
    skill_keys,
)
from app.services.providers.base import ProviderJob


def _provider_job(**overrides) -> ProviderJob:
    defaults = dict(
        source="demo",
        external_id="x-1",
        title="Data Analyst",
        company="Acme Analytics",
        location="Lahore, Pakistan",
        work_mode="hybrid",
        employment_type="full-time",
        salary_min=1000,
        salary_max=2000,
        currency="USD",
    )
    defaults.update(overrides)
    return ProviderJob(**defaults)


def test_normalizes_valid_provider_job():
    normalized = normalize_provider_job(_provider_job())
    assert isinstance(normalized, NormalizedJob)
    assert normalized.employment_type == "full-time"
    assert normalized.work_mode == "hybrid"
    assert normalized.city == "Lahore"
    assert normalized.country == "Pakistan"


def test_normalizes_synonym_values_and_derives_location():
    normalized = normalize_provider_job(
        _provider_job(work_mode="On-Site", employment_type="Full Time")
    )
    assert normalized.work_mode == "onsite"
    assert normalized.employment_type == "full-time"


def test_missing_external_id_rejected():
    with pytest.raises(JobNormalizationError):
        normalize_provider_job(_provider_job(external_id=""))


def test_missing_title_rejected():
    with pytest.raises(JobNormalizationError):
        normalize_provider_job(_provider_job(title="   "))


def test_missing_company_rejected():
    with pytest.raises(JobNormalizationError):
        normalize_provider_job(_provider_job(company="   "))


def test_missing_source_rejected():
    with pytest.raises(JobNormalizationError):
        normalize_provider_job(_provider_job(source=""))


def test_invalid_employment_type_rejected():
    with pytest.raises(JobNormalizationError, match="employment_type"):
        normalize_provider_job(_provider_job(employment_type="permanent"))


def test_missing_employment_type_rejected():
    with pytest.raises(JobNormalizationError, match="employment_type"):
        normalize_provider_job(_provider_job(employment_type=None))


def test_invalid_work_mode_rejected():
    with pytest.raises(JobNormalizationError, match="work_mode"):
        normalize_provider_job(_provider_job(work_mode="spaceship"))


def test_salary_min_above_max_rejected():
    with pytest.raises(JobNormalizationError, match="salary_min"):
        normalize_provider_job(_provider_job(salary_min=5000, salary_max=1000))


def test_coerces_numeric_fields():
    normalized = normalize_provider_job(
        _provider_job(salary_min=1000, salary_max=2000, minimum_experience_years=1)
    )
    assert isinstance(normalized.salary_min, float)
    assert isinstance(normalized.minimum_experience_years, float)


def test_skill_keys_collapse_case_duplicates():
    keys = skill_keys(["Python", "python", "Data Analysis", "data analysis", ""])
    assert keys == {"python": "Python", "data analysis": "Data Analysis"}
    assert len(keys) == 2


def test_qualification_keys_collapse_case_duplicates():
    keys = qualification_keys(["\t", "Bachelor's in CS", "bachelor's in cs"])
    assert keys == {"bachelor's in cs": "Bachelor's in CS"}