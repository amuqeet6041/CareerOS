"""
Matching service.

Contains modular, easily-extensible logic for computing match percentages
between a user's profile and a job listing. The initial implementation uses
simple set overlap and is NOT a production-grade AI matching score --
replace/extend with NLP or embedding-based similarity later.
"""


def calculate_skill_match(user_skills: list[str], job_required_skills: list[str]) -> float:
    """
    Returns a percentage (0-100) representing how many of the job's required
    skills the user has. Simple placeholder logic based on case-insensitive
    set overlap.
    """
    if not job_required_skills:
        return 0.0

    user_set = {s.strip().lower() for s in user_skills}
    required_set = {s.strip().lower() for s in job_required_skills}

    matched = user_set.intersection(required_set)
    return round((len(matched) / len(required_set)) * 100, 2)


def calculate_qualification_match(user_education: list[str], job_required_education: list[str]) -> float:
    """
    Returns a percentage (0-100) representing qualification match.
    Placeholder logic mirroring calculate_skill_match; refine with real
    qualification-level comparisons (e.g. degree level ordering) later.
    """
    if not job_required_education:
        return 0.0

    user_set = {e.strip().lower() for e in user_education}
    required_set = {e.strip().lower() for e in job_required_education}

    matched = user_set.intersection(required_set)
    return round((len(matched) / len(required_set)) * 100, 2)
