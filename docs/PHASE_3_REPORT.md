# Phase 3 Report — AI Resume Intelligence

## Objective
Layer **provider-agnostic AI structured extraction** on top of the deterministic
resume parser: enrich skills/education/certifications/experience (with
employment dates) from raw resume text, derive a deterministic total-experience
figure that the Phase 2 matching engine can finally score, and retry failed AI
analyses — without letting AI ever compute scores, break an upload, invent data,
or leak resume text/keys.

## What Was Implemented

### New files
- `backend/app/services/ai/__init__.py` — package exports (typed errors).
- `backend/app/services/ai/base.py` — `AIProvider` interface + typed errors
  (`AIConfigurationError`, `AIRequestError`, `AIOutputError`).
- `backend/app/services/ai/schemas.py` — `AIResumeExtraction` + `AIEducation` /
  `AICertification` / `AIExperience`; strict `YYYY-MM` date normalization.
- `backend/app/services/ai/prompts.py` — JSON-only prompt; forbids scoring,
  guessing, and out-of-text claims; `truncate_resume_text` head-truncation.
- `backend/app/services/ai/provider.py` — `get_ai_provider()` factory,
  `OpenAICompatibleProvider` (httpx → `/chat/completions`,
  `response_format: json_object`), `MockAIProvider` (dev/tests),
  `parse_json_payload` (never evals).
- `backend/app/services/ai/pipeline.py` — `run_resume_analysis(raw_text)` →
  `(structured | None, status)`; `structured_to_persist` (dedupe + duration).
- `backend/app/services/experience_duration.py` — deterministic month/year math.
- `backend/alembic/versions/c821c44ae290_phase3_resume_ai.py` — reversible
  migration (down_revision `bf773dd3d573`).
- `backend/tests/test_experience_duration.py`, `backend/tests/test_ai_resume_pipeline.py`.
- `docs/PHASE_3_REPORT.md` (this report).

### Modified files
- `backend/app/core/config.py` — AI settings + production fail-fast validator.
- `backend/app/models/resume.py` — `Resume.total_experience_years` &
  `analysis_status`; `Education` nullable `institution` + `start_year`/
  `end_year`; `Experience.location/start_date/end_date/currently_employed`;
  `Certification.issue_year/expiry_year`.
- `backend/app/services/resume_service.py` — shared `_rebuild_children`,
  `analysis_status`/`structured` on `save_resume`, new `update_resume_analysis`.
- `backend/app/schemas/resume.py` — new output fields.
- `backend/app/api/routes/resume.py` — AI upload + `POST /api/resume/analyze`.
- `backend/app/services/matching_service.py` — `build_candidate_profile` now
  reads `resume.total_experience_years`.
- `backend/app/services/ai_service.py` — deprecated legacy placeholder.
- `backend/.env.example`, `.env.example` — AI variables documented.
- `frontend/components/resume/ExperienceList.jsx` — dates/location display;
  `frontend/components/resume/ResumeAnalysis.jsx` — total-experience + status.
- `docs/ARCHITECTURE.md`, `docs/DEVELOPMENT_ROADMAP.md`, `README.md`.

## AI Architecture
```
Raw resume text (deterministic parser output)
      │
      ▼
pipeline.run_resume_analysis(text) ─────────► get_ai_provider()
      │                                        ├─ None (AI disabled)   → "parsed"
      │                                        ├─ OpenAICompatibleProvider
      │                                        └─ MockAIProvider (dev/tests)
      ▼
provider.extract_resume_information(text) ──► typed AIProviderError OR dict
      │
      ▼
AIResumeExtraction.model_validate(payload) ──► ValidationError OR model
      │
      ▼
structured_to_persist()  (skill dedupe by matching engine's normalize_skill;
                          deterministic total_experience_years; no model math)
      │
      ▼
resume_service.save_resume(..., analysis_status, structured) / update_resume_analysis
```
- Providers return raw JSON objects only; the pipeline always validates before
  persisting and never trusts the model for numbers (experience years are
  computed locally by `experience_duration.py`).
- The prompt includes no job data, so the model cannot tailor output to any
  employer; extraction is kept word-for-word (`Power BI` stays `Power BI`).

## Schema Change (migration `c821c44ae290`)
| Table | Change |
| --- | --- |
| `resumes` | `+ total_experience_years` (Float, nullable), `+ analysis_status` (String, `"parsed"` default) |
| `education` | `institution` → nullable; `+ start_year`, `+ end_year` (Integer) |
| `experience` | `+ location`, `+ start_date`, `+ end_date` (String `YYYY-MM`), `+ currently_employed` (Bool, default false) |
| `certifications` | `+ issue_year`, `+ expiry_year` (Integer) |

Verified on fresh SQLite: `alembic upgrade head` and `alembic downgrade -1`
both apply cleanly (batch-mode ops, PostgreSQL-safe). The existing
`tests/test_migrations.py` (expected-table check) still passes.

## Experience-Duration Policy (`experience_duration.py`)
- Start month inclusive, end month exclusive: `2024-01 → 2025-01` = exactly
  12 months = 1.0 year.
- `currently_employed` runs through the current month; future end dates are
  clamped to the current month.
- Overlapping/adjacent jobs are merged (no double counting).
- If ANY job's interval is unreliable (missing/malformed start or non-current
  end, end before start, future start) the total is `None`. Zero jobs → `None`.
  Unknown never becomes zero.
- Years = merged months / 12, rounded to 2 decimals.

## Matching Integration
`matching_service.build_candidate_profile` now sets
`experience_years = resume.total_experience_years`. When AI supplies dated
experience, the Phase 2 engine scores
`Experience Match % = 100` for jobs with `min ≤ years ≤ max`, instead of the
Phase 2 unknown. AI strictly supplies candidate *data*; all scoring rules and
weights (50/30/20) remain the deterministic engine's.

## API Changes
- `POST /api/resume/upload` — runs `run_resume_analysis` after parsing;
  response gains `analysis_status` and `total_experience_years`.
- `POST /api/resume/analyze` (new, auth-required) — re-runs AI on the stored
  `raw_text`; on AI failure the existing children + total are preserved, only
  the status changes to `ai_failed`; 404 when the user has no resume.
- `GET /api/resume/analysis` — unchanged contract, new fields.
- Existing `GET /api/jobs/{id}/match` and legacy `POST /api/matching` contracts
  are unchanged.

## Error Handling (fallback chain)
Every failure degrades to the deterministic parse with `analysis_status =
"ai_failed"` and a 201 successful upload: missing/invalid provider config,
timeout, network error, invalid key, rate limit, non-200, non-JSON body,
schema-invalid payload, out-of-range dates, and unexpected provider exceptions
(row 34 of `pipeline.py`). Only the error *category* is logged (with full
traceback for unexpected errors); no secrets are logged at any level.

## Privacy
- Resume text, prompts (system/user messages), provider responses, and API keys
  are never logged (confirmed by tests that assert an error message containing a
  fake key does not appear in the upload response or logs).
- No resume/gateway data is sent to employers; the API never writes prompts or
  raw AI responses into the DB (only validated extraction).
- Production fails startup on `AI_PROVIDER` without `AI_API_KEY` and refuses
  the `mock` provider; `AI_PROVIDER=mock` is dev/test-only.

## Tests (212 total, all passing)
- 156 pre-existing tests unchanged and green.
- 22 new duration tests (`test_experience_duration.py`): exact-year, same-month,
  end-month-exclusive, current/below/future-start jobs, overlap and adjacency
  merging, future-end clamping, full unknown policy, month parsing, rounding.
- 34 new AI tests (`test_ai_resume_pipeline.py`): extraction persistence,
  skill dedupe + display spelling, empty/null payloads, invalid dates, unknown
  totals, provider unit tests (timeout/429/malformed body, config validation),
  JSON-payload parsing without eval, endpoint integration (disabled/failed/
  retry/preserve-on-failure), auth + own-resume scoping, secret-leak guards,
  and matching-engine integration (AI skills + dated experience → 100% scores,
  `candidate_experience_years` populated).

## Verification
- Backend: `pytest -q` → **212 passed, 0 failed**.
- Migration: `upgrade head` + `downgrade -1` on fresh SQLite verified; applied
  tables checked via `PRAGMA table_info`.
- Frontend: `npm run build` → success, 17 routes.
- `ai_service.py` retained as a deprecated shim (code references only in docs,
  which were updated).

## Manual AI Smoke Test — SKIPPED
No real AI API key is configured in this environment, and none will be
fabricated. The provider path was exercised end-to-end with the deterministic
`MockAIProvider`; the httpx-based `OpenAICompatibleProvider` is covered by
mocked unit tests (timeout, rate-limit, malformed body). To smoke-test live:
set `AI_PROVIDER=openai` + `AI_API_KEY` (+ optional `AI_MODEL`/`AI_BASE_URL`)
in `backend/.env`, restart uvicorn, upload a resume, and observe
`analysis_status:"ai_analyzed"` with dated experience and a computed
`total_experience_years`.

## Limitations (next phases)
- Education/certification dates are stored as years only (display data);
  nothing depends on them yet.
- `total_experience_years` is recomputed on every upload/analyze from that
  upload's experience rows; manual edits to dates (no edit UI yet) would need a
  recompute endpoint.
- AI extraction quality depends on the provider; `AI_MAX_RESUME_CHARS` truncates
  the head of long resumes (context budget).
- Matching uses exact normalized-string equality still; synonym/degree-level
  semantics remain future work (Phase 6+/explicit AI-driven matching, not this
  phase's scope).

## Next Phase
**Phase 4 — Jobs Frontend**: wire the public and dashboard jobs pages to
`GET /api/jobs` and present match scores (`GET /api/jobs/{id}/match`).