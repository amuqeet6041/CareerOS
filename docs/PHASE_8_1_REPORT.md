# CareerOS — Phase 8.1 — Resume Extraction Diagnostics & Fix
## AI Extraction, Deterministic Fallback & Skill/Qualification Pipeline

Date: 2026-09-24 — working tree only, no commit, no push. Phase 10 paused / not
started. Backend changes are strictly limited to the resume extraction pipeline
and its tests; no auth, no provider architecture, no schema, no migrations, no
Phase UI/UI.1 changes, no frontend changes.

## 1. Extraction Flow (documented before modification)

```
Resume file (.pdf/.docx)
   ├─ POST /api/resume/upload (frontend one-shot, event-driven)
   ▼
app.api.routes.resume.upload_resume
   ├─ resume_parser.parse_resume() → raw_text + deterministic sections
   ▼
app.services.ai.pipeline.run_resume_analysis(raw_text)
   ├─ get_ai_provider() → provider or None ("parsed" when AI disabled)
   ├─ provider.extract_resume_information(text)   ← ONE provider call, no retry
   │     on success → AIResumeExtraction validation → structured_to_persist()
   │     on AIProviderError/validation/unexpected → (None, "ai_failed")
   ▼
resume_service.save_resume(...)  → analysis_status ∈ {ai_analyzed, parsed, ai_failed}
   └─ _rebuild_children() replaces (never appends) skills/education/
      experience/certifications children; total_experience_years from AI path
   ▼
Persistence → GET /api/resume/analysis (ResumeOut, unchanged contract)
   ▼
Candidate consumption
   ├─ build_candidate_profile(resume): skills (Skill.name), qualifications
   │   (degree / field_of_study / "degree in field" / cert names),
   │   experience_years (resume.total_experience_years, None-safe)
   ├─ GET /api/jobs/{id}/match → deterministic matching_engine (no AI)
   └─ GET /api/career-insights → deterministic + optional AI explanations
```

## 2. Root Cause

Two separate things were broken:

1. **Upstream Gemini free-tier quota.** The provider is genuinely being rate
   limited by Google — not a code bug, not a misconfiguration.
   - Live request: HTTP `429`, elapsed `0.95s` (instant rejection), sanitized
     provider error:
     `"Quota exceeded for metric: generativelanguage.googleapis.com/
     generate_content_free_tier_requests, limit: 20, model: gemini-3.6-flash.
     Please retry in ~35s."`
   - This is a **free-tier requests quota (RPD)** for `generate_content`,
     not RPM throttling, not billing-on-OpenAI, not invalid config (429 is
     distinct from the 401/403 → `invalid_key` and timeout → `timeout`
     mappings). Classification as `rate_limit` is correct.
2. **The deterministic fallback was incomplete**, so every provider 429
   degraded the profile:
   - **Skills:** the whole skills section was joined into one string then
     split, so the dominant one-skill-per-line layout produced ONE garbage
     skill (`["Python SQL Pandas NumPy Power BI Excel"]`) — practically an
     empty skill profile for job matching.
   - **Qualifications/education:** every tested format returned `[]` even
     without AI. `parse_education` discarded any entry lacking an
     institution, so degrees listed without a university name (the normal
     layout) were lost entirely. Short-form degrees ("BS Economics and Data
     Science", "BSc Economics", "MS Data Science", "MBA") and pre-university
     qualifications ("Intermediate", "A Levels") were not recognized.

### Duplicate-request check (no accidental doubling)
One upload → exactly one `POST /api/resume/upload` → exactly **one** provider
call. The frontend `ResumeUpload.submit()` is event-driven (no React
StrictMode auto-fire); the resume page only `GET /api/resume/analysis` on
mount; the dashboard retry is a user-initiated `POST /api/resume/analyze`
(re-runs AI deliberately). The repeated
`GET /api/jobs/{id}/match` calls in the logs are **deterministic, AI-free**
(`useJobRecommendations`: 1 x GET /jobs + 1 x GET /{id}/match per candidate)
and are expected behavior — they never touch the provider.

## 3. AI Runtime (safe report — no secrets exposed)

| Field | Value |
|---|---|
| Configured provider | `gemini` (via Google OpenAI-compatible endpoint) |
| Provider class | `OpenAICompatibleProvider` (httpx, no SDK) |
| Model | `gemini-3.6-flash` (AI_MODEL explicit; `gemini-1.5-flash` retired per .env note) |
| Endpoint | `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions` |
| Request path | `POST /chat/completions`, `response_format=json_object`, `temperature=0` |
| Requests per upload/analyze | 1 (no retries, no polling, no duplicate frontend calls) |
| Live failure | 429 → category `rate_limit`, ~1s, free-tier `generate_content_free_tier_requests` limit 20, retry in ~35s |
| API key / auth header | never printed, never logged |

## 4. Extraction (before → after)

- **Raw text extraction:** unchanged — PDF (PyMuPDF) and DOCX (python-docx,
  paragraphs + table rows) already worked; preserved.
- **AI extraction:** unchanged architecture — still attempted first; on success
  `AIResumeExtraction` is validated and normalized through
  `structured_to_persist` (`ai_analyzed`).
- **Fallback extraction (fixed):**
  - Skills now split **per line** and per in-line delimiter (comma /
    semicolon / bullet / pipe), keeping multi-word skills intact
    ("Data Analysis") and never merging lines; case-dedupe preserved
    (first-seen display spelling), version variants ("Python 3") stay
    distinct.
  - Qualifications now recognize and preserve: wordy degrees with
    " in <field>" ("Bachelor of Science in Economics and Data Science"),
    short-form degrees ("BS Economics and Data Science" → degree "BS" +
    field "Economics and Data Science"; "BSc Economics", "MS Data Science",
    "MBA", ...), and pre-university qualifications ("Intermediate",
    "A Levels", "O Levels"). Entries are kept even without an institution.
- **Normalization:** skills dedupe on `normalize_skill` key (case-insensitive,
  whitespace-collapsed); no synonym over-merge (SQL / MySQL / PostgreSQL stay
  distinct; "Python" vs "Python 3" distinct). Qualification matching remains
  exact-match by design.
- **Persistence:** deterministic education/experience/certification dicts now
  carry the exact same key sets as the AI path
  (`start_year/end_year`, `location/start_date/end_date/currently_employed`,
  `issue_year/expiry_year`, all null when unknown) → **one canonical
  persistence shape**; `total_experience_years` stays `None` (never guessed)
  on the fallback path. `analysis_status=ai_failed` is preserved and already
  surfaced by the UI (ResumeStatusCard "AI analysis failed" + Retry,
  ResumeAnalysis "fell back to a basic parse") — no masked failure.

## 5. Skills (live sample, Test A synthetic resume, ai_failed fallback)

```
['Python', 'SQL', 'Pandas', 'NumPy', 'Power BI', 'Tableau', 'Excel']
```
(Previously: `['Python SQL Pandas NumPy Power BI Excel']`.)

## 6. Qualifications (live sample, fallback)

```
BS           + Economics and Data Science
Bachelor of Science + Computer Science + University of Punjab
Intermediate
A Levels
MBA
```

## 7. Job Matching

Extracted data reaches matching correctly with no engine changes:
- `GET /api/jobs/{id}/match` (deterministic) scored the fallback-extracted
  skills (matched `Excel`; missing `Research`, `Report Writing`; overall
  20.83, qualification/experience honored None-safe rules). Insights returned
  `has_resume: true`.
- Matching was verified NOT to consume wrong data: candidate profile is built
  only from persisted `Skill`/`Education`/`Certification`/`total_experience_years`
  rows → a provider 429 now yields a full, useful profile instead of a hollow
  one.

## 8. Tests

- Targeted (resume parser + AI pipeline): **64 passed** — incl. new:
  - `test_ai_rate_limit_falls_back_to_useful_skills` (exact 429 scenario →
    `ai_failed` + per-line skills + short-form qualification persisted),
  - `test_deterministic_and_ai_shapes_share_canonical_schema`,
  - one-per-line / bullet / colon skill tests, case-dedupe + version test,
  - qualification-format matrix (wordy, short-form, MBA, Intermediate, A Levels),
  - `test_deterministic_qualification_matches_job_requirement_shape`,
  - AI-disabled upload keeps per-line skills.
- Full backend suite: **274 passed** (no regressions).
- Manual live validation on `127.0.0.1:8000` (real Gemini config, real 429):
  - A — normal `.docx`: skills/quals/exp/certs extracted, `ai_failed`, 201.
  - B — rate-limit fallback: exercised live (the above IS a rate-limit run) +
    mocked 429 unit test.
  - C — broken `.pdf`: HTTP 400 "The file does not appear to be a PDF."
  - D — `/api/jobs/{id}/match` + `/api/career-insights` work on extracted data.
- Frontend build: **not run** — zero frontend files changed this phase (the
  fixed API response is already rendered correctly; no display-integration
  change required). Frontend build/state from Phase UI.1 untouched.

## 9. Migrations & Backend Integrity

- No model/schema change → **no migration created**. `alembic heads` ==
  `alembic current` == `a1b2c3d4e5f6` (unchanged); `git status -- backend/alembic`
  clean. `test_migrations` passes within the full suite.
- Backend files changed (only 3): `app/services/resume_parser.py`,
  `tests/test_resume.py`, `tests/test_ai_resume_pipeline.py`
  (+255 / −21 lines). No changes to routes, config, providers, auth,
  matching engine, or the FastAPI response contract (`ResumeOut`).
- Synthetic fixture (`synthetic_resume.docx`) lives in the OS temp dir outside
  the repo — no real/private user data touched.

## Phase Status

The 429 is an external Google free-tier quota limitation on
`gemini-3.6-flash` (`generate_content_free_tier_requests`, limit 20); the
provider request path is correct and the quota is NOT masked. The deterministic
fallback — which a quota failure always triggers — was incomplete and is now
fixed, canonical, and regression-tested end to end. A provider 429 no longer
turns the resume into an empty/poor profile.

**PHASE 8.1 — RESUME EXTRACTION FIX — PASSED**
(Provider availability limited by Gemini free-tier quota —
  code path correct, fallback working; per the phase's branch for external
  quota: `CODE PATH PASSED / PROVIDER QUOTA LIMITATION REMAINS`.)