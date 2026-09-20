"""Unit tests for the deterministic employment-duration calculation.

The documented policy: each job counts its start month inclusive and end month
exclusive; currently-employed roles run to the current month; overlapping and
adjacent jobs are merged; missing/malformed/inconsistent date information makes
the total None (unknown), never zero.
"""

from app.services.experience_duration import (
    MonthYear,
    calculate_experience_months,
    calculate_total_experience_years,
    parse_month_year,
)

NOW = MonthYear(2026, 6)


def test_one_job_exact_year():
    result = calculate_experience_months(
        [{"company": "A", "start_date": "2024-01", "end_date": "2025-01"}],
        now=NOW,
    )
    assert result == 12
    assert calculate_total_experience_years(
        [{"company": "A", "start_date": "2024-01", "end_date": "2025-01"}],
        now=NOW,
    ) == 1.0


def test_same_month_job_counts_zero():
    assert calculate_experience_months(
        [{"company": "A", "start_date": "2024-01", "end_date": "2024-01"}],
        now=NOW,
    ) == 0


def test_end_month_exclusive():
    result = calculate_experience_months(
        [{"company": "A", "start_date": "2024-01", "end_date": "2024-06"}],
        now=NOW,
    )
    assert result == 5
    assert calculate_total_experience_years(
        [{"company": "A", "start_date": "2024-01", "end_date": "2024-06"}],
        now=NOW,
    ) == round(5 / 12, 2)


def test_current_job_spans_to_now():
    result = calculate_experience_months(
        [{"company": "A", "start_date": "2024-01", "currently_employed": True}],
        now=NOW,
    )
    assert result == (2026 - 1970) * 12 + 5 - (2024 - 1970) * 12
    assert calculate_total_experience_years(
        [{"company": "A", "start_date": "2024-01", "currently_employed": True}],
        now=NOW,
    ) == round(((2026 - 1970) * 12 + 5 - (2024 - 1970) * 12) / 12, 2)


def test_current_job_just_started_counts_zero():
    assert calculate_experience_months(
        [{"company": "A", "start_date": "2026-06", "currently_employed": True}],
        now=NOW,
    ) == 0


def test_overlapping_jobs_not_double_counted():
    result = calculate_experience_months(
        [
            {"company": "A", "start_date": "2024-01", "end_date": "2025-01"},
            {"company": "B", "start_date": "2024-06", "end_date": "2025-06"},
        ],
        now=NOW,
    )
    assert result == 17


def test_adjacent_jobs_are_merged_not_double_counted():
    result = calculate_experience_months(
        [
            {"company": "A", "start_date": "2024-01", "end_date": "2024-07"},
            {"company": "B", "start_date": "2024-07", "end_date": "2025-01"},
        ],
        now=NOW,
    )
    assert result == 12


def test_non_overlapping_jobs_sum():
    result = calculate_experience_months(
        [
            {"company": "A", "start_date": "2020-01", "end_date": "2021-01"},
            {"company": "B", "start_date": "2022-01", "end_date": "2023-01"},
        ],
        now=NOW,
    )
    assert result == 24
    assert calculate_total_experience_years(
        [
            {"company": "A", "start_date": "2020-01", "end_date": "2021-01"},
            {"company": "B", "start_date": "2022-01", "end_date": "2023-01"},
        ],
        now=NOW,
    ) == 2.0


def test_december_to_january_is_one_month():
    assert calculate_experience_months(
        [{"company": "A", "start_date": "2024-12", "end_date": "2025-01"}],
        now=NOW,
    ) == 1


def test_missing_start_date_is_unknown():
    assert calculate_experience_months(
        [{"company": "A", "end_date": "2025-01"}],
        now=NOW,
    ) is None


def test_missing_end_date_when_not_current_is_unknown():
    assert calculate_experience_months(
        [{"company": "A", "start_date": "2024-01"}],
        now=NOW,
    ) is None


def test_malformed_start_date_is_unknown():
    assert calculate_experience_months(
        [{"company": "A", "start_date": "2025/06", "end_date": "2026-01"}],
        now=NOW,
    ) is None


def test_start_date_as_int_is_unknown():
    assert calculate_experience_months(
        [{"company": "A", "start_date": 202401, "end_date": "2025-01"}],
        now=NOW,
    ) is None


def test_future_start_date_is_unknown():
    assert calculate_experience_months(
        [{"company": "A", "start_date": "2030-01", "end_date": "2031-01"}],
        now=NOW,
    ) is None


def test_end_before_start_is_unknown():
    assert calculate_experience_months(
        [{"company": "A", "start_date": "2025-06", "end_date": "2024-01"}],
        now=NOW,
    ) is None


def test_future_end_date_is_clamped_to_now():
    result = calculate_experience_months(
        [{"company": "A", "start_date": "2020-01", "end_date": "2030-01"}],
        now=NOW,
    )
    assert result == (2026 - 1970) * 12 + 5 - (2020 - 1970) * 12


def test_current_job_with_future_start_is_unknown():
    assert calculate_experience_months(
        [{"company": "A", "start_date": "2030-01", "currently_employed": True}],
        now=NOW,
    ) is None


def test_no_experience_is_unknown_not_zero():
    assert calculate_experience_months([], now=NOW) is None
    assert calculate_total_experience_years([], now=NOW) is None


def test_jobs_without_company_names_are_skipped():
    assert calculate_experience_months(
        [
            {"start_date": "2024-01", "end_date": "2025-01"},
            {"company": "", "start_date": "2022-01", "end_date": "2023-01"},
        ],
        now=NOW,
    ) is None


def test_duplicated_job_counted_once():
    job = {"company": "A", "start_date": "2024-01", "end_date": "2025-01"}
    assert calculate_experience_months([job, dict(job)], now=NOW) == 12


def test_one_unknown_job_poisons_the_total():
    assert calculate_experience_months(
        [
            {"company": "A", "start_date": "2024-01", "end_date": "2025-01"},
            {"company": "B", "start_date": "2022-01"},
        ],
        now=NOW,
    ) is None


def test_parse_month_year_validation():
    assert parse_month_year("2024-01").year == 2024
    assert parse_month_year("2024-01").month == 1
    assert parse_month_year("2024-00") is None
    assert parse_month_year("2024-13") is None
    assert parse_month_year("Jan 2024") is None
    assert parse_month_year(None) is None
    assert parse_month_year(2024) is None


def test_years_rounding_to_two_decimals():
    assert calculate_total_experience_years(
        [{"company": "A", "start_date": "2024-01", "end_date": "2024-06"}],
        now=NOW,
    ) == round(5 / 12, 2)
    assert calculate_total_experience_years(
        [{"company": "A", "start_date": "2024-12", "end_date": "2025-01"}],
        now=NOW,
    ) == round(1 / 12, 2)