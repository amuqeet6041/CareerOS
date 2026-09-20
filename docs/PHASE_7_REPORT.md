# Phase 7 Report — Career Insights

**Status:** Complete
**Date:** 2026-09-21

## 1. Overview

Phase 7 adds a **Career Insights** surface to CareerOS. It analyzes an
authenticated user's stored resume against the platform's active job catalog
and returns a deterministic, evidence-based career analysis:

- a verified **profile summary** (skills, experience years, education,
  certifications — nothing invented),
- **strengths** (verified skills that relevant jobs actually require),
- **skill gaps** (required skills the user is missing, ranked by demand),
- **career directions** (roles grouped from available job titles, with how well
  the user already matches),
- a deterministic **action plan + resume suggestions**, and
- optional **AI explanations**, clearly flagged as `available | disabled |
  failed` and strictly sanitized so the model can only explain data the
  deterministic analysis already produced.

The endpoint is `GET /api/career-insights` and the page is
`/student-dashboard/career-insights`.

## 2. Scope

In scope:

- Deterministic analysis back end (`career_insights_service.py`).
- Extending the provider-agnostic AI layer with a career-insights prompt,
  strict response schema, and mock-provider support.
- A new authenticated API route + Pydantic response schemas.
- 19 new backend tests (total suite: **241 passing**).
- Frontend service, hook, components, and page rewrite for the existing
  landing-stub route.
- Docs + README/roadmap updates.

Out of scope (unchanged): the matching engine, job ingestion/search,
resume parsing, authentication, and any database schema changes.

## 3. What Was Implemented

Backend:

- `backend/app/services/career_insights_service.py` — the deterministic analysis
  (no persistence, computed on the fly).
- `backend/app/services/ai/career_insights_prompts.py` — system + user prompt
  builder grounded exclusively in the deterministic payload.
- `backend/app/services/ai/schemas.py` — added `AICareerInsights`,
  `AICareerDirection`, `AISkillDevelopment` (strict `Literal` priority).
- `backend/app/services/ai/base.py` + `provider.py` — added
  `generate_career_insights` (default raises `AIOutputError`; implemented on the
  OpenAI-compatible and mock providers, with a shared `_chat` helper).
- `backend/app/schemas/career_insights.py` — response models.
- `backend/app/api/routes/career_insights.py` — the route; registered in
  `app/main.py`.
- `backend/tests/test_career_insights_api.py` — 19 tests.

Frontend:

- `frontend/services/careerInsightsService.js`, `hooks/useCareerInsights.js`.
- `frontend/components/career-insights/` — `priority.js`,
  `CareerSnapshot.jsx`, `StrengthsSection.jsx`, `SkillGapsSection.jsx`,
  `CareerDirections.jsx`, `AICareerInsights.jsx`, `ActionPlanSection.jsx`,
  `CareerInsightsView.jsx`, `CareerInsightsSkeleton.jsx`,
  `CareerInsightsEmpty.jsx`.
- `frontend/app/student-dashboard/career-insights/page.js` rewritten (was a stub
  rendering a placeholder overview).

## 4. Deterministic Analysis Design

- **Sources only**: the analysis reads the stored resume and active jobs via
  existing services (`get_resume_for_user`, `matching_service` +
  `job_search.search_jobs`) — no new tables, no new columns, no persisted
  insight records.
- **Relevance rule** (`_is_job_relevant`): a job is relevant when its skill
  component is resolved (it requires skills — a real demand signal) and the
  user shares at least one required skill or qualification. If the user's
  verified skill set is empty, any skill-requiring job is relevant so current
  demand can still be surfaced honestly.
- **Strengths**: verified user skills that appear among relevant jobs' required
  skills, counted per job (a job counts a skill once).
- **Gaps**: normalized required skills absent from the verified set, counted
  across relevant jobs and sorted by demand; `priority` thresholds are
  `high = count ≥ 0.6 × max`, `medium = count ≥ 0.33 × max`, else `low`.
- **Directions**: jobs grouped by normalized title; each group reports the
  number of matching jobs, average overall match, supporting (already-held)
  and missing skills, and a short explanation.
- **Bounds**: at most 30 active jobs fetched, at most 20 relevant analyzed,
  at most 6 directions, at most 5 missing skills per direction — the endpoint
  stays cheap and predictable.
- **Normalization**: reuses `utils/job_fields.normalize_skill` so insights,
  the matching engine, and job normalization all agree. Duplicate/case/space
  variants collapse correctly (`"python"`, `"Python"`, `" PYTHON "` → one).

## 5. AI Career Insights Design (Boundaries & Safety)

- AI is optional and **never the source of truth**: the deterministic analysis
  always renders. AI can only explain, prioritize, and suggest next steps
  against facts already produced by the deterministic payload.
- The AI is *not allowed* to invent skills, qualifications, experience,
  certifications, salary figures, or labor-market statistics — the prompt
  forbids it, and the response is **sanitized** (`_trim_ai_insights`):
  any `skill_development` item whose normalized skill is not in the user's
  verified skills ∪ derived gaps is dropped.
- Strict response validation: `AICareerInsights` uses typed fields and a
  `Literal["high","medium","low"]` priority; invalid/oversized output degrades
  to `status: "failed"` with empty content and the deterministic page intact.
- Status is always exposed: `disabled` (no provider configured), `failed`
  (provider/config error, outage, or invalid output), `available`.
- No career-prediction claims: deterministic copy and the disabled/failed
  notices explicitly say analysis is computed from the user's resume and the
  jobs on the platform.
- Failure conventions match Phase 3: nothing is logged except error *category*
  (no prompt, no response text, no resume data, no keys).

## 6. API Contract

`GET /api/career-insights` (Bearer token required)

- `401` — not authenticated.
- `404` — `{"detail":"No resume uploaded yet. Upload a resume to unlock Career
  Insights."}`
- `200` — `CareerInsightsResponse`:

```jsonc
{
  "has_resume": true,
  "profile_summary": { "skills": [], "total_experience_years": null,
                       "education": [], "certifications": [], "experience_entries": 0 },
  "strengths": [{ "skill": "SQL", "relevance_count": 2 }],
  "skill_gaps": [{ "skill": "Power BI", "relevance_count": 1,
                   "priority": "high", "why_it_matters": "Required by 1 of 2 relevant jobs analyzed." }],
  "career_directions": [{ "title": "Data Analyst", "matching_job_count": 2,
                          "average_match": 66.67, "supporting_skills": ["SQL"],
                          "missing_skills": ["Power BI"], "explanation": "..." }],
  "action_plan": ["..."], "resume_suggestions": ["..."],
  "fetched_job_count": 30, "relevant_job_count": 20,
  "ai_insights": { "status": "disabled|available|failed", "summary": "",
                   "career_directions": [], "skill_development": [],
                   "resume_suggestions": [], "action_plan": [] }
}
```

The route never accepts a `user_id` — it always analyzes `current_user` from
the token, so no user can read another user's analysis.

## 7. Data Changes / Migration Statement

**No Phase 7 schema changes.** The feature is fully stateless: every insight is
computed on the fly from the existing `resumes`/`skills`/`education`/
`experience`/`certifications` and `jobs`/`job_skills`/`job_qualifications`
tables. No migration was created.

### Pre-existing dev-database drift (found & repaired)

During live verification the dev SQLite database surfaced a **pre-existing**
drift: the `careeros.db` file only contained the *initial* schema — the Phase 1
(`job_skills`/`job_qualifications` tables; `jobs` city/country/posted_at/
is_active/employment fields) and Phase 3 (`resumes.total_experience_years`,
`analysis_status`; education/experience/certification detail columns)
migrations had never been applied to it (`alembic_version` was empty), so any
live request touching those columns failed with `no such column: ...`.

Repair (data-preserving, no application-code change, no new migration):

1. `job_skills` + `job_qualifications` tables created from the models.
2. Missing columns added to `resumes`, `education`, `experience`,
   `certifications`, `jobs`.
3. `alembic stamp head` records the schema is current.

`python -m alembic check` now reports only cosmetic, pre-existing drift
unrelated to Phase 7 (DB-level unique constraints for applications/saved-jobs/
jobs source+external_id, a couple of nullability tweaks, and the renamed
`job_type`/`apply_url` → `employment_type`/`application_url` columns). These
were present before Phase 7 and are outside this phase's scope.

## 8. Security & Privacy

- Auth-gated via the existing `get_current_user` dependency; 401 without a
  token.
- Per-user scoping enforced by the server (`current_user.id`), never by
  client-supplied IDs (verified by `test_authentication_isolation`).
- The AI prompt receives only the user's own verified summary + deterministic
  strengths/gaps/directions; salaries/salary ranges are excluded; AI output is
  vocabulary-sanitized (unknown skills are dropped).
- No secrets logged; AI error category only.

## 9. Testing Strategy & Results

`backend/tests/test_career_insights_api.py` (19 tests) covers:

1. Auth required (401).
2. No resume → 404 with resume hint.
3. **User isolation** — Alice sees her own strengths; Bob (no resume) gets 404.
4. No-skill resume surfaces demand (gaps/directions from jobs, strengths empty).
5. Resume with skills → strengths + gaps + directions with counts/order.
6. Skill normalization (case/whitespace dedupe) reflected in summary + strengths.
7. Duplicate user skills count each job once.
8. Gap detection with per-job counting and `why_it_matters`.
9. Gap frequency ordering + `high`/`medium` priority thresholds.
10. Fetch bound (`fetched_job_count == 30`) and relevant cap (`≤ 20`).
11. Deterministic analysis with AI disabled (status `disabled`, correct
    strengths, empty AI summary).
12. No relevant jobs → graceful empty analysis + "job data" action plan.
13. Empty job dataset → graceful (fetched/relevant 0).
14. AI success → status `available` with summary/directions/skill
    development/suggestions/plan.
15. AI provider failure → status `failed`, deterministic data intact.
16. AI configuration error → status `failed`.
17. Invalid AI response shape → status `failed`.
18. Invalid AI `priority` value → status `failed`.
19. AI unknown-skill rejection — `Golang` dropped, allowed skill kept.

Tests use `MockAIProvider` / monkeypatched `get_ai_provider` (no real key) and
token-isolated skills so counts stay deterministic in the shared in-memory DB.

Results:

- Full backend suite: **241 passed** (222 baseline + 19 new) in ~93 s.
- Frontend production build: **green** (`/student-dashboard/career-insights`
  builds; 17 routes).

## 10. Frontend Changes

The existing `/student-dashboard/career-insights` stub (which rendered a
placeholder `CareerOverview` before any feature existed) was replaced with a
real page that:

- matches the sibling dashboard pages' light theme (`bg-surface`, white
  `border-border` cards, `text-navy`, `bg-accent` accents),
- shows an **empty state** with an "Upload resume" CTA when the user has no
  resume,
- is sectioned with **own loading skeletons and per-section retry** (using the
  existing `DashboardSection`/`SectionSkeleton`/`SectionError` primitives),
- renders the deterministic analysis (snapshot, strengths, gaps with priority
  badges, directions with supporting/missing skill chips, action plan +
  resume suggestions),
- surfaces the AI status honestly: full AI content when `available`, a notice
  when `disabled` (current dev configuration), and a temporary-unavailable
  notice when `failed` — with the deterministic content always present.

## 11. Live Verification (smoke)

Performed against the running dev stack (uvicorn on :8000, Next.js on :3000/3001,
SQLite dev DB) with a throwaway user (cleaned up afterward):

- `POST /api/auth/register` + login → token.
- `GET /api/career-insights` with no resume → **404** with the "No resume
  uploaded yet…" message (instead of the pre-fix broken 500).
- Seeded a resume (skills Python/SQL/Excel) + two active "Data Analyst" jobs in
  the dev DB → `GET /api/career-insights` → **200** with:
  - strengths `SQL ×2, Excel ×1, Python ×1`,
  - gaps `Power BI`/`Tableau` (high priority) with `why_it_matters`,
  - direction "Data Analyst", `matching_job_count 2`, `average_match 66.67`,
  - action plan + resume suggestions,
  - `ai_insights.status = "disabled"` (correct — `AI_PROVIDER` is empty in dev).
- Smoke rows (users/resumes/jobs) fully removed; real dev users untouched.

UI: page renders empty/loading/sections; nav link already present in the
sidebar. A true visual browser walkthrough was not scripted (no browser tool),
so UI was validated by production build + component review.

## 12. Bugs Found & Fixed

| Issue | Cause | Fix |
|---|---|---|
| `GET /api/career-insights` returned **500** instead of 404 for a no-resume user | dev `careeros.db` was missing `resumes.total_experience_years`/`analysis_status` (Phase-3 migration never applied; pre-existing) | repaired dev DB schema (tables + columns) + `alembic stamp head` |
| Initial insight test suite had nondeterministic counts | tests shared one DB; strengths aggregate across all active jobs, so identical skill names collided across tests | per-test token-isolated skills; unique job ids |
| `alembic upgrade head` also failed on the dev DB | tables already existed from an old `create_all` but version table was empty | data-preserving ALTER + `create_all(checkfirst)` for the two missing tables, then stamp |

## 13. Deviations & Decisions

- The brief described a dark "AI dashboard" aesthetic; the page instead matches
  the existing student-dashboard light theme for consistency (deterministic
  content is the primary surface). Dark, colorful theming stays on marketing
  pages.
- AI status is shown explicitly when `disabled` rather than hiding the AI
  section — honesty over polish, consistent with earlier phases.
- No new migration was created (per the brief's "no migration unless necessary"
  rule); the dev DB was repaired in place instead, which also un-blocked
  pre-existing resume/job endpoints live.
- Live PDF upload could not be exercised end-to-end (no valid PDF fixture),
  so the live flow used direct DB seeding of the same resume record the upload
  route produces; PDF/DOCX parsing is already covered by its own test suite.

## 14. Follow-ups / Future Work

- Enforce the remaining pre-existing drift (add `uq_*` unique constraints and
  align nullability / `job_type`→`employment_type`, `apply_url`→
  `application_url` renames) via a small future cleanup migration.
- Trending roles / salary ranges in insights (explicitly future; requires real
  provider data).
- Live visual verification of the new page in a browser session.

## 15. Files Touched

Backend:

- `backend/app/services/career_insights_service.py` *(new)*
- `backend/app/services/ai/career_insights_prompts.py` *(new)*
- `backend/app/services/ai/base.py`, `schemas.py`, `provider.py`
- `backend/app/schemas/career_insights.py` *(new)*
- `backend/app/api/routes/career_insights.py` *(new)*
- `backend/app/main.py` (router registration)
- `backend/tests/test_career_insights_api.py` *(new)*
- `backend/careeros.db` (dev DB schema repair; data preserved)

Frontend:

- `frontend/services/careerInsightsService.js` *(new)*
- `frontend/hooks/useCareerInsights.js` *(new)*
- `frontend/components/career-insights/*` *(9 new files)*
- `frontend/app/student-dashboard/career-insights/page.js` (rewritten)

Docs:

- `docs/PHASE_7_REPORT.md` *(new)*, `README.md` (status/implemented/roadmap
  updates).