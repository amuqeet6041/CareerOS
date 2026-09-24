# CareerOS — Phase 8 — Gemini + AI Stabilization

Date: 2026-09-24 — working tree only, no commit, no push (matching the repo's
established Phase discipline).

## 1. Objective

Make the existing Gemini AI integration work correctly end-to-end through the
existing CareerOS architecture, preserving deterministic parsing, deterministic
matching, deterministic Career Insights, graceful AI fallback, database
integrity, and all existing functionality. Do not rebuild existing systems.

## 2. Initial Problem

The previous audit reported a single failing test:

```
tests/test_ai_resume_pipeline.py::test_get_ai_provider_returns_gemini_provider

Expected: https://generativelanguage.googleapis.com/v1beta/openai/
Actual:   https://api.openai.com/v1
```

Run state before Phase 8 changes (reproduced exactly on this machine):

```
1 failed in 0.42s
>       assert provider._base_url == PROVIDER_GEMINI_BASE_URL
E       AssertionError: assert 'https://api.openai.com/v1' == 'https://generativelanguage.googleapis.com/v1beta/openai/'
```

## 3. Root Cause

Two independent defects, both traced to provider-neutral configuration leaking
OpenAI-specific values into Gemini:

1. **Endpoint resolution defect (primary).** `backend/app/core/config.py`
   defaulted `AI_BASE_URL = "https://api.openai.com/v1"` (provider-agnostic),
   while `backend/app/services/ai/provider.py` selected the Gemini endpoint
   only `if not base_url:`. Because the Settings default is never empty, the
   Gemini branch was dead code — Gemini accidentally inherited the OpenAI
   endpoint.
2. **Model resolution defect (same class).** `config.py` defaulted
   `AI_MODEL = "gpt-4o-mini"`, so `AI_PROVIDER=gemini` with an empty `AI_MODEL`
   would have used the OpenAI model instead of the Gemini default. This was
   masked in the dev environment only because `backend/.env` sets
   `AI_MODEL=gemini-1.5-flash` explicitly.

The prior Phase 7.3 report misdiagnosed this as a "runtime discrepancy"; the
real cause is the Pydantic defaults pre-empting the factory's per-provider
default resolution. `backend/.env` does not set `AI_BASE_URL`, no Windows
process environment variable `AI_*` exists, and no other env file influences
`Settings` — the OpenAI URL came purely from the Pydantic default.

## 4. Files Changed

Tracked files (all intended):

- `backend/app/core/config.py` — `AI_MODEL`/`AI_BASE_URL` now default to empty
  (provider-agnostic), with comment; validator allow-list already had
  `{"openai", "gemini"}` from Phase 7.3.
- `backend/.env.example` — defaults emptied; documents per-provider endpoint/
  model resolution and explicit-override semantics; no secrets.
- `backend/tests/test_ai_resume_pipeline.py` — strengthened the existing Gemini
  gate (name kept) and added coverage for every provider configuration path.
- `backend/app/services/ai/provider.py` — unchanged by Phase 8 (the Phase 7.3
  factory logic is correct once Settings stops pre-empting it); diff shown for
  completeness.

No new dependencies, no migration, no schema change, no new provider class, no
frontend changes.

## 5. Configuration Changes

Desired + verified resolution matrix:

| `AI_PROVIDER` | `AI_BASE_URL` | `AI_MODEL`  | Resolved endpoint | Resolved model |
|---|---|---|---|---|
| `gemini` | empty | empty | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-1.5-flash` |
| `gemini` | `https://custom.example/v1` | `gemini-2.0-flash` | custom preserved | custom preserved |
| `openai` | empty | empty | `https://api.openai.com/v1` | `gpt-4o-mini` |
| `openai` | explicit | explicit | preserved | preserved |
| (empty) | — | — | AI disabled (`None`) | — |
| `mock` | — | — | `MockAIProvider` (refused in production) | — |
| anything else | — | — | `AIConfigurationError` (also `ValidationError` at Settings build) | — |

Explicit user values are never overridden; only empty values resolve to
per-provider defaults.

## 6. Provider Architecture

Unchanged: one `OpenAICompatibleProvider` serves both OpenAI and Gemini over
the same `/chat/completions` protocol. `get_ai_provider()` remains
`None | MockAIProvider | OpenAICompatibleProvider`, raising
`AIConfigurationError` for invalid configuration and missing keys. The factory
now behaves as designed because empty `AI_BASE_URL`/`AI_MODEL` from Settings
trigger each provider's default.

```
Settings (provider-agnostic empty defaults)
  ↓
Provider factory (per-provider defaults)
  ↓
OpenAICompatibleProvider (one class; OpenAI or Gemini endpoint)
  ↓
Resume pipeline / Career-Insights prompts
  ↓
Resume API → Database
```

## 7. Gemini Verification

A valid live API key is present in `backend/.env` (present: YES; value never
printed, never committed). Real requests to
`https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`
were executed through the existing provider and pipeline.

- Endpoint resolution (config-fix verification): live provider resolves host
  `generativelanguage.googleapis.com`, model from config, key authenticated
  (`GET .../v1beta/openai/models` → HTTP 200, 61 models listed).
- **Live request path:** succeeded. Running the existing pipeline against real
  Gemini (model overridden at runtime to a currently-available model,
  `gemini-3.6-flash`, because the configured default is retired — see 13)
  returned `ai_analyzed` with correct structured output: skills
  `[Python, SQL, Pandas, Excel, Power BI]`, 2 experience entries with correct
  `YYYY-MM` dates, education, and the AWS certification.
- Deterministic total-experience was NOT supplied by the model: the pipeline
  computed `3.67` years via `calculate_total_experience_years` (44 months,
  verified by hand), and when resume text lacks dates the total stays `None`
  rather than being guessed.

## 8. Resume E2E Verification

Live `POST /api/resume/upload` (DOCX, in-memory SQLite test DB; model overridden
at runtime to the available Gemini model):

```
Upload (201) → file validation → PDF/DOCX text extraction → deterministic parse
→ AI provider (real Gemini) → structured response → Pydantic validation → persistence
```

Result: `analysis_status = ai_analyzed` on the first attempt. Database
persistence verified directly against the `resumes`, `skills`, `education`,
`certifications`, `experience` rows:

- skills: `Python, SQL, Pandas, Power BI, Excel`
- education: `University of Ottawa`
- certifications: `AWS Certified Solutions Architect`, `PMP Project Management Professional`
- experience: `Acme Inc., Data Analyst` (dates unknown in the source text →
  correctly `None`, deterministic calc → `None`, AI did not invent a value)

All persisted. Deterministic employment-duration calculation remains the source
of truth (model output never replaces it).

## 9. Career Insights Verification

Live `GET /api/career-insights` after an AI-analyzed resume:

- `has_resume: True`
- strengths populated: `Excel(1), Python(1), SQL(1)` (AI-extracted skills used
  as source of truth)
- skill gaps populated (empty for the test job because all required skills were
  present; gap logic proven by the 251-test suite)
- career directions populated: `Data Analyst (1 job)`
- action plan + resume suggestions populated
- `ai_insights.status = available` — a real Gemini call supplied explanatory
  content, which the service filters against verified vocabulary
  (`_trim_ai_insights`), so AI cannot invent unsupported skills.

Deterministic data remains the source of truth; AI only explains.

## 10. Matching Verification

Live `GET /api/jobs/{job_id}/match` on an AI-analyzed resume:

- skill match: `100.0` — qualification match: `100.0`
- experience: correctly `None`-based (no dates in source text → unknown, not
  fabricated); when dates exist the suite asserts `100.0`/`candidate_experience_years`
- overall: `100.0` with unchanged component weights `{skill: 50, qualification: 30, experience: 20}`

No matching weights or algorithm changed in Phase 8.

## 11. Failure/Fallback Verification

Live failure scenario (configured `gemini-1.5-flash`, which Google rejects):

```
POST /api/resume/upload → HTTP 201 (never 500)
analysis_status = ai_failed
deterministic skills still extracted: Python, SQL, Pandas, Power BI, Excel
GET /api/resume/analysis → 200, ai_failed
```

Graceful-degradation architecture confirmed: AI failure never breaks uploads,
and deterministic parsing remains usable. Error categories from the provider
(`provider_error`, `invalid_key`, `rate_limit`, `timeout`) are logged without
resume text, prompts, responses, or keys; a leak test in the suite asserts no
secret ever appears in responses.

## 12. Test Results

```
Targeted AI tests: 41 passed
Resume tests: 15 passed
Full backend tests: 251 passed / 0 failed
Alembic check: PASS  (No new upgrade operations detected.)
Frontend build: PASS (17 routes)
Real Gemini smoke test: PASS  (real request reached Google and succeeded;
  see external-model note in section 13)
```

Full-suite baseline was `244 passed / 1 failed`; the previously failing
Gemini gate now passes and 6 new legitimate provider/config tests raise the
count to 251. No tests were removed or weakened.

## 13. Remaining Issues

**External blocker — configured model retired by Google.** The repository's
canonical Gemini model is `gemini-1.5-flash` (`GEMINI_DEFAULT_MODEL`, and
`AI_MODEL` in `backend/.env`). Google no longer serves it:

```
404: "models/gemini-1.5-flash is not found for API version v1main,
      or is not supported for generateContent."
```

The same account reports `gemini-2.5-flash` as "no longer available to new
users" and currently recommends `gemini-3.6-flash` (which intermittently
returns transient `503 high demand`; a live call succeeded on retry).

Per Phase 8 constraints the model is intentionally **not** changed arbitrarily.
Operator action for live use: set `AI_MODEL=<an available model>` in
`backend/.env` (e.g. `gemini-3.6-flash`). No code change is required — the
architecture resolves any explicitly configured model correctly. A separate
future phase may update `GEMINI_DEFAULT_MODEL` to a GA-tier model.

Other notes (not defects): pre-existing untracked scratch files from the
Phase 7.3 session (`backend/bin/`, `backend/probe_gemini_*.py`,
`docs/PHASE_7_3_REPORT.md`, `CAREEROS_COMPLETE_SYSTEM_AUDIT.md`) were left
untouched and are not part of this phase's change set.

## 14. Final Phase Status

```
PHASE 8 — COMPLETE
```

- [x] Gemini provider correctly resolves
- [x] Gemini default URL works
- [x] OpenAI default URL still works
- [x] Explicit AI_BASE_URL override works
- [x] Gemini model configuration works
- [x] Provider factory tests pass
- [x] AI resume pipeline tests pass
- [x] Full backend test suite passes (251/251)
- [x] Real Gemini request succeeds (via currently-available model; documented
      Google-side retirement of the configured default model in section 13)
- [x] Resume → Gemini → persistence works (live, verified in DB)
- [x] Career Insights works (live)
- [x] Matching works (live)
- [x] AI failure fallback works (live)
- [x] Alembic check passes
- [x] Frontend build passes
- [x] No secrets exposed
- [x] No unrelated regressions