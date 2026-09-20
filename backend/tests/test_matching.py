from app.services.matching_service import (
    calculate_qualification_match,
    calculate_skill_match,
)


def test_calculate_skill_match_no_overlap():
    result = calculate_skill_match(user_skills=["python"], job_required_skills=["java"])
    assert result == 0.0


def test_calculate_skill_match_full_overlap():
    result = calculate_skill_match(user_skills=["python", "sql"], job_required_skills=["python", "sql"])
    assert result == 100.0


def test_calculate_skill_match_partial_overlap():
    result = calculate_skill_match(
        user_skills=["Python", "SQL"],
        job_required_skills=["python", "java", "rest"],
    )
    assert result == round((1 / 3) * 100, 2)


def test_calculate_skill_match_case_insensitive():
    result = calculate_skill_match(user_skills=["PYTHON"], job_required_skills=["python"])
    assert result == 100.0


def test_calculate_skill_match_ignores_empty_requirements():
    assert calculate_skill_match(user_skills=["python"], job_required_skills=[]) == 0.0


def test_calculate_qualification_match_no_overlap():
    result = calculate_qualification_match(
        user_education=["bachelor"],
        job_required_education=["master"],
    )
    assert result == 0.0


def test_calculate_qualification_match_partial_overlap():
    result = calculate_qualification_match(
        user_education=["bachelor", "master"],
        job_required_education=["bachelor", "phd"],
    )
    assert result == 50.0


def test_calculate_qualification_match_full_overlap():
    result = calculate_qualification_match(
        user_education=["bachelor"],
        job_required_education=["bachelor"],
    )
    assert result == 100.0


def test_calculate_qualification_match_ignores_empty_requirements():
    assert calculate_qualification_match(
        user_education=["bachelor"],
        job_required_education=[],
    ) == 0.0