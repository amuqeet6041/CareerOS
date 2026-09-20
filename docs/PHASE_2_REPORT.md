# Phase 2 Report — Deterministic Matching Engine

## Objective
Build the first production-quality **deterministic** matching engine that
compares a user's stored resume/profile against a Job and returns Skill Match
%, Qualification Match %, Experience Match %, Overall Match %, matched/missing
skills and qualifications, an experience assessment, and a human-readable
explanation — with no LLM, no external job APIs, and no misleading scores when
information is missing.

## What Was Implemented
- A pure calculation layer: `backend/app/services/matching_engine.py`
  (deterministic functions only, no database access, no AI).
- A thin orchestration layer: `backend/app/services/matching_service.py` builds
  a normalized `CandidateProfile` from the stored resume and runs the engine
  against a job (legacy placeholder functions are preserved for backward
  compatibility).
- A response schema: `backend/app/schemas/matching.py`.
- An authenticated endpoint: **`GET /api/jobs/{job_id}/match`**.
- 52 new tests (`tests/test_matching_engine.py`, `tests/test_job_match_api.py`);
  all existing Phase 0/1 tests still pass.

## Matching Architecture
```
Stored resume ──► CandidateProfile (skills, qualifications, experience_years)
Job listing ──► required skill/qualification display names + min/max exp
        │
        ▼
matching_engine.match_candidate_to_job(...)   (pure & deterministic)
        │
SkillMatchResult │ QualificationMatchResult │ ExperienceMatchResult │ summary
        ▼
JobMatchResult ──► GET /api/jobs/{id}/match (auth; caller's own resume only)
```
Normalization reuses `app/utils/job_fields.py::normalize_skill` /
`normalize_qualification` (lowercase + strip + inner-whitespace collapse). No
synonym dictionary; string-level normalized equality only.

## Skill Matching
`Skill Match % = matched required skills / total required skills × 100`.
Case/whitespace-insensitive, deduplicated on both sides. `matched_skills` /
`missing_skills` carry the job's display names. Empty job requirements →
`null` (unknown), never a fabricated 100.

## Qualification Matching
`Qualification Match % = matched required qualifications / total required
qualifications × 100`. Candidate qualification tokens come only from stored
data: each education entry's `degree`, `field_of_study`, combined
`"{degree} in {field_of_study}"`, and each certification's name. Nothing is
invented. Empty job requirements → `null`.

## Experience Matching
Uses the job's `minimum_experience_years` / `maximum_experience_years`:

| Situation | Score | Status |
| --- | --- | --- |
| Job has no min and no max | `null` | `no_requirement` |
| Candidate years unknown | `null` | `unknown` (never assumed 0) |
| `min ≤ years ≤ max` | 100 | `meets_requirement` |
| Below min | `years/min × 100` | `below_minimum` |
| Above max | `max/years × 100` | `above_maximum` |

**Known limitation:** the current resume schema stores company/title/description
but **no employment dates**, so candidate experience years cannot be derived
deterministically. Phase 2 returns the experience component as `unknown`
(`null`). The rules above are fully unit-tested and become live once the resume
model captures durations (future phase, likely with Phase 3 resume
intelligence).

## Overall Score
```
Overall Match % = skill×0.50 + qualification×0.30 + experience×0.20
```
Weights are constants in `matching_engine.py`
(`SKILL_WEIGHT`/`QUALIFICATION_WEIGHT`/`EXPERIENCE_WEIGHT`) and exposed in the
response as `component_weights: {"skill": 50, "qualification": 30, "experience": 20}`.

## Unknown Data Handling
Three states are kept distinct:
1. **`null` (unknown)** — the job has **no requirement** for a component
   (no required skills/qualifications, no experience range).
2. **0** — the candidate has data but nothing matches the (existing)
   requirement; this is evidence-based.
3. **404** — the user has no resume at all; no fabricated scores are ever
   returned.

When a component is unknown it is excluded from the overall score and its
weight is redistributed over the known components; overall is `null` when all
components are unknown. This policy is documented in `docs/ARCHITECTURE.md` and
ensures the system never produces misleading certainty.

## API
`GET /api/jobs/{job_id}/match` — **authentication required**.

| Scenario | Behavior |
| --- | --- |
| Unauthenticated | `401` (from `get_current_user`) |
| Job does not exist | `404` `"Job not found"` |
| User has no resume | `404` `"No resume uploaded yet. Upload a resume before requesting a match."` |
| Valid auth + job (any resume state) | `200` full `JobMatchResponse` with `null` components where unknown/inapplicable |

Example response (abridged):
```json
{
  "job_id": 123,
  "skill_match_percentage": 80.0,
  "qualification_match_percentage": 66.67,
  "experience_match_percentage": null,
  "overall_match_percentage": 80.0,
  "matched_skills": ["Python", "SQL", "Pandas", "Power BI"],
  "missing_skills": ["Tableau"],
  "matched_qualifications": ["Bachelor's degree"],
  "missing_qualifications": ["Master's degree"],
  "experience_status": "unknown",
  "candidate_experience_years": null,
  "minimum_required_years": 2,
  "maximum_required_years": null,
  "component_weights": {"skill": 50, "qualification": 30, "experience": 20},
  "summary": "Strong match. Missing required skills: Tableau."
}
```
The legacy `POST /api/matching` placeholder and its placeholder functions
(`calculate_skill_match`/`calculate_qualification_match`) remain unchanged for
backward compatibility.

## Tests
- **Before Phase 2:** 104 passing.
- **After Phase 2:** 156 passing (52 new, 0 failures, 0 weakened/removed).
- New coverage: skill normalization (case/whitespace/duplicates); skill
  matching (100/0/partial/duplicates/no-requirements/empty candidates);
  qualification matching (complete/partial/none/case/duplicates/no-requirements/
  no candidate data); experience (no-requirement/exact/above/below/max boundary/
  zero years/unknown); overall (weighting, 0–100 bounds, decimals, unknown
  redistribution); summary determinism; API (401/404 no-job/404 no-resume/
  valid/incomplete/no-requirements/own-resume isolation/certifications).

## Verification
1. **Backend suite:** `python -m pytest -q` → `156 passed`.
2. **Migrations:** `"No database migration required for Phase 2."` — no schema
   change was needed; match scores are computed on demand and never persisted.
3. **API smoke:** exercised the new endpoint through the full FastAPI test
   client (401, 404s, valid match, no-requirements, incomplete resume).
4. **Frontend build:** `npm run build` — pending final report (no UI changes
   were made; Phase 2 responses are backward-compatible contracts).

## Files Changed
**Created**
- `backend/app/services/matching_engine.py`
- `backend/app/schemas/matching.py`
- `backend/tests/test_matching_engine.py`
- `backend/tests/test_job_match_api.py`
- `docs/PHASE_2_REPORT.md`

**Modified**
- `backend/app/services/matching_service.py` (kept legacy functions; added
  `build_candidate_profile`, `match_resume_to_job`)
- `backend/app/api/routes/jobs.py` (added `GET /{job_id}/match`)
- `docs/ARCHITECTURE.md` (Matching Engine section)
- `docs/DEVELOPMENT_ROADMAP.md` (Phase 2 complete)
- `README.md` (status + implemented list)

## Known Limitations
- Candidate experience years cannot be derived because the resume schema does
  not store employment dates; the experience component is `unknown` until a
  future phase captures durations.
- Qualification matching is exact normalized-string equality: no degree-level
  thesaurus, so `"B.Sc"` vs `"Bachelor of Science"` won't match. Synonym and
  semantic handling is deferred to the AI phase.
- Summary language is fixed-template English only (no localization).
- Scores are computed per request; no caching and no persistence (intentional).
- Live/external job providers remain out of scope (demo provider only).

## Next Phase
**Phase 3 — AI Resume Intelligence.** Connect an LLM provider while preserving
this deterministic core: richer resume extraction (including experience
durations), skill/qualification synonym semantics that can feed back into the
engine, and tailored match explanations. The Phase 2 engine remains the
deterministic fallback/ground truth.