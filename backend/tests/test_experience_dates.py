"""Tests for deterministic employment-date extraction and its wiring.

Covers the Phase 8 gap this closed: before these changes a resume whose AI call
failed always produced ``total_experience_years = None`` even when the document
plainly stated "Jan 2022 - Present", because the deterministic parser left every
date null. These tests pin the date grammar, the conservative rejection of
ambiguous input, the total-experience fallback, and the fact that the AI and
deterministic paths still share one canonical shape.
"""

from app.core.config import settings
from app.services.experience_dates import parse_date_range, strip_date_text
from app.services.experience_duration import calculate_total_experience_years
from app.services.resume_parser import parse_experience, parse_sections

from tests.conftest import client
from tests.test_resume import DOCX_CT, auth_headers, login_user, make_docx, register_user


def entry(lines, index=0):
    return parse_experience(lines)[index]


# ---------------------------------------------------------------------------
# Date grammar
# ---------------------------------------------------------------------------


def test_month_name_range_with_ongoing_marker():
    assert parse_date_range("Jan 2022 - Present") == {
        "start_date": "2022-01",
        "end_date": None,
        "currently_employed": True,
    }


def test_full_month_name_range():
    assert parse_date_range("January 2022 - December 2023") == {
        "start_date": "2022-01",
        "end_date": "2023-12",
        "currently_employed": False,
    }


def test_year_only_range_covers_whole_years():
    """A year-only start resolves to January and a year-only end to December
    so the named years are fully counted, without reaching beyond them."""
    assert parse_date_range("2015 - 2019") == {
        "start_date": "2015-01",
        "end_date": "2019-12",
        "currently_employed": False,
    }


def test_year_range_with_word_separator():
    assert parse_date_range("2020 to 2022") == {
        "start_date": "2020-01",
        "end_date": "2022-12",
        "currently_employed": False,
    }


def test_numeric_month_year_range():
    assert parse_date_range("2021/05 - 2023/06") == {
        "start_date": "2021-05",
        "end_date": "2023-06",
        "currently_employed": False,
    }


def test_en_and_em_dash_separators():
    for separator in ("-", "\u2013", "\u2014"):
        result = parse_date_range(f"2019{separator}2021")
        assert result["start_date"] == "2019-01"
        assert result["end_date"] == "2021-12"


def test_ongoing_marker_variants():
    for token in ("Present", "Current", "Till Date", "Till now", "Ongoing", "To date"):
        result = parse_date_range(f"Mar 2023 - {token}")
        assert result == {
            "start_date": "2023-03",
            "end_date": None,
            "currently_employed": True,
        }


def test_abbreviated_month_with_period():
    assert parse_date_range("Sept 2020 - Present")["start_date"] == "2020-09"


# ---------------------------------------------------------------------------
# Ambiguous / malformed input is rejected, never guessed
# ---------------------------------------------------------------------------


def test_lone_year_is_not_a_range():
    assert parse_date_range("2020") is None


def test_dangling_separator_is_not_a_range():
    assert parse_date_range("2020 -") is None
    assert parse_date_range("- 2020") is None


def test_reversed_range_is_rejected():
    assert parse_date_range("2021 - 2019") is None


def test_ongoing_marker_without_start_is_rejected():
    """A bare "Present" carries no start date, so it cannot become a role."""
    assert parse_date_range("Present") is None
    assert parse_date_range("Currently employed") is None


def test_city_name_is_not_a_separator():
    """"Toronto" contains "to"; a word separator must not split mid-word."""
    assert parse_date_range("Manager at Toronto") is None


def test_impossible_month_number_is_rejected():
    """A broken numeric date is a formatting error, not a bare year, so
    "2020-13" must not quietly become January 2020."""
    assert parse_date_range("2020-13 - 2021-01") is None
    assert parse_date_range("2020-00 - 2021-06") is None


def test_unrecognized_month_names_still_yield_year_only_range():
    """Unknown words around the years are ignored; the explicit year range is
    still unambiguous enough to use."""
    result = parse_date_range("Foo 2020 - Bar 2021")
    assert result == {
        "start_date": "2020-01",
        "end_date": "2021-12",
        "currently_employed": False,
    }


def test_non_string_and_empty_input_is_safe():
    assert parse_date_range("") is None
    assert parse_date_range(None) is None


def test_year_outside_plausible_range_is_rejected():
    assert parse_date_range("1890 - 1895") is None
    assert parse_date_range("2200 - 2201") is None


# ---------------------------------------------------------------------------
# strip_date_text: the date must not leak into title/company text
# ---------------------------------------------------------------------------


def test_strip_removes_inline_date_from_pipe_header():
    assert (
        strip_date_text("Data Analyst | Acme Inc. | Jan 2022 - Present")
        == "Data Analyst | Acme Inc."
    )


def test_strip_removes_parenthesized_range():
    assert (
        strip_date_text("Senior Analyst, Acme Inc. (Jan 2020 - Dec 2021)")
        == "Senior Analyst, Acme Inc."
    )


def test_strip_leaves_line_without_dates_untouched():
    line = "Manager at Initech - 2020"
    assert strip_date_text(line) == line


# ---------------------------------------------------------------------------
# Parser wiring
# ---------------------------------------------------------------------------


def test_date_on_its_own_line_attaches_to_entry():
    result = entry(["Data Analyst at Acme Inc.", "Jan 2022 - Present", "Built reports"])
    assert result["start_date"] == "2022-01"
    assert result["end_date"] is None
    assert result["currently_employed"] is True
    assert result["description"] == "Built reports"


def test_inline_pipe_header_date():
    result = entry(["Data Analyst | Acme Inc. | Jan 2022 - Present"])
    assert result["company"] == "Acme Inc."
    assert result["title"] == "Data Analyst"
    assert result["start_date"] == "2022-01"
    assert result["currently_employed"] is True


def test_company_name_does_not_swallow_trailing_columns():
    """Location/decoration columns after the company must not be folded into
    the name (they previously leaked into matching text)."""
    result = entry(["Senior Analyst | Acme Inc. | Toronto, ON | Jan 2020 - Dec 2021"])
    assert result["company"] == "Acme Inc."
    assert result["title"] == "Senior Analyst"
    assert result["start_date"] == "2020-01"
    assert result["end_date"] == "2021-12"


def test_multiple_entries_keep_their_own_dates():
    results = parse_experience(
        [
            "Analyst at First Co | Jan 2018 - Dec 2020",
            "",
            "Senior Analyst at Second Co | 2022-01 - 2024-06",
        ]
    )
    assert results[0]["start_date"] == "2018-01"
    assert results[0]["end_date"] == "2020-12"
    assert results[1]["start_date"] == "2022-01"
    assert results[1]["end_date"] == "2024-06"


def test_missing_dates_stay_none():
    result = entry(["Analyst at Epsilon", "no dates on this line"])
    assert result["start_date"] is None
    assert result["end_date"] is None
    assert result["currently_employed"] is False


def test_malformed_dates_do_not_crash_parser():
    result = entry(["Analyst at Broken Co", "2019 - 2021 - 2023"])
    assert result["company"] == "Broken Co"


def test_parse_sections_shares_canonical_experience_shape():
    """parse_sections (used by re-analysis) must emit the same experience keys
    as the upload path."""
    parsed = parse_sections("Work Experience\nAnalyst at Acme Inc. | 2022-01 - Present\n")
    assert set(parsed["experience"][0]) == {
        "company",
        "title",
        "description",
        "location",
        "start_date",
        "end_date",
        "currently_employed",
    }
    assert parsed["experience"][0]["start_date"] == "2022-01"


# ---------------------------------------------------------------------------
# Fallback total experience
# ---------------------------------------------------------------------------


def test_deterministic_dates_produce_a_total():
    """End-exclusive arithmetic: Jan 2022 through Jan 2024 is 24 months."""
    experiences = parse_experience(["Analyst at Acme Inc. | Jan 2022 - Jan 2024"])
    assert calculate_total_experience_years(experiences) == 2.0


def test_deterministic_total_stays_unknown_without_dates():
    experiences = parse_experience(["Analyst at Acme Inc."])
    assert calculate_total_experience_years(experiences) is None


def test_deterministic_total_unknown_when_any_role_undated():
    """The all-or-nothing policy still holds: one undated role keeps the total
    unknown rather than reporting a partial figure."""
    experiences = parse_experience(
        [
            "Analyst at Acme Inc. | Jan 2022 - Dec 2023",
            "",
            "Intern at No Dates Ltd",
        ]
    )
    assert calculate_total_experience_years(experiences) is None


# ---------------------------------------------------------------------------
# Endpoint integration: fallback path yields a real total
# ---------------------------------------------------------------------------

DATED_TEXT = """Technical Skills
Python
SQL

Work Experience
Data Analyst | Acme Inc. | Jan 2022 - Jan 2024
Built automated reports
"""


def _register(email):
    register_user(email=email)
    return login_user(email).json()["access_token"]


def _upload(token, text):
    return client.post(
        "/api/resume/upload",
        files={"file": ("dates.docx", make_docx(text), DOCX_CT)},
        headers=auth_headers(token),
    )


def test_upload_with_ai_disabled_persists_deterministic_dates(monkeypatch):
    """The headline fallback fix: with AI off, a dated resume now stores real
    dates and a real total instead of nulls."""
    monkeypatch.setattr(settings, "AI_PROVIDER", "")
    token = _register("dates.det@example.com")
    response = _upload(token, DATED_TEXT)
    assert response.status_code == 201
    data = response.json()
    assert data["analysis_status"] == "parsed"
    assert data["experience"][0]["start_date"] == "2022-01"
    assert data["experience"][0]["end_date"] == "2024-01"
    assert data["total_experience_years"] == 2.0


def test_ai_failure_fallback_still_yields_dates_and_total(monkeypatch):
    from app.services.ai.base import AIRequestError
    from app.services.ai.provider import MockAIProvider

    monkeypatch.setattr(
        "app.services.ai.provider.get_ai_provider",
        lambda: MockAIProvider(error=AIRequestError("throttled", category="rate_limit")),
    )
    token = _register("dates.aifail@example.com")
    response = _upload(token, DATED_TEXT)
    assert response.status_code == 201
    data = response.json()
    assert data["analysis_status"] == "ai_failed"
    assert data["total_experience_years"] == 2.0
    assert [s["name"] for s in data["skills"]] == ["Python", "SQL"]


def test_ai_dates_are_not_overwritten_by_deterministic_dates(monkeypatch):
    """When the AI returns dates they stand; the deterministic parse is only a
    supplement for what the model omitted."""
    from app.services.ai.provider import MockAIProvider

    monkeypatch.setattr(
        "app.services.ai.provider.get_ai_provider",
        lambda: MockAIProvider(
            response={
                "skills": ["Python"],
                "experience": [
                    {
                        "company": "Acme Inc.",
                        "job_title": "Data Analyst",
                        "start_date": "2024-01",
                        "end_date": "2025-01",
                        "currently_employed": False,
                    }
                ],
            }
        ),
    )
    token = _register("dates.merge@example.com")
    response = _upload(token, DATED_TEXT)
    assert response.status_code == 201
    data = response.json()
    assert data["analysis_status"] == "ai_analyzed"
    assert data["experience"][0]["start_date"] == "2024-01"
    assert data["experience"][0]["end_date"] == "2025-01"
    assert data["total_experience_years"] == 1.0


def test_ai_missing_dates_are_filled_from_deterministic_parse(monkeypatch):
    from app.services.ai.provider import MockAIProvider

    monkeypatch.setattr(
        "app.services.ai.provider.get_ai_provider",
        lambda: MockAIProvider(
            response={
                "skills": ["Python"],
                "experience": [{"company": "Acme Inc.", "job_title": "Data Analyst"}],
            }
        ),
    )
    token = _register("dates.fill@example.com")
    response = _upload(token, DATED_TEXT)
    assert response.status_code == 201
    data = response.json()
    assert data["analysis_status"] == "ai_analyzed"
    assert data["experience"][0]["start_date"] == "2022-01"
    assert data["experience"][0]["end_date"] == "2024-01"
    assert data["total_experience_years"] == 2.0


def test_dates_are_not_invented_for_an_unmatched_company(monkeypatch):
    """A company the deterministic parser never saw must not pick up dates."""
    from app.services.ai.provider import MockAIProvider

    monkeypatch.setattr(
        "app.services.ai.provider.get_ai_provider",
        lambda: MockAIProvider(
            response={
                "skills": [],
                "experience": [{"company": "Totally Different Co"}],
            }
        ),
    )
    token = _register("dates.nomatch@example.com")
    response = _upload(token, DATED_TEXT)
    data = response.json()
    assert data["analysis_status"] == "ai_analyzed"
    assert data["experience"][0]["start_date"] is None
    assert data["total_experience_years"] is None


def test_matching_consumes_deterministic_experience_fallback(monkeypatch):
    """End-to-end: with AI unavailable, a dated resume still scores experience
    requirements through the unchanged matching engine."""
    from app.services.ai.base import AIRequestError
    from app.services.ai.provider import MockAIProvider
    from tests.test_jobs_api import _add_job

    monkeypatch.setattr(
        "app.services.ai.provider.get_ai_provider",
        lambda: MockAIProvider(error=AIRequestError("down", category="timeout")),
    )
    token = _register("dates.match@example.com")
    assert _upload(token, DATED_TEXT).status_code == 201

    job_id = _add_job(
        "dates-match",
        "dates-1",
        skills={"Python", "SQL"},
        qualifications={"Bachelor of Science"},
        minimum_experience_years=1,
        maximum_experience_years=4,
    )
    body = client.get(f"/api/jobs/{job_id}/match", headers=auth_headers(token)).json()
    assert body["candidate_experience_years"] == 2.0
    assert body["experience_match_percentage"] == 100.0
    assert body["experience_status"] == "meets_requirement"


def test_reanalysis_reuses_deterministic_dates(monkeypatch):
    """The re-analysis path re-parses stored text so the date supplement is
    available after a transient provider failure clears."""
    from app.services.ai.provider import MockAIProvider

    token = _register("dates.reanalyze@example.com")
    assert _upload(token, DATED_TEXT).status_code == 201

    monkeypatch.setattr(
        "app.services.ai.provider.get_ai_provider",
        lambda: MockAIProvider(
            response={
                "skills": ["Python"],
                "experience": [{"company": "Acme Inc.", "job_title": "Data Analyst"}],
            }
        ),
    )
    body = client.post("/api/resume/analyze", headers=auth_headers(token)).json()
    assert body["analysis_status"] == "ai_analyzed"
    assert body["experience"][0]["start_date"] == "2022-01"
    assert body["total_experience_years"] == 2.0