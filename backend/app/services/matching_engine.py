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
  On top of that, matching uses small, fixed equivalence rules so common
  resume spellings line up with job requirements: punctuation/spacing variants
  ("PowerBI" = "Power BI", "React.js" = "React"), a short alias table
  ("MS Excel" = "Excel"), implied skills ("MySQL" also counts as "SQL"), and
  degree parsing ("BS in Computer Science" satisfies "Bachelor's in Computer
  Science"; a higher degree in the same field also satisfies it). The rules
  are static tables, so results stay deterministic.
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

import re
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


# Compact skill key (lowercase, no punctuation/spaces) -> canonical compact key.
_SKILL_ALIASES = {
    "msexcel": "excel",
    "microsoftexcel": "excel",
    "advancedexcel": "excel",
    "excelspreadsheets": "excel",
    "python3": "python",
    "js": "javascript",
    "es6": "javascript",
    "ecmascript": "javascript",
    "ts": "typescript",
    "html5": "html",
    "css3": "css",
    "rest": "restapis",
    "restapi": "restapis",
    "restful": "restapis",
    "restfulapi": "restapis",
    "restfulapis": "restapis",
    "ml": "machinelearning",
    "datavisualisation": "datavisualization",
    "dataviz": "datavisualization",
    "msword": "word",
    "microsoftword": "word",
    "mspowerpoint": "powerpoint",
    "microsoftpowerpoint": "powerpoint",
    "microsoftpowerbi": "powerbi",
    "postgres": "postgresql",
    "golang": "go",
}

# Candidate skills that also demonstrate a more general required skill.
_SKILL_IMPLIES = {
    "mysql": ("sql",),
    "postgresql": ("sql",),
    "mssql": ("sql",),
    "sqlserver": ("sql",),
    "microsoftsqlserver": ("sql",),
    "tsql": ("sql",),
    "plsql": ("sql",),
    "sqlite": ("sql",),
    "oraclesql": ("sql",),
    "typescript": ("javascript",),
    "react": ("javascript",),
    "django": ("python",),
    "flask": ("python",),
    "fastapi": ("python",),
    "pandas": ("python",),
}

_SKILL_QUALIFIER_SUFFIX = re.compile(r"\s+(?:fundamentals|basics)$")
# "react.js" / "reactjs" -> "react"; "node.js" -> "node". Applied to both the
# candidate and the job side, so the stripping is symmetric.
_JS_SUFFIX = re.compile(r"(?<=[a-z])js$")


def skill_match_key(skill: str) -> str:
    """Matching key for a skill: tolerant of punctuation, spacing, a few common
    aliases, and ".js" suffixes. "C++" and "C#" stay distinct from "C"."""
    text = normalize_skill(skill)
    if not text:
        return ""
    text = text.replace("c++", "cplusplus").replace("c#", "csharp").replace("&", "and")
    text = _SKILL_QUALIFIER_SUFFIX.sub("", text)
    compact = re.sub(r"[^a-z0-9]", "", text)
    compact = _SKILL_ALIASES.get(compact, compact)
    if compact not in _SKILL_ALIASES.values():
        compact = _JS_SUFFIX.sub("", compact) or compact
    return compact


def _candidate_skill_keys(user_skills: list[str]) -> set[str]:
    keys = {skill_match_key(skill) for skill in user_skills}
    keys.discard("")
    for key in list(keys):
        keys.update(_SKILL_IMPLIES.get(key, ()))
    return keys


def skill_match(user_skills: list[str], job_required_skills: list[str]) -> SkillMatchResult:
    """Skill Match % = matched required skills / total required skills * 100."""
    required = _dedupe_normalized(job_required_skills, skill_match_key)
    if not required:
        return SkillMatchResult(percentage=None, matched_skills=[], missing_skills=[])
    candidate = _candidate_skill_keys(user_skills)
    matched = [display for key, display in required.items() if key in candidate]
    missing = [display for key, display in required.items() if key not in candidate]
    percentage = round((len(matched) / len(required)) * 100, 2)
    return SkillMatchResult(percentage=percentage, matched_skills=matched, missing_skills=missing)


_BACHELOR, _MASTER, _DOCTORATE = 1, 2, 3

# Compact degree text -> level.
_DEGREE_LEVELS = {
    **dict.fromkeys(
        (
            "bachelor", "bachelors", "bachelorsdegree", "bachelordegree",
            "undergraduate", "undergraduatedegree", "bs", "bsc", "ba", "be",
            "beng", "btech", "bba", "bcs", "bscs", "bsse", "bsit", "bcom",
            "bachelorofscience", "bachelorofarts", "bachelorofengineering",
            "bacheloroftechnology", "bachelorofbusinessadministration",
            "bachelorofcommerce", "bachelorofcomputerscience",
        ),
        _BACHELOR,
    ),
    **dict.fromkeys(
        (
            "master", "masters", "mastersdegree", "masterdegree", "ms", "msc",
            "ma", "mba", "meng", "mtech", "mphil", "mcs", "mscs", "mcom",
            "masterofscience", "masterofarts", "masterofengineering",
            "masterofbusinessadministration", "masterofphilosophy",
        ),
        _MASTER,
    ),
    **dict.fromkeys(("phd", "doctorate", "doctoral", "doctorofphilosophy"), _DOCTORATE),
}

# Degree abbreviations that already name a field.
_DEGREE_IMPLIED_FIELD = {
    "bscs": "computerscience",
    "mscs": "computerscience",
    "bcs": "computerscience",
    "mcs": "computerscience",
    "bachelorofcomputerscience": "computerscience",
    "bsse": "softwareengineering",
    "bsit": "informationtechnology",
    "bba": "businessadministration",
    "mba": "businessadministration",
}

_FIELD_ALIASES = {
    "cs": "computerscience",
    "se": "softwareengineering",
    "it": "informationtechnology",
    "ai": "artificialintelligence",
}


def _compact(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text)


def _parse_qualification(key: str) -> tuple[int | None, str | None]:
    """Split a normalized qualification into ``(degree level, field)``.

    "bachelor's in computer science" -> (1, "computerscience");
    "bs" -> (1, None); "computer science" -> (None, "computerscience").
    Anything that is not recognizably a degree and/or field still yields a
    field-only key, which only matches an equal field.
    """
    text = re.sub(r"\([^)]*\)", " ", key).replace("&", "and")
    degree_part, sep, field_part = text.partition(" in ")
    if not sep:
        # "BS Computer Science" (no "in"): try the leading word as a degree.
        head, _, rest = text.strip().partition(" ")
        if _compact(head) in _DEGREE_LEVELS and rest:
            degree_part, field_part = head, rest
        else:
            degree_part, field_part = text, ""

    degree = _compact(degree_part.replace("degree", ""))
    level = _DEGREE_LEVELS.get(degree)
    if level is None:
        # Not a degree after all: the whole string is a field of study.
        field = _compact(text)
        return None, _FIELD_ALIASES.get(field, field) or None

    field = _compact(field_part)
    field = _FIELD_ALIASES.get(field, field) or _DEGREE_IMPLIED_FIELD.get(degree)
    return level, field or None


def _fields_match(required: str, candidate: str) -> bool:
    if required == candidate:
        return True
    # "Economics and Data Science" covers "Data Science".
    return len(required) >= 6 and required in candidate


def _degree_requirement_met(
    required: tuple[int | None, str | None],
    candidates: list[tuple[int | None, str | None]],
) -> bool:
    """A required degree is met by a candidate degree of the same or higher
    level in a matching field (the field is skipped when the job names none)."""
    req_level, req_field = required
    if req_level is None:
        return False  # Field-only / unrecognized requirements need an exact match.
    for level, field in candidates:
        if level is None or level < req_level:
            continue
        if req_field is None or (field is not None and _fields_match(req_field, field)):
            return True
    return False


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
    parsed_candidate = [_parse_qualification(q) for q in candidate]

    def satisfied(key: str) -> bool:
        return key in candidate or _degree_requirement_met(
            _parse_qualification(key), parsed_candidate
        )

    matched = [display for key, display in required.items() if satisfied(key)]
    missing = [display for key, display in required.items() if not satisfied(key)]
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