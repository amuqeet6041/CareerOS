"""Tests for canonical job field normalization helpers."""

from datetime import datetime, timedelta

from app.utils.job_fields import (
    EMPLOYMENT_TYPES,
    WORK_MODES,
    canonicalize_employment_type,
    canonicalize_work_mode,
    derive_city_country,
    is_expired,
    is_known_employment_type,
    is_known_work_mode,
    normalize_qualification,
    normalize_skill,
    normalize_text,
)


def test_employment_types_are_fixed_contract():
    assert EMPLOYMENT_TYPES == {
        "full-time",
        "part-time",
        "contract",
        "internship",
        "temporary",
        "freelance",
    }


def test_work_modes_are_fixed_contract():
    assert WORK_MODES == {"remote", "hybrid", "onsite"}


def test_normalize_text_lowercases_and_collapses():
    assert normalize_text("  Machine   Learning ") == "machine learning"
    assert normalize_text("") is None
    assert normalize_text(None) is None


def test_normalize_skill_and_qualification_are_case_insensitive_keys():
    assert normalize_skill("SQL") == "sql"
    assert normalize_skill("Data Analysis") == "data analysis"
    assert normalize_qualification("Bachelor's in CS") == "bachelor's in cs"


def test_canonicalize_employment_type_synonyms():
    assert canonicalize_employment_type("Full Time") == "full-time"
    assert canonicalize_employment_type("fulltime") == "full-time"
    assert canonicalize_employment_type("Intern") == "internship"
    assert canonicalize_employment_type("temp") == "temporary"
    assert canonicalize_employment_type("independent contractor") == "freelance"
    assert canonicalize_employment_type(None) is None
    assert canonicalize_employment_type("permanent") is None


def test_canonicalize_work_mode_synonyms():
    assert canonicalize_work_mode("On-Site") == "onsite"
    assert canonicalize_work_mode("on site") == "onsite"
    assert canonicalize_work_mode("Fully Remote") == "remote"
    assert canonicalize_work_mode("Hybrid") == "hybrid"
    assert canonicalize_work_mode(None) is None
    assert canonicalize_work_mode("space") is None


def test_known_field_checks():
    assert is_known_employment_type("contract")
    assert not is_known_employment_type("Contract")
    assert is_known_work_mode("onsite")
    assert not is_known_work_mode("office")


def test_derive_city_country():
    assert derive_city_country("Lahore, Pakistan") == ("Lahore", "Pakistan")
    assert derive_city_country("New York, NY, USA") == ("New York, NY", "USA")
    assert derive_city_country("Remote") == ("Remote", None)
    assert derive_city_country("") == (None, None)
    assert derive_city_country(None) == (None, None)


def test_is_expired():
    now = datetime(2026, 1, 1)
    assert is_expired(datetime(2025, 12, 1), now=now)
    assert not is_expired(datetime(2026, 2, 1), now=now)
    assert is_expired(None, now=now) is False
    assert is_expired(datetime(2026, 1, 1), now=now)  # equality counts as expired


def test_is_expired_handles_timezone_aware_datetimes():
    from datetime import timezone

    aware_past = datetime(2025, 1, 1, tzinfo=timezone.utc)
    aware_future = datetime(2027, 1, 1, tzinfo=timezone.utc)
    assert is_expired(aware_past)
    assert not is_expired(aware_future)
    assert not is_expired(aware_future + timedelta(minutes=1))