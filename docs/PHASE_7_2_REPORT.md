# PHASE 7.2 REPORT — Resume AI Intelligence Activation & End-to-End Validation

**Status:** COMPLETE
**Date:** 2026-09-21
**Scope:** Activate and validate the full resume-intelligence chain
`upload → deterministic parse → AI analysis → persisted skills/education/
experience/certifications → Career Insights (strengths / skill gaps / career
directions) → deterministic matching`. The Phase 3 AI provider architecture is
kept as-is; the only two changes are a development configuration fix and an
integration test. No API keys were invented, injected, or committed. All live
verification used the **mock AI provider** on a temporary database and clearly
marked as such — the real provider path was verified at the config/test level
and requires the user to supply a live key (see Env Vars & Known Limitations).

---

## 1. Background & Goal

Phase 7.1 reconciled the database schema. The app already had a complete,
Phase-3-built AI service layer (`backend/app/services/ai/`) with an upload API
that auto-triggers AI analysis *when a provider is configured*, a resume
analysis endpoint, a career-insights service/route, a matching engine, and a
frontend that already renders analysis + "Analyze with AI / Retry" controls
(implemented during Phase 7.1). In practice the running app only ever produced
`analysis_status="parsed"` with an empty `skills`/children set, so Career
Insights and matching had nothing to work from. This phase found why and made
the whole chain work end-to-end under a mock provider, with real-provider
configuration verified by tests.

The core question the user asked — *"do I need to provide/configure a real AI
API key?"* — is answered in §4 and §15. **Yes:** to get real AI analysis you set
`AI_PROVIDER=openai` + `AI_API_KEY` in `backend/.env`. Without a key the app
stays deterministic (`parsed`, no extracted skills) by design; a `mock`
provider is available for development/tests only (see §3/§4).

## 2. Root Cause Analysis

The resume that previously uploaded (`backend/careeros.db`, resume id 1,
`username=resume-demo` user) sat in `analysis_status="parsed"` with **zero**
persisted skills, education, experience, or certifications — so Career Insights
produced empty strengths/gaps and matching had no user skills to compare. Chain
of causes (each separately confirmed):

1. **AI disabled in configuration.** `backend/.env` left `AI_PROVIDER` empty.
   `get_ai_provider()` (`backend/app/services/ai/provider.py`) returns `None`
   when no provider is configured, so the upload route's post-parse AI step was
   skipped and the resume was persisted as `parsed` only. The deterministic
   fallback never ran. This is intended behavior (no key → no AI), not a bug —
   the real fix is supplying a provider/key or a dev mock.
2. **Deterministic parser extracted nothing for this particular PDF.**
   `resume_parser.parse_resume` splits on known section headings
   (`SKILLS`, `EDUCATION`, `EXPERIENCE`, `CERTIFICATIONS`, …). The reviewer's
   real CV/PDF used headings the heuristic section matcher did not recognize,
   so all four sections stayed empty at the deterministic tier (0 children on
   resume id 1). The parser, service, and persistence are correct — this is a
   parsing-coverage limitation of the specific document (documented as a known
   limitation; AI extraction is designed to fill this gap).
3. **Config gap found during audit:** `backend/app/core/config.py`'s model
   validator rejected `AI_PROVIDER=mock` in *every* environment, even though the
   provider layer supports (and the docs/tests use) a mock provider for
   development/tests. This contradicted the documented dev/test mock path and
   blocked a key-less local validation. **Fixed** (see §7).

## 3. Required Knowledge: Question "Do I need a real AI API key?"

- **For real AI analysis (production / real deployment): YES.** Set in
  `backend/.env` (the file is git-ignored; never commit it):
  - `AI_PROVIDER=openai` (activates the OpenAI-compatible provider)
  - `AI_API_KEY=<your real key>` (required; validated — production refuses to
    start without it)
  - `AI_MODEL` (optional; default `gpt-4o-mini`)
  - `AI_BASE_URL` (optional; default `https://api.openai.com/v1`)
  Restart the backend, then re-upload or press **"Analyze with AI"** on an
  existing resume.
- **Without any key:** the app stays deterministic (`parsed`, empty children) —
  that is by design and safe; no fake data is ever seeded.
- **For development/tests with no key:** `AI_PROVIDER=mock` is now allowed
  (development/test environments only, after the §7 config fix). This is the
  path used by all live smoke verification below and nothing is seeded into a
  real database.
- No key was invented or committed. `backend/.env.example` documents all
  options with placeholders only.

## 4. Architecture (Phase 3 AI Layer — unchanged)

The Phase 3 pipeline is the single entry point and was kept intact:

- `backend/app/services/ai/base.py` — `AIProvider` protocol, `AIError`,
  `InvalidAnalysisError`.
- `backend/app/services/ai/provider.py` — `get_ai_provider()` factory
  (`None` if `AI_PROVIDER` empty), `OpenAICompatibleProvider`, and
  **`MockAIProvider`** (deterministic, used only in tests/smoke).
- `backend/app/services/ai/pipeline.py` — `run_resume_analysis(raw_text)`
  returns `(extraction_dict | None, error_message)`. Calls `extract_resume_
  information`, builds the `AIResumeExtraction` (pydantic) model,
  `structured_to_persist(...)`, and computes `total_experience_years` from
  parsed experience.
- `backend/app/services/ai/prompts.py`, `backend/app/services/ai/schemas.py`,
  `backend/app/services/ai/career_insights_prompts.py` — prompt building and
  output schemas.
- `backend/app/services/ai_service.py` + `backend/app/services/career_insights_
  service.py` — thin wrappers delegating to the pipeline; the insights service
  builds a deterministic payload and, when AI is available, enriches it
  (`agentic` path) while always falling back to deterministic strengths/gaps/
  directions.

## 5. Resume Analysis Flow (verified end-to-end)

`POST /api/resume/upload` → `resume_parser.parse_resume` (deterministic) →
children (skills/education/experience/certifications) persisted via
`resume_service.save_resume` → **if a provider is configured**, AI analysis is
triggered automatically (`run_resume_analysis`) and
`resume_service.update_resume_analysis` persists the structured AI result and
sets `analysis_status="ai_analyzed"`. `POST /api/resume/analyze` (and the
frontend **"Analyze with AI"** button) is the explicit retry path for resumes
already uploaded without AI. `GET /api/resume/analysis` returns the current
resume with its children and status breframes. The route (`backend/app/api/
routes/resume.py`) is auth-bound and returns the proper status codes
(415/400/422) on malformed uploads.

## 6. Persistence (verified)

- `skills` → `resumes.Skills` rows (name, normalized name; all 5 deduped)
- `education` → `resumes.Education` rows (institution + degree)
- `experience` → `resumes.Experience` rows (title/company/from/to + computed
  months)
- `certifications` → `resumes.Certification` rows
- `Resume.total_experience_years` = 7.17 years (computed from experience spans
  via `experience_duration.calculate_total_experience_years`)
- `Resume.analysis_status` = `ai_analyzed` after AI, `parsed` otherwise
- All rows are bound to `Resume.owner_id`; GET /analysis returns children in
  the same `ResumeOut` shape the frontend renders.

## 7. Changes Made (this phase)

1. `backend/app/core/config.py` — **fixed the mock-provider validator**: allow
   `AI_PROVIDER=mock` for `development`/`test` environments, still refuse it in
   production; correctly enable `AIProvider=mock` returns without an API key at
   validation time. (Comment typo corrected.)
2. `backend/tests/test_ai_resume_pipeline.py` — **added**
   `test_ai_analyzed_resume_feeds_insights_and_matching` — a full
   upload→AI→persist→insights→matching integration test using mock provider.
3. No model, migration, route, service, or frontend changes were required; the
   schema/pipeline/frontend were all audited and already correct.

## 8. Frontend Flow (audited; already fulfilled by Phase 7.1)

`ResumeManager.jsx` — upload card + analysis preview + **"Analyze with AI" /
Retry** button with analyzing loading state; renders the persisted children as
chips/sections and shows a hint when a parsed-but-empty resume is detected.
`useResume.js` — exposes `applyResult` / `retryAnalysis`; `resumeService.js` +
`lib/api.js` — authorized `POST /resume/analyze`, `GET /resume/analysis`.
Career Insights page (`frontend/app/student-dashboard/career-insights/page.js`)
uses `useCareerInsights` → `GET /api/career-insights`, rendering the persisted
strengths/gaps/directions. The Phase 7.1 frontend remediation remains in place
(no regressions; frontend build is green).

## 9. Career Insights Integration (verified)

Deterministic payload is always built from persisted resume children
(strengths = top skills, gaps = missing job-skill coverage, directions = role
suggestions). When AI is configured (`agentic` path), the service delegates to
`generate_career_insights(messages)` and strips results to only skills already
present in the resume (`_trim_ai_insights`), keeping output grounded. If AI
fails, a deterministic fallback is returned — the API never 500s because of AI
(see Known Limitations).

## 10. Matching Integration (verified)

`matching_service.match_resume_to_job` builds `CandidateProfile` from the
persisted AI-extracted skills/experience and `matching_engine` computes skill
match % (normalized intersection), qualification match, experience match, and
an overall score. Because the AI-extracted skills now populate the candidate
profile, job matching operates on real extracted competencies rather than an
empty skills list. Verified by `test_match_uses_ai_extracted_*` and the new
integration test.

## 11. Tests

Targeted (backend directory):

| Command | Result |
| --- | --- |
| `python -m pytest tests/test_ai_resume_pipeline.py -q -k "feeds_insights or matching"` | 2 passed |
| `python -m pytest tests/test_resume.py -q` | passed (upload/parse/persist) |
| `python -m pytest tests/test_ai_resume_pipeline.py -q -k "mock_provider or config or feeds_insights"` | 2 passed |
| `python -m pytest tests/test_ai_resume_pipeline.py -q -k "matching"` | 1 passed, 34 deselected |
| `python -m pytest tests/test_resume.py tests/test_ai_resume_pipeline.py -q` | 50 passed |
| Full micro-backend suite `python -m pytest -q` | 245 passed |
| `python -m alembic check` | No new upgrade operations detected |

Frontend: `npm run build` — green (no TS/lint errors; all 17 routes).

## 12. Live Smoke (MOCK PROVIDER — clearly marked)

A live smoke ran the **entire stack** with the **MockAIProvider** (patched, not
the OpenAI client) over real HTTP on a **temporary SQLite database and a
temporary user** — nothing was written to the dev database:

- register / login → token issued
- upload PDF → `201` returned with `analysis_status="ai_analyzed"`; resume
  persisted with owner_id
- children: 5 skills (`Python`, `SQL`, `Excel`, `Power BI`, `Pandas`),
  education (institution + degree), 2 experience entries, 1 certification
- `Resume.total_experience_years` = 7.17
- `GET /analysis` → `ai_analyzed` + children in response
- `GET /api/career-insights` → strengths/gaps/directions populated (AI status:
  available under mock)
- progression verified through the chain — full PASS.

> **Real-provider live test was NOT run** (no API key is available to the
> assistant; none was invented). The OpenAI-compatible provider path is covered
> by unit/config tests (key required in production; `_chat` returns 200-green
> with a stubbed `httpx`), and only requires the user to set real
> `AI_PROVIDER`/`AI_API_KEY` to go live (§15). This is exactly "MOCK PROVIDER
> TEST vs REAL PROVIDER TEST" — mock marked everywhere, real left for the user
> with creds.

## 13. Environment — AI Configuration Summary

| Key (in `backend/.env`) | Purpose | Default / Example |
| --- | --- | --- |
| `AI_PROVIDER` | `openai` (real), `mock` (dev/test only), empty = disabled | `openai` |
| `AI_API_KEY` | Required when `AI_PROVIDER` set (production enforces) | `sk-...` |
| `AI_MODEL` | Model to use | `gpt-4o-mini` |
| `AI_BASE_URL` | OpenAI-compatible base URL | `https://api.openai.com/v1` |

## 14. Known Limitations / Next Steps

- Real AI analysis cannot be exercised until the user supplies a real key; the
  mock smoke is a faithful stand-in for flow correctness.
- The deterministic parser does not recognize section headings in some CV
  layouts (the reviewer's PDF is one such case) — AI extraction is the designed
  remedy once configured; until then such resumes remain `parsed` with no
  children by design.
- AI output is trimmed to skills already present in the resume; the model may
  still hallucinate, and rate-limit/timeout errors fall back to deterministic
  output (never a 5xx).
- No commit was made; `git status` shows the two changed files from §7.

## 15. Files Changed

- `backend/app/core/config.py` (mock-provider validator fix)
- `backend/tests/test_ai_resume_pipeline.py` (new integration test)
- `docs/PHASE_7_2_REPORT.md` (this report)

(No schema, migration, route, service, or frontend files were modified in this
phase — the Phase 3 AI architecture and Phase 7.1 frontend remediation already
satisfied the requirements end-to-end.)
