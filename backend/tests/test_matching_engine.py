"""Unit tests for the deterministic matching engine (pure calculation layer).

Covers skill/qualification normalization and matching, experience logic,
overall-score weighting, unknown-data handling, and deterministic summaries.
"""

from app.services.matching_engine import (
    COMPONENT_WEIGHTS_PERCENT,
    CandidateProfile,
    build_summary,
    calculate_overall_match,
    experience_match,
    match_candidate_to_job,
    normalize_qualification,
    normalize_skill,
    qualification_match,
    skill_match,
)


# ---------------------------------------------------------------- normalization


def test_normalize_skill_lowercases():
    assert normalize_skill("Python") == "python"


def test_normalize_skill_uppercases():
    assert normalize_skill("PYTHON") == "python"


def test_normalize_skill_mixed_case():
    assert normalize_skill("PyThOn") == "python"


def test_normalize_skill_strips_whitespace():
    assert normalize_skill(" Python ") == "python"


def test_normalize_skill_collapses_inner_whitespace():
    assert normalize_skill("  power   bi  ") == "power bi"


def test_normalize_skill_preserves_meaningful_spaces():
    assert normalize_skill("Power BI") == "power bi"
    assert normalize_skill("SQL") == "sql"


def test_normalize_qualification_case_and_whitespace():
    assert normalize_qualification(" Bachelor's degree ") == "bachelor's degree"


# ---------------------------------------------------------------- skill matching


def test_skill_match_100_percent():
    result = skill_match(
        user_skills=["Python", "SQL"],
        job_required_skills=["python", "sql"],
    )
    assert result.percentage == 100.0
    assert result.matched_skills == ["python", "sql"]
    assert result.missing_skills == []


def test_skill_match_zero_percent():
    result = skill_match(user_skills=["Excel"], job_required_skills=["Python"])
    assert result.percentage == 0.0
    assert result.matched_skills == []
    assert result.missing_skills == ["Python"]


def test_skill_match_partial_book_example():
    required = ["Python", "SQL", "Pandas", "Power BI", "Tableau"]
    candidate = ["Python", "SQL", "Pandas", "Excel", "Power BI"]
    result = skill_match(candidate, required)
    assert result.percentage == 80.0
    assert sorted(result.matched_skills) == ["Pandas", "Power BI", "Python", "SQL"]
    assert result.missing_skills == ["Tableau"]


def test_skill_match_ignores_duplicate_candidate_skills():
    result = skill_match(
        user_skills=["python", "Python", " PYTHON "],
        job_required_skills=["Python"],
    )
    assert result.percentage == 100.0
    assert result.matched_skills == ["Python"]


def test_skill_match_case_insensitive():
    result = skill_match(user_skills=["PYTHON"], job_required_skills=["python"])
    assert result.percentage == 100.0


def test_skill_match_missing_required_skills():
    result = skill_match(user_skills=[], job_required_skills=["Python", "SQL"])
    assert result.percentage == 0.0
    assert result.matched_skills == []
    assert result.missing_skills == ["Python", "SQL"]


def test_skill_match_job_with_no_required_skills_is_unknown():
    result = skill_match(user_skills=["Python"], job_required_skills=[])
    assert result.percentage is None
    assert result.matched_skills == []
    assert result.missing_skills == []


# ---------------------------------------------------- qualification matching


def test_qualification_match_complete():
    result = qualification_match(
        candidate_qualifications=["Bachelor's degree", "Economics"],
        job_required_qualifications=["Bachelor's degree", "Economics"],
    )
    assert result.percentage == 100.0


def test_qualification_match_partial_book_example():
    result = qualification_match(
        candidate_qualifications=["Bachelor's degree", "Economics"],
        job_required_qualifications=["Bachelor's degree", "Economics", "Data Science"],
    )
    assert result.percentage == round((2 / 3) * 100, 2)
    assert result.matched_qualifications == ["Bachelor's degree", "Economics"]
    assert result.missing_qualifications == ["Data Science"]


def test_qualification_match_no_match():
    result = qualification_match(
        candidate_qualifications=["Master's degree"],
        job_required_qualifications=["Bachelor's degree"],
    )
    assert result.percentage == 0.0
    assert result.missing_qualifications == ["Bachelor's degree"]


def test_qualification_match_case_insensitive():
    result = qualification_match(
        candidate_qualifications=["BACHELOR'S DEGREE"],
        job_required_qualifications=["bachelor's degree"],
    )
    assert result.percentage == 100.0


def test_qualification_match_ignores_duplicate_candidates():
    result = qualification_match(
        candidate_qualifications=["Bachelor's degree", "bachelor's degree"],
        job_required_qualifications=["Bachelor's degree"],
    )
    assert result.percentage == 100.0
    assert result.matched_qualifications == ["Bachelor's degree"]


def test_qualification_match_no_requirements_is_unknown():
    result = qualification_match(
        candidate_qualifications=["Bachelor's degree"], job_required_qualifications=[]
    )
    assert result.percentage is None


def test_qualification_match_missing_candidate_data():
    result = qualification_match(
        candidate_qualifications=[], job_required_qualifications=["Bachelor's degree"]
    )
    assert result.percentage == 0.0
    assert result.missing_qualifications == ["Bachelor's degree"]


# ------------------------------------------------------- experience matching


def test_experience_no_requirement_is_unknown():
    result = experience_match(candidate_experience_years=5, minimum_required_years=None, maximum_required_years=None)
    assert result.percentage is None
    assert result.status == "no_requirement"


def test_experience_unknown_candidate_never_assumed_zero():
    result = experience_match(candidate_experience_years=None, minimum_required_years=2, maximum_required_years=None)
    assert result.percentage is None
    assert result.status == "unknown"
    assert result.candidate_experience_years is None


def test_experience_exact_minimum():
    result = experience_match(candidate_experience_years=2, minimum_required_years=2, maximum_required_years=None)
    assert result.percentage == 100.0
    assert result.status == "meets_requirement"


def test_experience_below_minimum_scaled():
    result = experience_match(candidate_experience_years=1, minimum_required_years=2, maximum_required_years=None)
    assert result.percentage == 50.0
    assert result.status == "below_minimum"


def test_experience_above_minimum_ok():
    result = experience_match(candidate_experience_years=5, minimum_required_years=2, maximum_required_years=None)
    assert result.percentage == 100.0
    assert result.status == "meets_requirement"


def test_experience_maximum_boundary_ok():
    result = experience_match(candidate_experience_years=5, minimum_required_years=None, maximum_required_years=5)
    assert result.percentage == 100.0
    assert result.status == "meets_requirement"


def test_experience_above_maximum_scaled():
    result = experience_match(candidate_experience_years=6, minimum_required_years=None, maximum_required_years=5)
    assert result.percentage == round((5 / 6) * 100, 2)
    assert result.status == "above_maximum"


def test_experience_zero_years_below_minimum():
    result = experience_match(candidate_experience_years=0, minimum_required_years=2, maximum_required_years=None)
    assert result.percentage == 0.0
    assert result.status == "below_minimum"


def test_experience_zero_minimum_boundary():
    result = experience_match(candidate_experience_years=0, minimum_required_years=0, maximum_required_years=None)
    assert result.percentage == 100.0
    assert result.status == "meets_requirement"


def test_experience_within_both_bounds():
    result = experience_match(candidate_experience_years=4, minimum_required_years=3, maximum_required_years=5)
    assert result.percentage == 100.0
    assert result.status == "meets_requirement"


def test_experience_below_minimum_with_maximum():
    result = experience_match(candidate_experience_years=2, minimum_required_years=3, maximum_required_years=5)
    assert result.percentage == round((2 / 3) * 100, 2)
    assert result.status == "below_minimum"


def test_experience_above_maximum_with_minimum():
    result = experience_match(candidate_experience_years=6, minimum_required_years=3, maximum_required_years=5)
    assert result.percentage == round((5 / 6) * 100, 2)
    assert result.status == "above_maximum"


# ------------------------------------------------------------ overall score


def test_overall_weighting_book_example():
    overall = calculate_overall_match(80.0, round((2 / 3) * 100, 2), 100.0)
    assert overall == 80.0


def test_overall_perfect_score():
    assert calculate_overall_match(100.0, 100.0, 100.0) == 100.0


def test_overall_stays_within_0_to_100():
    for skill, qual, exp in [
        (100.0, 100.0, 100.0),
        (0.0, 0.0, 0.0),
        (33.33, 66.67, 50.0),
        (12.5, 87.5, 42.9),
    ]:
        value = calculate_overall_match(skill, qual, exp)
        assert value is not None
        assert 0.0 <= value <= 100.0


def test_overall_decimal_handling():
    value = calculate_overall_match(50.0, 66.67, 0.0)
    assert isinstance(value, float)
    assert value == round(value, 2)


def test_overall_redistributes_known_weights_when_skill_unknown():
    overall = calculate_overall_match(None, 80.0, 60.0)
    assert overall == round((80.0 * 0.3 + 60.0 * 0.2) / 0.5, 2)


def test_overall_uses_single_known_component():
    assert calculate_overall_match(100.0, None, None) == 100.0


def test_overall_all_unknown_is_none():
    assert calculate_overall_match(None, None, None) is None


def test_component_weights_are_exposed_as_percentages():
    assert COMPONENT_WEIGHTS_PERCENT == {"skill": 50, "qualification": 30, "experience": 20}


# ------------------------------------------------------------- full pipeline


def test_match_candidate_to_job_deterministic_result():
    profile = CandidateProfile(
        skills=["Python", "SQL"],
        qualifications=["Bachelor's degree"],
        experience_years=None,
    )
    result = match_candidate_to_job(
        profile,
        job_required_skills=["python", "tableau"],
        job_required_qualifications=["Bachelor's degree"],
        minimum_experience_years=2,
        maximum_experience_years=5,
    )
    assert result.skill_match_percentage == 50.0
    assert result.qualification_match_percentage == 100.0
    assert result.experience_match_percentage is None
    assert result.experience_status == "unknown"
    assert result.missing_skills == ["tableau"]
    assert result.matched_qualifications == ["Bachelor's degree"]
    assert result.overall_match_percentage == round((50.0 * 0.5 + 100.0 * 0.3) / 0.8, 2)
    assert "Good match." in result.summary
    assert "Missing required skills: tableau." in result.summary


def test_match_candidate_to_job_no_requirements_is_not_misleading():
    profile = CandidateProfile(skills=["Python"], qualifications=["Bachelor's degree"])
    result = match_candidate_to_job(
        profile,
        job_required_skills=[],
        job_required_qualifications=[],
        minimum_experience_years=None,
        maximum_experience_years=None,
    )
    assert result.skill_match_percentage is None
    assert result.qualification_match_percentage is None
    assert result.experience_match_percentage is None
    assert result.overall_match_percentage is None
    assert "Insufficient information" in result.summary


def test_build_summary_is_deterministic():
    skill = skill_match(["Excel"], ["Python"])
    qualification = qualification_match(["Bachelor's degree"], ["Bachelor's degree"])
    experience = experience_match(7, None, 5)
    summary = build_summary(calculate_overall_match(skill.percentage, qualification.percentage, experience.percentage), skill, qualification, experience)
    summary_bis = build_summary(calculate_overall_match(skill.percentage, qualification.percentage, experience.percentage), skill, qualification, experience)
    assert summary == summary_bis
    assert "Candidate experience exceeds the required maximum." in summary