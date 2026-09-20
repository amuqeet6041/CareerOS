"""
Deterministic matching engine (pure calculation layer).

Compares a normalized candidate profile against a job's requirements and
returns skill / qualification / experience / overall match percentages plus
matched & missing items and a human-readable summary.

Design rules:

- No LLM, no randomness, no external calls. Every result is a pure function of
  its inputs so scores are reproducible and unit-testable.
- Normalization is case-insensitive and whitespace-tolerant (reuses
  :func:`app.utils.job_fields.normalize_skill` / ``normalize_qualification``).
  No synonym/thesaurus dictionary is used; "Power BI" and "power bi" are the
  same skill, while "B.Sc" and "Bachelor of Science" are *not* treated as equal.
- A component score is ``None`` (unknown) when the **job has no requirement**
  for it (no required skills, no required qualifications, no experience
  requirement). This deliberately distinguishes "candidate meets all required
  skills" (a real 100%) from "job lists no skills" (unknown, not 100).
- When the candidate has data but no matching items (e.g. candidate skills that
  match none of the required skills), the score is a real 0 -- that is
  evidence-based, not missing information.
- Candidate experience years are ``None`` in Phase 2 because the resume schema
  does not store employment dates; that component is therefore returned as
  "unknown" rather than a fabricated score.
"""

from dataclasses import dataclass

from app.utils.job_fields import normalize_qualification, normalize_skill

SKILL_WEIGHT = 0.50
QUALIFICATION_WEIGHT = 0.30
EXPERIENCE_WEIGHT = 0.20

# Nominal weights exposed in the API so clients can see how the overall score
# is produced. When a component is unknown its weight is redistributed across
# the known components (see ``calculate_overall_match``).
COMPONENT_WEIGHTS_PERCENT = {
    "skill": round(SKILL_WEIGHT * 100),
    "qualification": round(QUALIFICATION_WEIGHT * 100),
    "experience": round(EXPERIENCE_WEIGHT * 100),
}

# Experience status strings returned by the engine.
EXPERIENCE_STATUS_UNKNOWN = "unknown"
EXPERIENCE_STATUS_NO_REQUIREMENT = "no_requirement"
EXPERIENCE_STATUS_MEETS = "meets_requirement"
EXPERIENCE_STATUS_BELOW_MINIMUM = "below_minimum"
EXPERIENCE_STATUS_ABOVE_MAXIMUM = "above_maximum"


@dataclass
class SkillMatchResult:
    """Result of comparing candidate skills against the job's required skills."""

    percentage: float | None
    matched_skills: list[str]
    missing_skills: list[str]


@dataclass
class QualificationMatchResult:
    """Result of comparing candidate qualifications against job requirements."""

    percentage: float | None
    matched_qualifications: list[str]
    missing_qualifications: list[str]


@dataclass
class ExperienceMatchResult:
    """Result of the deterministic experience comparison."""

    percentage: float | None
    status: str
    candidate_experience_years: float | None
    minimum_required_years: float | None
    maximum_required_years: float | None


@dataclass
class CandidateProfile:
    """Normalized candidate information the engine operates on.

    ``qualifications`` is a pre-derived list of qualification tokens (degrees,
    fields of study, certification names) built from the stored resume data by
    the service layer -- the engine never invents qualifications.
    """

    skills: list[str]
    qualifications: list[str]
    experience_years: float | None = None


@dataclass
class JobMatchResult:
    """Complete deterministic match result for a single (candidate, job) pair."""

    skill_match_percentage: float | None
    qualification_match_percentage: float | None
    experience_match_percentage: float | None
    overall_match_percentage: float | None
    matched_skills: list[str]
    missing_skills: list[str]
    matched_qualifications: list[str]
    missing_qualifications: list[str]
    experience_status: str | None
    candidate_experience_years: float | None
    minimum_required_years: float | None
    maximum_required_years: float | None
    summary: str


def _dedupe_normalized(values: list[str], normalizer) -> dict[str, str]:
    """Map each normalized key to its first-seen display value.

    Keeps matching deterministic and duplicate-safe ("Python" and "python" from
    the same list collapse to one key) while preserving a usable display name.
    """
    seen: dict[str, str] = {}
    for value in values:
        key = normalizer(value)
        if key and key not in seen:
            seen[key] = value
    return seen


def skill_match(user_skills: list[str], job_required_skills: list[str]) -> SkillMatchResult:
    """Skill Match % = matched required skills / total required skills * 100."""
    required = _dedupe_normalized(job_required_skills, normalize_skill)
    if not required:
        return SkillMatchResult(percentage=None, matched_skills=[], missing_skills=[])
    candidate = {normalize_skill(skill) for skill in user_skills if normalize_skill(skill)}
    matched = [display for key, display in required.items() if key in candidate]
    missing = [display for key, display in required.items() if key not in candidate]
    percentage = round((len(matched) / len(required)) * 100, 2)
    return SkillMatchResult(percentage=percentage, matched_skills=matched, missing_skills=missing)


def qualification_match(
    candidate_qualifications: list[str],
    job_required_qualifications: list[str],
) -> QualificationMatchResult:
    """Qualification Match % = matched required qualifications / total * 100."""
    required = _dedupe_normalized(job_required_qualifications, normalize_qualification)
    if not required:
        return QualificationMatchResult(
            percentage=None, matched_qualifications=[], missing_qualifications=[]
        )
    candidate = {
        normalize_qualification(q) for q in candidate_qualifications if normalize_qualification(q)
    }
    matched = [display for key, display in required.items() if key in candidate]
    missing = [display for key, display in required.items() if key not in candidate]
    percentage = round((len(matched) / len(required)) * 100, 2)
    return QualificationMatchResult(
        percentage=percentage, matched_qualifications=matched, missing_qualifications=missing
    )


def experience_match(
    candidate_experience_years: float | None,
    minimum_required_years: float | None,
    maximum_required_years: float | None,
) -> ExperienceMatchResult:
    """Compare candidate experience to the job's min/max experience window.

    Deterministic rule (documented in docs/ARCHITECTURE.md):

    - No min and no max  -> "no_requirement"  (unknown, score ``None``).
    - Candidate years unknown -> "unknown" (never assumed to be zero).
    - ``min <= candidate <= max`` -> 100%, status "meets_requirement".
    - Below minimum -> ``candidate / minimum * 100`` (min > 0), "below_minimum".
    - Above maximum -> ``maximum / candidate * 100``, "above_maximum".
    """
    if minimum_required_years is None and maximum_required_years is None:
        return ExperienceMatchResult(
            percentage=None,
            status=EXPERIENCE_STATUS_NO_REQUIREMENT,
            candidate_experience_years=candidate_experience_years,
            minimum_required_years=minimum_required_years,
            maximum_required_years=maximum_required_years,
        )

    if candidate_experience_years is None:
        return ExperienceMatchResult(
            percentage=None,
            status=EXPERIENCE_STATUS_UNKNOWN,
            candidate_experience_years=None,
            minimum_required_years=minimum_required_years,
            maximum_required_years=maximum_required_years,
        )

    candidate = max(0.0, candidate_experience_years)

    if minimum_required_years is not None and candidate < minimum_required_years:
        percentage = 0.0 if minimum_required_years == 0 else max(
            0.0, round((candidate / minimum_required_years) * 100, 2)
        )
        status = EXPERIENCE_STATUS_BELOW_MINIMUM
    elif maximum_required_years is not None and candidate > maximum_required_years:
        percentage = max(0.0, round((maximum_required_years / candidate) * 100, 2))
        status = EXPERIENCE_STATUS_ABOVE_MAXIMUM
    else:
        percentage = 100.0
        status = EXPERIENCE_STATUS_MEETS

    return ExperienceMatchResult(
        percentage=percentage,
        status=status,
        candidate_experience_years=candidate_experience_years,
        minimum_required_years=minimum_required_years,
        maximum_required_years=maximum_required_years,
    )


def calculate_overall_match(
    skill_percentage: float | None,
    qualification_percentage: float | None,
    experience_percentage: float | None,
) -> float | None:
    """Weighted overall score (skill 50%, qualification 30%, experience 20%).

    Unknown components are excluded and their weight is redistributed over the
    known components so scores never pretend certainty (`None` if nothing is
    known at all).
    """
    known = []
    for weight, percentage in (
        (SKILL_WEIGHT, skill_percentage),
        (QUALIFICATION_WEIGHT, qualification_percentage),
        (EXPERIENCE_WEIGHT, experience_percentage),
    ):
        if percentage is not None:
            known.append((weight, percentage))

    if not known:
        return None

    total_weight = sum(weight for weight, _ in known)
    score = sum((weight * percentage for weight, percentage in known), 0.0) / total_weight
    return round(score, 2)


def _overall_bucket(overall: float) -> str:
    if overall >= 80:
        return "Strong match."
    if overall >= 60:
        return "Good match."
    if overall >= 40:
        return "Moderate match."
    if overall >= 20:
        return "Weak match."
    return "Poor match."


def build_summary(
    overall_match_percentage: float | None,
    skill_result: SkillMatchResult,
    qualification_result: QualificationMatchResult,
    experience_result: ExperienceMatchResult,
) -> str:
    """Deterministic, human-readable summary assembled from fixed rules.

    No LLM and no random phrasing; the same inputs always produce the same
    sentences.
    """
    parts: list[str] = []
    if overall_match_percentage is None:
        parts.append("Insufficient information to compute an overall match score.")
    else:
        parts.append(_overall_bucket(overall_match_percentage))

    if skill_result.missing_skills:
        parts.append(f"Missing required skills: {', '.join(skill_result.missing_skills)}.")
    if qualification_result.missing_qualifications:
        parts.append(
            f"Missing required qualifications: "
            f"{', '.join(qualification_result.missing_qualifications)}."
        )

    if experience_result.status == EXPERIENCE_STATUS_BELOW_MINIMUM:
        parts.append("Candidate experience is below the required minimum.")
    elif experience_result.status == EXPERIENCE_STATUS_ABOVE_MAXIMUM:
        parts.append("Candidate experience exceeds the required maximum.")

    if (
        overall_match_percentage is None
        and not skill_result.missing_skills
        and not qualification_result.missing_qualifications
    ):
        parts.append("Upload a resume with skills and qualifications to get a match assessment.")

    return " ".join(parts)


def match_candidate_to_job(
    profile: CandidateProfile,
    job_required_skills: list[str],
    job_required_qualifications: list[str],
    minimum_experience_years: float | None = None,
    maximum_experience_years: float | None = None,
) -> JobMatchResult:
    """Run the full deterministic matching pipeline and build the summary."""
    skill = skill_match(profile.skills, job_required_skills)
    qualification = qualification_match(profile.qualifications, job_required_qualifications)
    experience = experience_match(
        profile.experience_years,
        minimum_experience_years,
        maximum_experience_years,
    )
    overall = calculate_overall_match(
        skill.percentage, qualification.percentage, experience.percentage
    )

    return JobMatchResult(
        skill_match_percentage=skill.percentage,
        qualification_match_percentage=qualification.percentage,
        experience_match_percentage=experience.percentage,
        overall_match_percentage=overall,
        matched_skills=skill.matched_skills,
        missing_skills=skill.missing_skills,
        matched_qualifications=qualification.matched_qualifications,
        missing_qualifications=qualification.missing_qualifications,
        experience_status=experience.status,
        candidate_experience_years=experience.candidate_experience_years,
        minimum_required_years=experience.minimum_required_years,
        maximum_required_years=experience.maximum_required_years,
        summary=build_summary(overall, skill, qualification, experience),
    )