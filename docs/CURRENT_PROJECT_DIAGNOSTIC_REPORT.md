# CareerOS — Current Project Diagnostic Report

**Date:** 2026-10-01
**Repository:** `C:\Users\amuqe\OneDrive\Desktop\CareerOS`
**Branch:** `main` @ `2b3392b` ("AI API Tried to Fix but still not fixed")
**Method:** Read-only inspection of the current repository. No source file, `.env`, migration, test, or database row in the project was modified. All runtime checks that create rows ran against a **copy** of `backend/careeros.db` placed outside the repository at `C:\Users\amuqe\AppData\Local\Temp\opencode\audit_smoke.db`. Where this report cites row counts, it distinguishes the project database (`backend/careeros.db`, 5 users / 3 resumes) from that throwaway smoke copy after the audit's own writes (10 users / 4 resumes).

**Secret handling:** No API key, JWT secret, password, or token value appears in this report. Where relevant: `SECRET DETECTED: NO` for committed-to-source secrets; the dev-only JWT fallback is noted without printing any value.

---

## 1. Executive Summary

CareerOS is a **working, tested, end-to-end-capable prototype** of an AI career/job-matching platform. The backend is a coherent FastAPI application with 274 passing tests, a clean single-head Alembic chain (5 revisions, zero drift), a deterministic matching engine with a rigorous "unknown ≠ zero" policy, and a deterministic resume parser that survives every AI failure. The frontend is a Next.js 14 App Router application with **15 explicit route handlers** (14 page routes + `/api/health`) that build cleanly and wire every feature to real backend endpoints — no mocked feature data exists anywhere. (Build tooling reports 16 route-table entries, counting the framework-generated `/_not-found`, and 17 static-generation steps; those build-side numbers are what the phase reports quote, and they are not the number of route files.)

The previous audit's headline conclusions are now **substantially out of date**. Six of its ten major claims were falsified by the current repository:

| Previous claim | Current reality | Verdict |
| --- | --- | --- |
| "4 Alembic migrations ending `313a54989d0d`" | **5** migrations, head `a1b2c3d4e5f6` | WRONG |
| "Around 245 backend tests" | **274** collected, **274** passed | WRONG |
| "1 test failing (`test_get_ai_provider_returns_gemini_provider`)" | **0 failures** | FIXED |
| "Gemini `AI_BASE_URL` defaults to OpenAI → Gemini broken" | Base URL, model, key and endpoint all resolve correctly; **HTTP 200** observed | WRONG |
| "`user_preferences` unrouted and unused; profile editing missing" | 4 profile endpoints + `UserProfile` model + real UI form, 15 tests | WRONG |
| "`careeros.db` contains 0 jobs" | **10** jobs, 5 users, 3 resumes, 2 applications, 1 saved job | WRONG |

Two previous claims remain **accurate**: application status editing has no UI control, and there is no real external job provider.

**The single most important finding in this report:** the Gemini AI integration is **not misconfigured**. It is being throttled upstream. Live probes against the effective URL returned HTTP **200** once and HTTP **503** and **429** on every subsequent call. Every one of the **three** resumes in `backend/careeros.db` has `analysis_status = 'ai_failed'`, and so does the fourth resume created by this audit's smoke test in the throwaway copy — i.e. **no AI analysis has ever succeeded in this environment**. The 429/503 responses are mapped to `ai_failed` **without any retry and without any backoff**, so the feature is effectively non-functional in practice even though the code is correct and the credentials are valid. This is an external-dependency + resilience gap, not a bug in the provider configuration — a materially different diagnosis from the previous audit.

**Second most important finding:** the deterministic resume parser deliberately discards employment dates (`backend/app/services/resume_parser.py:356-357`). Because `total_experience_years` is only ever computed from *AI-extracted* experience (`backend/app/services/resume_service.py:109,112`), **every user whose AI analysis fails has a permanently `null` total experience**, which forces the Experience Match component to `"unknown"` forever and silently reduces the overall score to a skill+qualification average. AI is therefore not a "nice-to-have" enhancement in this system — it is load-bearing for a third of the match score.

**Third:** `UserProfile` and `UserPreference` are **write-only stores**. A repository-wide grep confirms nothing outside `profile.py` / `profile_service.py` / the profile routes ever reads them. Users can diligently fill in preferred roles, work modes, salary, industries, and relocation willingness — and no matching, insights, recommendation, dashboard, or job-search code path consumes any of it. The product's personalization story is currently inert.

Issue counts: **2 BLOCKER, 9 HIGH, 11 MEDIUM, 15 LOW** (37 total — see §23).

---

## 2. Repository & Architecture

### Structure

```
CareerOS/
├── backend/            FastAPI application (20 app modules, 18 test modules)
│   ├── alembic/versions/  5 revisions
│   ├── app/
│   │   ├── api/{deps.py, routes/*}   7 routers
│   │   ├── core/{config,database,security}.py
│   │   ├── models/*  5 model modules
│   │   ├── schemas/* 7 schema modules
│   │   ├── services/* 14 service modules (ai/, providers/ subpackages)
│   │   ├── utils/*   3 utility modules
│   │   ├── cli.py, main.py
│   ├── careeros.db     SQLite dev database (gitignored, present)
│   ├── probe_gemini_factory.py, probe_gemini_pytest_side.py   <-- committed one-shot debug scripts
│   ├── bin/probe_gemini.py
│   ├── requirements.txt (21 pins), alembic.ini, pytest.ini
├── frontend/           Next.js 14.2.5 App Router (15 route handlers, 34 "use client" files)
│   ├── app/(auth)/, app/(public)/, app/student-dashboard/, app/api/health
│   ├── components/{applications,auth,career-insights,dashboard,jobs,resume,shared}
│   ├── hooks/ (10), services/ (7), lib/ (5), utils/ (2)
├── docs/               24 markdown files, 4204 lines (phase reports, audits, architecture)
├── data/{raw,processed,sample}/   empty (.gitkeep only)
├── scripts/            setup_backend.bat, setup_frontend.bat
├── docker-compose.yml  db + backend + frontend (both `build:` targets have no Dockerfile)
├── .env.example, README.md, CAREEROS_COMPLETE_SYSTEM_AUDIT.md
```

### Subsystem inventory

| Area | Current State |
| --- | --- |
| **Frontend** | Next.js 14.2.5 App Router, React 18.3, Tailwind 3.4, plain JavaScript (no TypeScript). 15 route handlers (14 pages + `/api/health`). Single `lib/api.js` fetch wrapper; `services/` → `hooks/` → `components/` layering. Route groups `(auth)`, `(public)`. **No** `middleware.js`, no `loading.tsx`, no `error.tsx`, no `not-found.tsx`, no test framework, no ESLint config despite an `npm run lint` script. |
| **Backend** | FastAPI 0.141.1, Pydantic 2.13.5, SQLAlchemy 2.0.54, 7 routers / **24 endpoints** (23 under `/api` plus root `GET /`), all mounted in `app/main.py:17-24`. Clean `routers → services → models` separation. No service-layer imports from `api/routes` business logic. |
| **Database** | 14 tables. Dev DB is SQLite (`careeros.db`); `psycopg2-binary` is installed and the models are dialect-neutral, but no PostgreSQL connection has ever been exercised by the test suite. `pool_pre_ping=True`. |
| **Migrations** | 5 revisions in one linear chain, single head `a1b2c3d4e5f6`. `alembic check` → **"No new upgrade operations detected."** Zero drift between models, migrations, and the live DB. |
| **Tests** | **274 tests in 18 files, all passing** (112 s). Heavy unit coverage of matching (44), AI pipeline (43), experience duration (23), auth (24), resume (21). API integration coverage via `TestClient` + in-memory SQLite with `PRAGMA foreign_keys=ON`. **Zero frontend tests.** |
| **AI** | Provider abstraction (`app/services/ai/base.py`), one httpx-based `OpenAICompatibleProvider` serving both `openai` and `gemini`, plus `MockAIProvider`. Resilient pipeline (`pipeline.py`) that never raises. Pydantic output schemas with a strict no-fabrication rule. **Configured correctly; throttled upstream.** |
| **Jobs** | `JobProvider` abstraction + **only** `DemoJobProvider` (10 fictional listings, `https://careeros-demo.example` apply links). `job_normalizer` + idempotent `job_ingestion` upsert keyed on `(source, external_id)`. CLI-only seeding. **No external provider, no scheduler.** |
| **Matching** | `matching_engine.py` — fully deterministic, pure functions, no I/O. Weights 50/30/20 with unknown-weight redistribution. Distinct real-0% vs unknown-`None` policy. Legacy `POST /api/matching` retained alongside the production engine. |
| **Authentication** | bcrypt (4.0.1) + HS256 JWT (python-jose), 24 h expiry, `HTTPBearer(auto_error=False)` dependency, explicit allow-list CORS. **No refresh, no revocation, no password policy, no email normalization.** |
| **Resume** | `pymupdf` PDF + `python-docx` DOCX text extraction, then a 500-line deterministic section/heuristic parser with **four typed error classes**. Persistence rebuilds children on re-upload. `analysis_status` ∈ {`parsed`, `ai_analyzed`, `ai_failed`}. **No DELETE endpoint, no file retention (bytes discarded).** |
| **Applications** | Full CRUD surface: create, list (job embedded), status PATCH. Backend status vocabulary: `applied`, `in_review`, `interview`, `offer`, `rejected`. Duplicate protection (409) + DB unique constraint. **`applied_at` never updates on status change. Frontend has no status control.** |
| **Saved Jobs** | Fully wired: `GET /api/jobs/saved`, `POST`, `DELETE` (204), duplicate → 409, unique constraint, correct user scoping. |
| **Career Insights** | **Hybrid.** Deterministic core (`_profile_summary`, strengths, skill gaps, directions, action plan) + optional AI explanation layer that is *sanitised* against a verified vocabulary (`_trim_ai_insights`). Bounded at 30 fetched / 20 relevant / 6 directions. No N+1. |
| **Profile** | `UserProfile` (1:1, unique FK) + `UserPreference` (1:1). 4 endpoints. Full editing form in the UI for headline/location/country/bio + 11 preference fields. **Both models are write-only — nothing reads them.** |
| **Recommendations** | **Client-side orchestration.** 1× `GET /api/jobs?page_size=15` + up to 15× `GET /api/jobs/{id}/match`, sorted client-side, top 5 displayed. **No backend `/recommendations` endpoint exists (404 confirmed).** Ignores all user preferences. |
| **Deployment** | **Not ready.** `docker-compose.yml` references `./backend` and `./frontend` build contexts with **no Dockerfile in either**. No CI/CD. No `.github/`. No reverse proxy, no TLS, no secret management, no structured logging config, no health-check probe. |
| **Documentation** | 24 markdown files in `docs/`, 4204 lines. Extensive but **materially drifted** — 15+ specific false claims identified (see §21). README status banner says "Phases 0-7 complete"; 8 later phases shipped. |

---

## 3. Git / Working Tree

```
$ git status
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean

$ git diff --stat        -> (empty)
$ git diff --cached --stat -> (empty)
```

**Branch:** `main`, in sync with `origin/main`.

**Recent commits:**

| Hash | Message | Date |
| --- | --- | --- |
| `2b3392b` | AI API Tried to Fix but still not fixed | 2026-09-24 |
| `f15eb43` | UI Improvements | 2026-09-24 |
| `f5fb003` | Checkpoint: Phase 8-9 | 2026-09-24 |
| `c340caa` | Phase 7.2 | 2026-09-21 |
| `45069f1` | Phase 7.1 | 2026-09-21 |
| `688e318` | Career Insights | 2026-09-21 |
| `dfeea9c` | Dashboard (Phase 6) | 2026-09-20 |
| `8ffe7ad` | Phase 5 | 2026-09-20 |
| `70f7a5d` | Phase 4: Jobs Frontend | 2026-09-20 |
| `72eaf89` | Phase 3: AI Implementation | 2026-09-20 |
| `acc1fb6` | Phase 2 | 2026-09-20 |
| `d848ec4` | feat: implement core job system | 2026-09-20 |
| `af2d4ed` | chore: establish CareerOS Phase 0 baseline | 2026-09-20 |

**Assessment:**

- **Working tree is completely clean.** All Phase 8–9 work *is* committed. Contrary to the headers in `docs/PHASE_7_3_REPORT.md`, `PHASE_8_REPORT.md`, and `PHASE_8_1_REPORT.md` — which all self-describe as "working tree only, uncommitted, no push" — the code they describe is present in `f5fb003` and `2b3392b`. Those document headers are now false.
- **No unfinished/uncommitted work in progress.** Nothing partially edited, nothing staged.
- **Three one-shot debug scripts are committed to the repository root/ bin:** `backend/probe_gemini_factory.py`, `backend/probe_gemini_pytest_side.py`, `backend/bin/probe_gemini.py`. These are ad-hoc Gemini investigation harnesses, not tests or tools. They hardcode fake keys (`AIza-probe`) and are dead weight that contradicts the docs' claim that Phase 7.3/8 work was uncommitted. They are also *not* collected by pytest (no `test_` prefix), so they do not affect the suite.
- **`.pytest_cache/` is present but gitignored** — no build artefact leakage.
- **No suspicious generated files** are tracked: `careeros.db`, `venv/`, `node_modules/`, `.next/`, `__pycache__/` are all correctly ignored.
- **Commit message quality:** `2b3392b` ("Tried to Fix but still not fixed") is a diagnostic note, not a change description. The actual changes in that commit are 95 lines in `resume_parser.py` plus 181 lines of new tests. Future commits should describe the change, not the emotional state.

---

## 4. Frontend Status

15 explicit route handlers (14 page routes + `/api/health`), all rendering successfully. `next build` reports a 16-entry route table (it adds the framework-generated `/_not-found`) and 17/17 static-generation steps — that build-side count is what the phase reports quote, and it is not the number of route files in the repository.

| Route | File | Completeness | Data source |
| --- | --- | --- | --- |
| `/` | `app/page.js` | Complete (static marketing) | Hardcoded marketing copy + a `MatchPreview` mockup with illustrative `92%/95%/89%` numbers |
| `/login` | `app/(auth)/login/page.js` | Complete | `POST /api/auth/login` |
| `/register` | `app/(auth)/register/page.js` | Complete | `POST /api/auth/register` |
| `/about` | `app/(public)/about/page.js` | **Placeholder** | None — literal text: *"This page is a placeholder — replace it with real content"* |
| `/contact` | `app/(public)/contact/page.js` | **Placeholder** | None — *"Placeholder contact page. Add a contact form or support email here."* |
| `/jobs` | `app/(public)/jobs/page.js` | Complete | `GET /api/jobs` + up to 12× `/match` |
| `/jobs/[id]` | `app/(public)/jobs/[id]/page.js` | Complete | `GET /api/jobs/{id}` (+ `/match` when authed) |
| `/api/health` | `app/api/health/route.js` | Complete | Static `{status:"ok"}` — **does not proxy or check the backend** |
| `/student-dashboard` | `app/student-dashboard/page.js` | Complete | 5 endpoints + 15 match calls |
| `/student-dashboard/jobs` | `.../jobs/page.js` | Complete | Same as `/jobs`, dashboard variant |
| `/student-dashboard/resume` | `.../resume/page.js` | Complete | `POST /upload`, `GET /analysis`, `POST /analyze` |
| `/student-dashboard/saved-jobs` | `.../saved-jobs/page.js` | Complete | `GET /api/jobs/saved`, POST/DELETE `/save` |
| `/student-dashboard/applications` | `.../applications/page.js` | **Partial** | `GET`, `POST` — **no status update UI** |
| `/student-dashboard/profile` | `.../profile/page.js` | Complete (form works) | `GET`/`PATCH` profile + preferences |
| `/student-dashboard/career-insights` | `.../career-insights/page.js` | Complete | `GET /api/career-insights` |

**No route is broken. No feature data is mocked or hardcoded.**

### Notable findings

**Route protection is client-side only.** `app/student-dashboard/layout.js:1` is `"use client"` and guards with `useAuth()` + `router.replace("/login")` (lines 8-31). There is **no `middleware.js`**. Dashboard JavaScript is served to anonymous visitors before the client redirect fires. `isAuthenticated` is a `localStorage` presence check (`hooks/useAuth.js:62`), not an API-verified claim.

**Token handling:** `lib/auth.js:1-2` documents the tradeoff explicitly — *"The JWT lives in localStorage for this v1; an httpOnly cookie + refresh endpoint is the recommended upgrade path."* No refresh, no expiry tracking, no global 401 interceptor.

**Stale-token persisted before validation.** `hooks/useAuth.js:42-50` calls `saveToken(data.access_token)` *before* `getMe()`. If `/me` rejects, the bad token stays on disk.

**401 message logic is inverted.** `lib/api.js:63-68` — the comment describes the "no backend detail" case, but the guard requires the message *not* to be the generic fallback (i.e. a detail *was* provided). Effect: submitting wrong credentials while a stale token exists reports **"Your session has expired. Please sign in again."** instead of "Invalid email or password."

**Inverted condition, concretely:** backend returns `"Invalid credentials"` (`app/api/routes/auth.py:34`), but `frontend/lib/api.js:64` and `docs/RESUME_UPLOAD_AUDIT.md:73` both document the detail as `'Invalid email or password'` — a string the backend never produces.

**Logout never reaches the backend.** `hooks/useAuth.js:52-57` clears local state only; `services/authService.js:17-19` `logout()` is **never imported**. (`POST /api/auth/logout` exists but is a no-op anyway — `app/api/routes/auth.py:40-43` acknowledges a token blocklist would be required.)

**Applications status UI — definitive answer:** there is **no working UI for changing application status.** `components/applications/ApplicationStatus.jsx:27-33` renders a static `<span>` badge. No `<select>`, no `<button>`, no `onChange`. `hooks/useApplications.js` imports only `getApplications` and `createApplication`. The backend capability **already exists and works**: `PATCH /api/applications/{id}` returning 200 with the updated record, 422 on an invalid status, 401 without auth — all verified live (§17). The dead frontend wrapper `services/applicationService.js:15-19 updateApplicationStatus()` sits unreferenced.

**Profile editing — the full 4-way split:**

| Layer | Support |
| --- | --- |
| Database | `user_profiles` (headline, bio, location, country, profile_source) + `user_preferences` (11 fields). Both migrated in `a1b2c3d4e5f6`. |
| Backend API | `GET/PATCH /api/profile`, `GET/PATCH /api/profile/preferences` — all 4 verified 200. 15 tests incl. cross-user isolation. |
| Frontend UI | Editable: headline, location, country, bio. Read-only: name, email. Resume-derived data (skills/education/experience/certs) is **link-only** — *"To update this data, re-upload your CV."* Editable: 11 preference fields. |
| Working E2E | **Yes** for profile + preferences round-trip. **No** for any consumption of those values. |

**Recommendations are client-side.** 16 requests per dashboard load (1 jobs + 15 matches), all concurrent via `Promise.allSettled` (`hooks/useJobRecommendations.js:57-59`). Eligibility requires `overall_match_percentage != null && > 0`; top 5 by score. **User preferences are never sent or consulted.** Bounded by `RECOMMENDATION_CANDIDATES = 15` / `RECOMMENDATION_DISPLAY_COUNT = 5` (`lib/constants.js:44-49`).

**Job lists cannot be sorted by match.** `SORT_OPTIONS` offers only `date_newest`, `date_oldest`, `salary_desc`. `MAX_LIST_MATCHES = 12` caps per-page scoring. The comment at `lib/constants.js:40-41` states this is Phase 5 work that "replaces this with server-side scoring" — Phase 5 shipped without it.

**Shared loading/error state bug.** `hooks/useProfile.js:65-76` — `loadProfile()` and `loadPreferences()` both write the same `loading`/`error` state. Whichever resolves first clears `loading`; and the page's guard `if (error && !profile)` (`profile/page.js:341`) **silently discards** a preferences-fetch error whenever the profile fetch succeeded. The hook's preference `saving`/`saved`/`saveError` flags are dead — the page shadows them with local `prefSaving`/`prefSaved`.

**Dashboard fan-out:** ~20 requests on load (1 `/me`, 1 `/resume/analysis`, 1 `/applications`, 1 `/jobs/saved`, 1 `/jobs`, 15 `/match`). No batching, no caching, no dedupe.

**Theming / UX / a11y are in good shape:** design tokens in `globals.css:18-88` mapped through `tailwind.config.js:28-60`, anti-FOUC script at `app/layout.js:12-21`, `prefers-reduced-motion` honoured, focus-visible ring, `role="meter"`/`progressbar`/`status`/`alert` present, modal focus-move + Escape + scroll-lock. Gaps: currency `<select>` and both salary inputs have **no `<label>`/`id`**; `CheckboxGroup` toggles (`profile/page.js:129-159`) render `<button>` with no `role`/`aria-pressed`; `LoginForm`/`RegisterForm` labels have no `htmlFor` and do not wrap their inputs.

**Verified dead frontend code:** `components/jobs/JobDetails.jsx` (75 lines, superseded by `JobDetailView.jsx`), `components/resume/ResumePreview.jsx` (16 lines), `utils/validators.js` (all 3 exports — the resume input uses a raw `accept=".pdf,.docx"` attribute instead), `services/authService.js:logout`, `services/applicationService.js:updateApplicationStatus`, `lib/constants.js` `JOB_TYPES`/`WORK_MODES`/`APP_NAME`, `ThemeProvider` `toggleTheme`/`resolvedTheme`, the `options`/`signal` passthrough in `services/jobService.js:15,22` (no caller passes options), and three **false comments** — `services/applicationService.js:3` and `services/resumeService.js:3` both say "Placeholder… Connect to backend", and `services/jobService.js:7-8` says saving is "intentionally not wired" — all three describe unwired state for code that is fully wired.

---

## 5. Backend Status

### Endpoint inventory (all 24 endpoints, verified at runtime)

| Method | Endpoint | Auth | Purpose | Status |
| --- | --- | --- | --- | --- |
| GET | `/` | No | Service banner | Working (200) |
| GET | `/api/health` | No | Liveness, `{"status":"ok","service":"backend"}` | Working (200) |
| POST | `/api/auth/register` | No | Create user, return `UserOut` | Working, **weak validation** (200/400/422) |
| POST | `/api/auth/login` | No | Password → JWT | Working (200/401) |
| POST | `/api/auth/logout` | **Yes** | No-op acknowledgement | Working but **semantically void** |
| GET | `/api/auth/me` | Yes | Current user from token | Working (200/401×3) |
| POST | `/api/resume/upload` | Yes | Parse + AI-analyse + persist PDF/DOCX | Working (201/400/413/415) |
| POST | `/api/resume/analyze` | Yes | Re-run AI on stored text | Working (200/404) |
| GET | `/api/resume/analysis` | Yes | Stored resume structure | Working (200/404) |
| GET | `/api/jobs` | No | Search/filter/sort/paginate | Working (200/400) |
| GET | `/api/jobs/saved` | Yes | Saved jobs (declared before `/{job_id}`) | Working (200) |
| GET | `/api/jobs/{id}` | No | Job detail w/ skills + qualifications | Working (200/404) |
| GET | `/api/jobs/{id}/match` | Yes | Deterministic match vs **own** resume | Working (200/401/404) |
| POST | `/api/jobs/{id}/save` | Yes | Save job | Working (201/404/409) |
| DELETE | `/api/jobs/{id}/save` | Yes | Unsave (idempotent) | Working (204/404) |
| POST | `/api/matching` | **No** | **Legacy** raw set-intersection match | Working but superseded |
| GET | `/api/applications` | Yes | List w/ embedded job | Working (200) |
| POST | `/api/applications` | Yes | Track an application | Working (201/404/409) |
| PATCH | `/api/applications/{id}` | Yes | **Change status** | Working (200/401/404/422) — **no UI** |
| GET | `/api/career-insights` | Yes | Deterministic + AI insights | Working (200/404) |
| GET | `/api/profile` | Yes | Profile + identity | Working (200) |
| PATCH | `/api/profile` | Yes | Partial profile update | Working (200) |
| GET | `/api/profile/preferences` | Yes | Preferences (empty object, never 404) | Working (200) |
| PATCH | `/api/profile/preferences` | Yes | Partial preferences update | Working (200) |

All endpoints are connected to the database, return real data, and have Pydantic validation on the request side. Every endpoint is exercised by the test suite except `POST /api/auth/logout` (no test asserts anything beyond its existence) and the legacy `POST /api/matching`.

### Orphan endpoints (exist, unused by the frontend)

| Endpoint | Frontend caller | Note |
| --- | --- | --- |
| `POST /api/matching` | **none** | Legacy; superseded by `GET /api/jobs/{id}/match`. Returns `0.0` (not `None`) for "no requirement" — semantically inconsistent with the production engine. Documented in the file as kept for backward compat. |
| `POST /api/auth/logout` | **none** (and it's a no-op) | Dead both server- and client-side. |
| Root `GET /` | none | Documentation-only. |

### Frontend functionality with no backend endpoint

| Frontend behaviour | Missing backend support |
| --- | --- |
| Job list sorting **by match score** | No sort option for match; `SORT_OPTIONS` has no match key, and `GET /api/jobs` cannot order by a computed score. |
| Batched / bulk match scoring | Only per-job `GET /api/jobs/{id}/match` exists; the dashboard issues 15 sequential round-trips. |
| Personalised recommendations from preferences | No `/api/recommendations`; no service reads `UserPreference`. |
| `DELETE /api/resume` | No delete/reset-resume endpoint; only overwrite-by-re-upload. |
| Aggregated dashboard endpoint | No `/api/dashboard` (confirmed 404); the dashboard is a 20-request client-side composition. |

### Service layer

14 modules. `matching_engine.py` and `experience_duration.py` are pure functions with no I/O (44 + 23 tests). `ai_service.py` is **dead code** — a two-function `NotImplementedError` stub retained only for legacy imports, with docstrings that still claim AI is "reserved, not yet implemented". `job_ingestion.py` implements correct idempotent upsert with a signature-based changed-detection to avoid needless writes and correctly flushes before re-inserting children to dodge unique-constraint collisions.

---

## 6. Database & Alembic

### Migration chain — single head, zero drift

```
$ alembic current
a1b2c3d4e5f6 (head)

$ alembic heads
a1b2c3d4e5f6 (head)

$ alembic history
313a54989d0d -> a1b2c3d4e5f6 (head), phase9_profile_preferences
c821c44ae290 -> 313a54989d0d, reconcile schema drift
bf773dd3d573 -> c821c44ae290, phase3 resume ai
9032a41514cb -> bf773dd3d573, phase1 job system
<base> -> 9032a41514cb, initial schema

$ alembic check
No new upgrade operations detected.
```

**No duplicate heads. No branch. No schema drift.** Models ↔ migrations ↔ live SQLite DB are fully in agreement across all 14 tables. `alembic/env.py:27-39` correctly resolves the URL as *script option → `DATABASE_URL` env var → `settings.DATABASE_URL`*, so a plain `alembic upgrade head` targets the same DB the API uses.

### Live schema (SQLite, `backend/careeros.db`)

| Table | Rows | Columns | Indexes |
| --- | --- | --- | --- |
| `users` | 5 | id, name, email (unique), hashed_password, created_at | `ix_users_email`, `ix_users_id` |
| `resumes` | 3 | id, user_id, file_name, raw_text, uploaded_at, `analysis_status` NOTNULL, `total_experience_years` | `ix_resumes_id` |
| `skills` | 7 | id, resume_id, name | `ix_skills_id` |
| `education` | 5 | + `start_year`, `end_year` | `ix_education_id` |
| `experience` | 2 | + `location`, `start_date`, `end_date`, `currently_employed` | `ix_experience_id` |
| `certifications` | 1 | + `issuer`, `issue_year`, `expiry_year` | `ix_certifications_id` |
| `jobs` | 10 | 23 columns incl. `source`, `external_id` (unique pair), salary, work_mode, employment_type, min/max experience, `is_active` | 8 indexes incl. `ix_jobs_source`, `ix_jobs_work_mode`, `ix_jobs_employment_type`, `ix_jobs_city`, `ix_jobs_posted_at`, `ix_jobs_is_active`, `ix_jobs_external_id` |
| `job_skills` | 29 | + `normalized_name`, unique `(job_id, normalized_name)` | 3 |
| `job_qualifications` | 17 | + `normalized_qualification`, unique pair | 3 |
| `saved_jobs` | 1 | user_id, job_id, saved_at — **unique `(user_id, job_id)`** | `ix_saved_jobs_id` |
| `applications` | 2 | user_id, job_id, status, applied_at — **unique `(user_id, job_id)`** | `ix_applications_id` |
| `user_profiles` | 1 | headline, bio, location, country, profile_source, updated_at — **unique user_id** | `ix_user_profiles_id` |
| `user_preferences` | 0 | `preferred_location`, `preferred_work_mode`, `preferred_job_type` (legacy) **+** 11 Phase-9 fields | `ix_user_preferences_id` |
| `alembic_version` | 1 | `a1b2c3d4e5f6` | auto |

### Findings

1. **`user_preferences` carries legacy columns that nothing populates.** `preferred_work_mode` and `preferred_job_type` (singular) sit alongside the Phase-9 `preferred_work_modes` / `preferred_employment_types` (plural). `schemas/profile.py:84` exposes `preferred_location` under the comment "Legacy fields (exposed for completeness)" while `preferred_work_mode` and `preferred_job_type` are **neither in `PreferencesOut` nor `PreferencesUpdate`** — so the DB column is permanently unreachable and permanently `NULL`.
2. **`user_preferences` is empty (0 rows) in the dev DB** while `user_profiles` has 1 — despite both being edited from the same page. Consistent with the write-only finding: nothing reads them, so no row was ever needed.
3. **`UserPreference` is defined in `backend/app/models/application.py:41`**, not a preferences module. A structural misplacement that makes `models/application.py` a grab-bag.
4. **No `NOT NULL` + CHECK constraint on `applications.status`** — the 5-value vocabulary is enforced only in Python (`app/utils/validators.py:is_valid_application_status` via `app/api/routes/applications.py:51`). The DB will accept any string if written by another path.
5. **No index on `resumes.user_id`** (nor on `applications.user_id`/`saved_jobs.user_id` alone — the unique-pair indexes cover user_id as a leading column, so those are fine). `GET /api/resume/analysis` filters on `Resume.user_id` per request; with one resume per user and a small table this is immaterial now, but it is an unbounded full scan at scale. `users.email` is correctly indexed.
6. **`experiences.start_date`/`end_date` are `VARCHAR`**, not `DATE`. Deliberate (accepts `YYYY-MM`), but it means date arithmetic is string-based and unenforceable at the DB level.
7. **No soft-delete / `deleted_at` on resumes, jobs, users.** `jobs.is_active` exists and is driven by `expires_at`, so job lifecycle is handled; resumes and users are not.
8. **`careeros.db` is committed-ignored but present** and contains real user data (5 users including what appears to be a genuine CV: `Abdul Muqeet CV (Data).pdf`, 4596 chars of `raw_text`). `.gitignore:43-48` correctly excludes `*.db`, so there is no leak — but note the file persists PII locally with no retention policy.

---

## 7. Authentication & Security

### Confirmed secure

- **No secrets in source.** `.env`, `*.db`, `*.pem`, `*.key` are all gitignored (`.gitignore:8-18`, `:43-48`, `:123-127`). `SECRET DETECTED: NO` for committed credentials. `.env.example` files contain no real values.
- **bcrypt hashing** (`app/core/security.py:7`) with a documented pin: `requirements.txt:14-16` explains that `passlib 1.7.4` is incompatible with `bcrypt>=5` (>72-byte passwords) and pins `bcrypt==4.0.1`. Good practice.
- **JWT** HS256 via `python-jose`, `sub` + `exp` only, 24 h expiry (`config.py:27`).
- **Production guard rails in config:** `ENVIRONMENT=production` **raises** on a placeholder/absent `JWT_SECRET` (`config.py:65-69`), on `AI_PROVIDER=mock` (`:82-85`), and on a missing `AI_API_KEY` with a provider configured (`:93-95`). This is genuinely well thought through.
- **No auth bypass.** Every protected route depends on `get_current_user()`. `deps.py` returns 401 for missing credentials, `JWTError`, non-integer `sub`, missing `sub`, and non-existent user. Verified live: no token → 401, garbage token → 401.
- **CORS is an explicit allow-list**, never `*` (`config.py:48-56`, `main.py:9-15`). Verified: `Origin: http://evil.example` → **no** `access-control-allow-origin` header; `Origin: http://localhost:3000` preflight → `access-control-allow-origin: http://localhost:3000`. Correct.
- **SQL injection:** not exploitable. `GET /api/jobs/1; DROP TABLE jobs` → 422 (int path converter). `GET /api/jobs?search=' OR 1=1--` → 200 with `total=0` (SQLAlchemy parameterisation).
- **Authorisation:** `user_id` is **never** accepted from client input on any endpoint. Profile, resume, match, applications, saved-jobs, and insights all derive the user from the token. Cross-user isolation is tested (`test_profile_api.py`).
- **No sensitive data over-exposed.** `ResumeOut` (`schemas/resume.py:50-62`) deliberately omits `raw_text`. Password hashes are never serialised. AI error messages never include response bodies (`provider.py:115` — *"Body is deliberately not included: it may echo the request"*).
- **AI never invents data.** `AISkillDevelopment` output is filtered to the verified vocabulary before it reaches the client (`career_insights_service.py:257-268,324-326`).

### Findings

| # | Finding | Evidence | Severity |
| --- | --- | --- | --- |
| S1 | **Empty password accepted at registration.** `UserCreate.password: str` has no constraints (`schemas/user.py:10-11`). Live: `{"name":"x","email":"...","password":""}` → **HTTP 200**, account created and loginable with an empty password. No minimum length, no complexity, no upper bound. | `schemas/user.py:11`, `api/routes/auth.py:19-27`, live 200 | **HIGH** |
| S2 | **Email is never normalised; uniqueness is case-sensitive.** Registered `UPPERca47fa@example.com`; logging in with `UPPERCACA47FA@EXAMPLE.COM` → **HTTP 401**. Two users can hold the same address differing only in case, and a user who types a different case at login is locked out of their own account. | `api/routes/auth.py:15,32` (raw `==` filter), `models/user.py:13`, live 401 | **HIGH** |
| S3 | **`JWT_SECRET` falls back to a hardcoded dev value.** `config.py:8` `DEV_ONLY_JWT_SECRET`; `.env` does not set `JWT_SECRET`, so the validator returns it. `is_dev_default = True` confirmed at runtime. Safe today because `ENVIRONMENT=development`, and the validator correctly rejects it under production — but any deployment that forgets `ENVIRONMENT=production` signs real tokens with a public constant. | `config.py:60-71`, runtime probe | **MEDIUM** |
| S4 | **No token revocation.** `POST /api/auth/logout` returns `{"message":"Logged out"}` and invalidates nothing; the code comment concedes a blocklist would be needed. A stolen 24-hour token is valid until natural expiry. | `api/routes/auth.py:40-43`, `docs/API_DOCUMENTATION.md:15-16` | **MEDIUM** |
| S5 | **Token stored in `localStorage`, readable by any XSS.** Documented as a deliberate v1 tradeoff. No CSP or security headers are configured in `next.config.mjs` (only `reactStrictMode` and `images.remotePatterns`). | `lib/auth.js:1-5`, `next.config.mjs:2-7` | **MEDIUM** |
| S6 | **JWT revocation of `alg`/`typ` claims:** `python-jose` `jwt.decode` is called with `algorithms=["HS256"]`, which correctly rejects `alg: none` and algorithm-confusion. **No issue.** | `core/security.py:25` | OK |
| S7 | **No rate limiting on `/api/auth/login`.** Unlimited password guessing. No lockout, no throttling, no audit log. | `api/routes/auth.py:30-37` | **MEDIUM** |
| S8 | **bcrypt truncation beyond 72 bytes is unhandled.** A 100-character password is accepted (live: 200). `bcrypt==4.0.1` silently ignores bytes past 72, so two passwords sharing a 72-byte prefix are equivalent. No `max_length` on the schema. | live 200, `requirements.txt:16`, `schemas/user.py:11` | **LOW** |
| S9 | **`datetime.utcnow()` is deprecated.** Emits `DeprecationWarning` in the suite; `models/user.py:15`, `models/profile.py:33`, `core/security.py:19`, `resume_service.py:103`, `job_ingestion.py:83`. Will break on a future Python. | 652 warnings in the test run | **LOW** |
| S10 | **No `name`/`bio` length limits.** `models/user.py:12` `Column(String)` is unbounded VARCHAR; `schemas/profile.py:52` `bio: Optional[str]`. Unbounded user-controlled text stored and echoed. | model + schema | **LOW** |

---

## 8. Resume Pipeline

### Traced flow

```
frontend/components/resume/ResumeUpload.jsx   accept=".pdf,.docx" + size guard
  ↓ POST /api/resume/upload  (multipart; lib/api.js:8-14 omits Content-Type for FormData)
app/api/routes/resume.py:28   contents = await file.read()
app/api/routes/resume.py:31   size > MAX_RESUME_SIZE_MB*1024*1024  → 413
app/services/resume_parser.py:492  allowed_resume_extension + matches_resume_content_type → 415
        ├── .pdf  : magic-byte check b"%PDF-" → MalformedResumeError → 400
        │           pymupdf.open → EmptyFileError → EmptyResumeError → 400
        │           FileDataError/ValueError/RuntimeError → MalformedResumeError → 400
        │           needs_pass → MalformedResumeError (password-protected) → 400
        └── .docx : magic-byte check b"PK" → MalformedResumeError → 400
                    python-docx Document() → any Exception → MalformedResumeError → 400
app/services/resume_parser.py:511  normalize_text (CRLF/tabs/NBSP/ZWSP/whitespace)
app/services/resume_parser.py:512  empty → EmptyResumeError → 400
app/services/resume_parser.py:516  _split_sections (heading-alias map, 4 sections)
        ├── parse_skills         → comma/bullet/pipe split, stop-word + length filters, dedupe
        ├── parse_education      → degree regex + institution regex + degree/field split
        ├── parse_experience     → "Title at Company" / "Title | Company" / "Title, Company"
        └── parse_certifications → separator split + issuer heuristic + year/ID stripping
app/services/ai/pipeline.py:99   run_resume_analysis(raw_text)
        ├── get_ai_provider()  → None ⇒ status "parsed"       (AI disabled)
        ├── provider.extract_resume_information(truncate(text, 30000))
        ├── AIResumeExtraction.model_validate(payload)         ← validation gate
        └── structured_to_persist()  → dedupe skills, drop company-less experience,
                                        calculate_total_experience_years(experience)
app/services/resume_service.py:76  save_resume()  → upsert Resume, _rebuild_children (DELETE+reINSERT)
app/schemas/resume.py:50           ResumeOut  (raw_text NOT exposed)
frontend/hooks/useResume.js:30     applyResult → re-render
```

### Verified behaviour per input class

| Input | HTTP | Detail |
| --- | --- | --- |
| Valid DOCX with skills/experience/education/certs | **201** | 5 skills extracted deterministically; `analysis_status='ai_failed'` (Gemini 429) |
| Invalid type (`text/plain`) | **415** | `"Unsupported file type. Please upload a PDF or DOCX resume."` |
| Malformed DOCX (not a ZIP) | **400** | `"The file does not appear to be a DOCX archive."` |
| Oversized (6 MB vs 5 MB limit) | **413** | `"Resume exceeds the maximum size of 5 MB."` |
| No resume yet (`GET /analysis`, `POST /analyze`) | **404** | `"No resume uploaded yet."` |
| Duplicate upload | **201** | Replaces in place: same `Resume` row updated, children deleted and re-inserted, `uploaded_at` refreshed. No duplicates. Verified — resume id 4 persisted, 5 skills. |

Error handling is genuinely thorough: **four** distinct typed exceptions mapped to **three** distinct HTTP codes with human-readable messages, and every branch verified live.

### What is actually persisted

| Data | Persisted | Where |
| --- | --- | --- |
| Skills | Yes | `skills` table |
| Education | Yes (institution/degree/field; **years always NULL deterministically**) | `education` |
| Experience | Yes (company/title/description; **location/dates always NULL deterministically**) | `experience` |
| Certifications | Yes (name; **issuer often wrong, years always NULL deterministically**) | `certifications` |
| Total experience | **Only from AI.** `resume_service.py:112` explicitly sets `None` on the fallback path. | `resumes.total_experience_years` |
| Raw text | Yes | `resumes.raw_text` |
| Analysis status | Yes | `resumes.analysis_status` |

### Findings

**R1 (HIGH) — deterministic extraction can never populate experience dates, so `total_experience_years` is permanently NULL on the fallback path.** `resume_parser.py:352-357` hard-codes `"location": None, "start_date": None, "end_date": None, "currently_employed": False` with the comment *"deterministic parser never guesses dates/roles"*. `resume_service.py:109` computes `total_experience_years` only from AI `structured`; line 112 sets `None` otherwise. Consequence: whenever AI fails, `matching_service.build_candidate_profile` sets `experience_years = None` (line 99) → `matching_engine.experience_match` returns `(None, "unknown")` (lines 186-193) → `calculate_overall_match` redistributes the 20% experience weight across skill+qualification. **The AI layer is load-bearing for a third of the match score, not merely an enhancement.** Confirmed live: all 4 resumes in the dev DB have `total_experience_years = NULL`, and the live match response returned `experience_match_percentage: null`.

**R2 (MEDIUM) — experience entry splitting corrupts multi-field lines.** A DOCX line `Data Analyst | Acme Corp | Lahore | 2020-01 - Present` matched `_EXPERIENCE_SEP_RE` (`resume_parser.py:98`) on the **first** `|`, persisting `company = "Acme Corp | Lahore | 2020-01 - Present"`. Verified live in the DB. Common CV layouts (pipe-separated role/company/location/dates) therefore produce garbage company names that then flow into career insights and any future application autofill.

**R3 (MEDIUM) — certification issuer swallows the trailing year.** `_CERT_SEPARATORS` (`resume_parser.py:110`) splits on the first matching separator; for `PL-300 Power BI | Microsoft | 2022` it yields `name="PL-300 Power BI"`, `issuer="Microsoft | 2022"` — `_looks_like_issuer` accepts it because it contains letters, and `_clean_certificate_name` strips dates from the *name* only. Verified live.

**R4 (LOW) — uploaded file bytes are discarded.** Only `file_name` and derived text are stored; `uploads/` is gitignored but never written. Good for privacy and disk, but re-parsing without a re-upload is impossible.

**R5 (LOW) — no `DELETE /api/resume`.** A user cannot remove a stored resume (including its PII `raw_text`). Only overwrite-by-re-upload exists.

**R6 (LOW) — `ResumeOut` includes ORM primary keys** (`SkillOut.id`, etc.), leaking internal row IDs to the client for no benefit.

**R7 (LOW) — the entire AI call is synchronous inside the request.** `run_resume_analysis` is called inline at `routes/resume.py:48`, so the 30-second `AI_TIMEOUT_SECONDS` blocks the HTTP response. No background job, no queue, no progress polling.

---

## 9. AI / Gemini

### Configuration trace (`.env` → `settings` → factory → provider → HTTP)

```
backend/.env (gitignored) contains exactly 7 keys:
  DATABASE_URL, ENVIRONMENT, AI_PROVIDER, AI_API_KEY, AI_MODEL,
  AI_MAX_RESUME_CHARS, AI_TIMEOUT_SECONDS
  (no AI_BASE_URL, no JWT_SECRET)

→ app/core/config.py:58   SettingsConfigDict(env_file=".env")     ← RELATIVE path
→ app/core/config.py:44   AI_BASE_URL: str = ""                   ← deliberately empty
→ app/core/config.py:73   _validate_ai_config  (production guards only)
→ app/services/ai/provider.py:163   name = settings.AI_PROVIDER.strip().lower()
→ app/services/ai/provider.py:175   base_url = (settings.AI_BASE_URL or "").strip()  → ""
→ app/services/ai/provider.py:183-186  if name == "gemini": base_url = PROVIDER_GEMINI_BASE_URL
→ app/services/ai/provider.py:75    self._base_url = base_url.rstrip("/")
→ app/services/ai/provider.py:80    url = f"{self._base_url}/chat/completions"
```

### Effective runtime values (secrets redacted)

```text
AI_PROVIDER         = gemini
AI_MODEL            = gemini-3.6-flash
AI_BASE_URL         = ""                     (empty → provider default)
EFFECTIVE_BASE_URL  = https://generativelanguage.googleapis.com/v1beta/openai
REQUEST_URL         = https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
AI_API_KEY_PRESENT  = True
AI_API_KEY_LENGTH   = 53                     [REDACTED]
AI_TIMEOUT_SECONDS  = 30
AI_MAX_RESUME_CHARS = 30000
AI_PROVIDER_CLASS   = OpenAICompatibleProvider   (Gemini uses the shared OpenAI-compatible class)
ENVIRONMENT         = development
DATABASE_URL_SCHEME = sqlite
SECRET DETECTED     : NO (no secret committed to source)
```

### Answer to the central question

> **When `AI_PROVIDER=gemini`, what exact base URL is used at runtime?**

`https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`

**No default value, environment variable, code path, or override causes Gemini to use an OpenAI URL.** The chain was verified at every hop:

| Risk | Reality | Evidence |
| --- | --- | --- |
| `config.py` `AI_BASE_URL` defaults to OpenAI | **No** — defaults to `""` (`config.py:44`) | `AI_BASE_URL = ''` in runtime output |
| Factory falls through to OpenAI | **No** — the Gemini branch runs first (`provider.py:178-186`) and sets both base URL and model; the OpenAI fallbacks at `:188-191` are unreachable when `name == "gemini"` | Runtime probe: `EFFECTIVE_BASE_URL` = Google's URL |
| `.env` overrides base URL | **No** — `AI_BASE_URL` is not present in `.env` at all | `.env` key listing (7 keys) |
| OS env var override | **No** — absent | probe with no override |
| Trailing-slash bug producing `//chat/completions` | **No** — `provider.py:75` `.rstrip("/")` | `REQUEST_URL` has a single slash |
| API key passed as `Authorization: Bearer` | **Yes, correctly** | `provider.py:87`; HTTP 200 observed |
| `gemini-3.6-flash` is a valid model | **Yes** — HTTP 200 with a valid JSON body | live probe |
| `response_format: {"type":"json_object"}` supported | **Yes** — honoured, model returned `{"ok": true}` | live probe |
| Endpoint constructed correctly | **Yes** | live probe |

### Live probe results (minimal, non-destructive)

```
POST https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
  model=gemini-3.6-flash  → HTTP 200  {"choices":[{"finish_reason":"stop",...}]}

Same endpoint, full resume-extraction prompt
  → HTTP 503 Service Unavailable          (twice)
  → HTTP 429 rate limit                   (twice)

Same endpoint, model=gemini-2.0-flash  → HTTP 404  "This model ... is no longer available.
                                            Please update your code to use models/gemini-3.8-flash"
Same endpoint, model=gemini-2.5-flash  → HTTP 404  "no longer available to new users"
Same endpoint, model=gemini-1.5-flash  → HTTP 404  "not found for API version v1main"
```

**Conclusion: the credentials, base URL, model id, request shape, and response parsing are all correct. The configured key is being throttled at the free tier.** Note also that the three historical model ids Google now advertises as replacements all 404, which explains why a naive "just downgrade the model" fix would not help.

### Error handling

Correctly categorised in `provider.py:96-127`:

| Condition | Status | Category | Handled |
| --- | --- | --- | --- |
| Timeout | — | `timeout` | Yes (`AIRequestError`) |
| Network/transport | — | `provider_unavailable` | Yes |
| Bad key | 401/403 | `invalid_key` | Yes |
| Rate limit | 429 | `rate_limit` | Yes |
| Server error | 5xx | `provider_error` | Yes |
| Non-JSON / fenced / non-object | 200 | `output_error` | Yes — `parse_json_payload` tolerates a fenced object, never `eval`s |
| Wrong payload shape | 200 | `output_error` | Yes |

All 7 categories degrade through `pipeline.run_resume_analysis` to `(None, "ai_failed")` without raising. **The deterministic path is fully preserved** — verified live: a DOCX upload with Gemini returning 429 still produced 201 with 5 extracted skills, a usable `GET /api/resume/analysis`, a working match, and working career insights.

### Findings

**A1 (BLOCKER) — no retry and no backoff for 429/503.** `provider.py` performs exactly one `httpx.post` and converts 429 → immediate `AIRequestError`. Every live probe after the first succeeded-with-200 returned 429/503. Effect: **a transient throttle permanently degrades the feature for that request** — and because `analysis_status` is persisted as `ai_failed`, the user's stored resume stays degraded until they manually hit "retry". Confirmed in `backend/careeros.db`: **3 of 3** resumes have `analysis_status='ai_failed'`, including a real 4596-character PDF CV — and the 4th resume created by this audit's smoke test in the throwaway copy is also `ai_failed`, i.e. **no AI analysis has ever completed successfully in this environment**. The resume data is not lost (skills/education/experience/certs are still persisted deterministically), but no AI-derived fields ever appear. This is the direct explanation for the commit message *"AI API Tried to Fix but still not fixed"* — the previous fixes corrected the URL/model/factory, and those fixes worked; the remaining failure is throttling plus zero resilience.

**A2 (HIGH) — career-insights AI errors are mislogged as validation failures.** `career_insights_service.py:317-319`:
```python
except (AIProviderError, ValidationError, ValueError, TypeError):
    logger.warning("Careers AI output failed validation; using deterministic analysis.")
```
`AIProviderError` (429, timeout, invalid key, 5xx) is caught by the same branch and reported as "failed validation". Live log output confirms the misattribution: `Careers AI output failed validation; using deterministic analysis.` was emitted during a run where the actual cause was a 429. This makes AI debugging actively misleading and directly contributed to the "still not fixed" confusion.

**A3 (HIGH) — `GEMINI_DEFAULT_MODEL = "gemini-3.6-flash"` is a hardcoded fallback that will silently rot.** `provider.py:158`. It happens to be the one model that works today, but it is pinned in source with no discovery mechanism, while the three better-known ids all 404. A future Google model deprecation would surface as `ai_failed` with no actionable signal.

**A4 (MEDIUM) — `settings.AI_MAX_RESUME_CHARS = 30000` truncates the *head* only.** `prompts.py:43` `raw_text[:max_chars]`. A long CV loses its entire experience section — the part AI most needs. No warning is recorded when truncation occurs.

**A5 (MEDIUM) — `env_file=".env"` is a relative path.** `config.py:58`. `Settings` resolves `.env` against the **current working directory**, so running `alembic`, `pytest`, or `uvicorn` from anywhere other than `backend/` silently loads *no* environment file and falls back to defaults — notably `DATABASE_URL` → `postgresql://user:password@localhost:5432/careeros` and `AI_PROVIDER` → `""` (AI silently disabled). This is a real footgun with a silent, confusing failure mode.

**A6 (LOW) — `MockAIProvider` is reachable in any non-production environment** and returns `{}` for both methods. `AIResumeExtraction` validates `{}` as all-empty-lists, so `mock` yields `status="ai_analyzed"` with a blank extraction and `total_experience_years = None` — an *optimistic* status for an empty result. `test_get_ai_provider_returns_gemini_provider` now passes, so this is not a live problem, only a latent one.

**A7 (LOW) — dead legacy module.** `app/services/ai_service.py` — two `NotImplementedError` stubs. Harmless but misleading.

---

## 10. Job System

> **Are the jobs currently shown to users real external jobs or demo/generated jobs?**

**Demo/generated jobs. Definitively.** 10 fictional listings with invented companies (`DataWorks Pakistan`, `Insight Analytics`, `Market Intelligence Group`, `TechNova`) and non-resolving apply links (`https://careeros-demo.example/apply/demo-01`). The provider docstring says so explicitly (`providers/demo.py:1-6`).

### Provider layer

- **Abstraction:** `providers/base.py` — `JobProvider` ABC (`fetch_jobs`, `fetch_job`) + `ProviderJob` Pydantic model. Clean contract.
- **Implementations:** `DemoJobProvider` **only**.
- **`get_active_provider()` (`providers/__init__.py:15-22`) hardcodes `return DemoJobProvider()`** and its docstring states configuration-driven selection *"is deferred until a real external provider is integrated."*
- **`JOBS_API_KEY` is declared (`config.py:30`) and referenced nowhere else** in `backend/app/**` or `backend/tests/**`. Dead setting.
- **`JOBS_API_KEY_PRESENT = False`** and **`LLM_API_KEY_PRESENT = False`** at runtime; neither key is in `.env`. `LLM_API_KEY` is likewise dead — superseded by `AI_API_KEY` but never removed.

### Ingestion

`job_ingestion.py` is production-quality for what it does:
- Idempotent upsert keyed on `(source, external_id)`.
- Signature-based change detection → `inserted` / `updated` / `skipped`, so re-seeding is a no-op.
- Per-record failures are counted, not fatal; a provider-level failure raises `JobIngestionError`.
- Children are de-associated and flushed before re-insert to avoid unique-constraint collisions (`:147-154`).
- `ingest_jobs` was exercised by the seed CLI producing the 10 rows now in the DB.

### Search

`job_search.py` + `routes/jobs.py` provide: free-text `search` (title, company, description, location, skills), `location`/`city` substring, `work_mode`, `employment_type`, `salary_min`/`salary_max` ranges, `source`, `include_inactive`, 3 sort keys, and pagination (`page` ≥ 1, `page_size` 1–100, `MAX_PAGE_SIZE`). All validated with explicit 400s listing the allowed values. Verified live: `?search=python` → `total=4`; unknown `work_mode`/`employment_type`/`sort` → 400. Relationships eager-loaded via `selectinload` (`:4, 112, 135`) — **no N+1**.

### Findings

**J1 (BLOCKER for the product promise) — no real job source.** `PROJECT_OVERVIEW.md:15,21` advertises *"live job listings"* from *"approved job data sources"*; the system serves invented data. Every downstream claim — skill gaps, career directions, recommendations, "required by N relevant jobs" — is computed against 10 fictional listings. The **cleanest integration point** is already in place and needs no refactor:
1. Implement `JobProvider` in `app/services/providers/<vendor>.py` (satisfy `fetch_jobs` / `fetch_job`; map the vendor payload into `ProviderJob`, whose `external_id` must be a stable vendor id — the dedupe key depends on it).
2. Return it from `get_active_provider()` (`providers/__init__.py:15`), selecting on a new setting driven by the already-present `JOBS_API_KEY`.
3. Run `python -m app.cli seed-jobs` (`app/cli.py:39-51`) — ingestion, normalization, and upsert already work for any conforming provider.
4. Nothing else changes: search, matching, insights, saved jobs, and applications all read the `jobs` table and are provider-agnostic.

**J2 (HIGH) — no scheduled or on-demand refresh.** `requirements.txt` contains no `celery`, `apscheduler`, or `rq`. Ingestion is CLI-only and manual. Even with a real provider, listings would go stale the moment the seed was last run. `job_ingestion.py:4` anticipates this (*"future scheduled syncs"*).

**J3 (MEDIUM) — `is_active` is never recomputed outside ingestion.** `_upsert_job` sets it from `expires_at` (`job_ingestion.py:117`), but nothing expires rows on a schedule, so an expired-but-not-resynced job stays active until the next ingest. `include_inactive=False` + `is_expired` filtering in search partially mitigates this; verify in `job_search.py` before relying on it.

**J4 (MEDIUM) — demo apply links are dead.** Every `application_url` points at `https://careeros-demo.example/...`, a reserved TLD that cannot resolve. `ApplyNowButton` navigates there, so the "apply externally" step of the user journey terminates in a dead link for 100% of jobs.

**J5 (LOW) — no pagination/limit safety on ingestion.** `DemoJobProvider.fetch_jobs()` returns the full list unbounded; a real provider returning 10 000 records would load all of them into memory and issue 10 000 individual upserts with no batching. `ingest_jobs` has no `chunk_size`.

**J6 (LOW) — no deduplication across providers.** Uniqueness is `(source, external_id)`, so the same real-world posting from two providers would create two rows with no cross-source merge.

---

## 11. Matching Engine

`backend/app/services/matching_engine.py` — 331 lines, **fully deterministic, zero I/O, zero randomness, zero LLM**.

### Algorithm

| Component | Formula | Weight |
| --- | --- | --- |
| Skill match | `matched required / total required × 100`, rounded to 2 dp | **50%** |
| Qualification match | `matched required / total required × 100` | **30%** |
| Experience match | below min → `candidate/min × 100`; above max → `max/candidate × 100`; in range → 100 | **20%** |
| **Overall** | Σ(weight × pct) / Σ(weights of **known** components) | — |

### The unknown-vs-zero policy (the engine's best feature)

- A component is `None` (**unknown**) when the **job** specifies no requirement for it — `skill_match` returns `None` on an empty required list (`:132-133`), `qualification_match` likewise (`:147-150`), `experience_match` returns `no_requirement` (`:177-184`).
- A component is a real **0** when the candidate *has* data that matches none of the requirements — evidence-based, not missing (`:196-205`).
- `calculate_overall_match` (`:218-243`) drops unknown components and **redistributes their weight**, so a job listing no experience requirement does not drag a 90% skill match down to 72%. Returns `None` only when nothing at all is known.
- Candidate experience `None` → `unknown`, **never** assumed to be zero (`:186-193`).
- Normalisation reuses `normalize_skill` / `normalize_qualification`, so the engine, ingestion, and insights all agree on identity. No synonym dictionary — `"Power BI"` == `"power bi"`, but `"B.Sc"` ≠ `"Bachelor of Science"` (documented at `:14-15`). This is a deliberate, stated limitation, not an oversight.
- Summary text is assembled from fixed rules (`:258-295`) with 5 deterministic buckets — always identical for identical inputs.

### Where matching runs

| Surface | Where | Source of score |
| --- | --- | --- |
| Job detail | `GET /api/jobs/{id}/match` | Backend — `matching_service.match_resume_to_job` |
| Job list | Up to 12× `/match` per page (`useJobMatches.js`) | Backend, fetched per job |
| Dashboard recommendations | 15× `/match`, sorted client-side | Backend score, client-side ranking |
| Career insights | `career_insights_service` calls `match_resume_to_job` in-process for ≤30 jobs | Backend, **same engine** |

**Single source of truth confirmed.** `matching_engine.py` is the only production implementation; `matching_service.match_resume_to_job` is the only adapter; all four surfaces route through it. The frontend never computes a match score — it renders `overall_match_percentage` / `average_match` from the API, and `utils/formatters.js:23-28` deliberately returns `null` rather than fabricate a `0%`. The only frontend-computed percentages are profile completion (`lib/profileCompletion.js:43`) and application-status proportions (`ApplicationStats.jsx:61`).

**Verified live** for job 10 vs a resume with Python/SQL/Power BI/Excel/Django:
```json
{"skill_match_percentage":33.33,"qualification_match_percentage":0.0,
 "experience_match_percentage":null,"overall_match_percentage":20.83,
 "matched_skills":["Excel"],"missing_skills":["Research",...],"experience_status":"unknown"}
```
Note the engine correctly reports `experience_match_percentage: null` rather than a fabricated value, and correctly redistributes the 20% weight.

### Findings

**M1 (HIGH) — the legacy engine contradicts the production engine's core policy.** `matching_service.calculate_skill_match` / `calculate_qualification_match` (`:44-72`) return **`0.0` for "no requirement"** where the production engine returns `None`. Reachable via unauthenticated `POST /api/matching` (verified live: HTTP 200). Two live endpoints give contradictory semantics for the same question. It is self-documented as legacy, but it is unauthenticated, undocumented in `API_DOCUMENTATION.md`, and still carries 9 tests.

**M2 (MEDIUM) — the experience component is structurally unavailable without AI.** See **R1**. `experience_match` is fully implemented and 44-unit-tested, yet in production it can only ever return `unknown`/`no_requirement` because `total_experience_years` comes solely from AI extraction. All 23 `test_experience_duration.py` tests and the engine's `below_minimum`/`above_maximum` branches are effectively unreachable in the current pipeline.

**M3 (MEDIUM) — job lists cannot be ordered by match.** Not a defect in the engine but a consequence of the N+1 architecture (§19). Users cannot answer "which of these jobs am I best suited to?" beyond the first page.

**M4 (LOW) — no synonym/thesaurus equivalence.** `"React"` vs `"ReactJS"`, `"PostgreSQL"` vs `"Postgres"`, `"JS"` vs `"JavaScript"` all score as mismatches. With only 10 demo jobs this is invisible; with a real job feed it would materially depress scores and pollute skill gaps. Documented and deliberate, so it is a known limitation to revisit with real data.

**M5 (LOW) — qualifications match on raw token equality.** `build_candidate_profile` emits `degree`, `field_of_study`, `"degree in field"`, and cert names. Demo jobs require e.g. `"Bachelor's in Computer Science"`; a resume storing `degree="BSc", field="Computer Science"` emits `"BSc in Computer Science"` — **no match**, producing the `qualification_match_percentage: 0.0` observed above. The `"degree in field"` composite was clearly designed for this, but the degree spellings still do not align. Under a real job feed this would make the 30%-weighted qualification component near-useless.

---

## 12. Saved Jobs & Applications

### Saved jobs — complete

| Operation | Endpoint | Verified |
| --- | --- | --- |
| List | `GET /api/jobs/saved` | **200**, count 1 |
| Save | `POST /api/jobs/{id}/save` | **201** |
| Duplicate save | — | **409** `"Job already saved"` |
| Unsave | `DELETE /api/jobs/{id}/save` | **204** |
| Unknown job | — | **404** |

Duplicate prevention is enforced twice (application-level check `routes/jobs.py:179-180` **and** a DB unique constraint on `(user_id, job_id)`). Unsave is idempotent. Authorisation is correct — `user_id` comes only from the token. Route ordering is deliberate and documented: `/saved` is declared before `/{job_id}` (`routes/jobs.py:99-100`) so the literal wins over the int converter. Frontend `useSavedJobs` mutates state only after backend confirmation (no optimistic faking).

### Applications

| Operation | Endpoint | Verified |
| --- | --- | --- |
| List (job embedded) | `GET /api/applications` | **200** |
| Create | `POST /api/applications` | **201**, `status: "applied"` |
| Duplicate | — | **409** `"Application already exists for this job"` |
| **Change status** | `PATCH /api/applications/{id}` | **200** → `status: "interview"` |
| Invalid status | — | **422** `"Invalid application status"` |
| No auth | — | **401** |
| Unknown job / application | — | **404** |

### Findings

**P1 (HIGH) — no UI to change application status.** Definitively confirmed. `ApplicationStatus.jsx:27-33` is a static badge; `useApplications.js` imports only `getApplications` and `createApplication`; `applicationService.updateApplicationStatus` (`services/applicationService.js:15-19`) is unreferenced. **The complete backend capability already exists and is verified working** (200/401/404/422 above) — this is purely a frontend gap. A user can record an application and can never move it past `applied`; `interview`, `offer`, and `rejected` are unreachable through the product. `README.md:88-92` correctly acknowledges this.

**P2 (MEDIUM) — `applied_at` is never updated on status change.** `application_service.update_application_status` sets only `status`; `routes/applications.py:44-57` has no status-history table. Verified live: `applied_at` identical before and after `applied → interview`. There is no way to answer "when did I get an interview?" — a core application-tracking capability.

**P3 (MEDIUM) — no "withdrawn"/"ghosted" status.** The 5-value vocabulary (`applied`, `in_review`, `interview`, `offer`, `rejected`) has no terminal-withdrawn state, so abandoned applications must be left as `applied`.

**P4 (MEDIUM) — status vocabulary is defined in two places.** `app/utils/validators.py:is_valid_application_status` (backend enforcement) and `frontend/components/applications/ApplicationStatus.jsx:5-19` `STATUS_LABELS` (frontend display) — no shared contract, no test asserting they agree. A drift would silently render an unknown status as raw text with neutral styling (`ApplicationStatus.jsx:24-26`).

**P5 (LOW) — `POST /api/applications` does not verify the job is active.** `routes/applications.py:34-36` checks existence only. A user can apply to a job excluded by `include_inactive=False`.

---

## 13. Profile & Preferences

### Four-way support matrix

| Capability | Database | Backend API | Frontend UI | Working E2E |
| --- | --- | --- | --- | --- |
| Name | `users.name` | — (read-only in `ProfileOut`) | Rendered read-only | **Read only** |
| Email | `users.email` | — (read-only in `ProfileOut`) | Rendered read-only | **Read only** |
| Phone | ✗ | ✗ | ✗ | **Missing entirely** |
| Headline | `user_profiles.headline` | `PATCH /api/profile` | `InputField` | **Yes** |
| Bio | `user_profiles.bio` | `PATCH /api/profile` | `TextareaField` | **Yes** |
| Location (city) | `user_profiles.location` | `PATCH /api/profile` | `InputField` | **Yes** |
| Country | `user_profiles.country` | `PATCH /api/profile` | `InputField` | **Yes** |
| Education (editable) | `education` table | ✗ | Link-only card | **Missing** |
| Skills (editable) | `skills` table | ✗ | Link-only card | **Missing** |
| Experience (editable) | `experience` table | ✗ | Link-only card | **Missing** |
| Certifications (editable) | `certifications` table | ✗ | Link-only card | **Missing** |
| Preferred roles | `user_preferences.preferred_roles` | `PATCH …/preferences` | `TagInput` | Stored, **never used** |
| Preferred skills | `preferred_skills` | ✅ | `TagInput` | Stored, **never used** |
| Preferred industries | `preferred_industries` | ✅ | `TagInput` | Stored, **never used** |
| Work mode (remote/hybrid) | `preferred_work_modes` | ✅ | `CheckboxGroup` | Stored, **never used** |
| Employment type | `preferred_employment_types` | ✅ | `CheckboxGroup` | Stored, **never used** |
| Preferred location | `preferred_location` | ✅ | `InputField` | Stored, **never used** |
| Salary min/max + currency | `salary_min`, `salary_max`, `currency` | ✅ | 2 number inputs + select | Stored, **never used** |
| Career level | `career_level` | ✅ | `<select>` | Stored, **never used** |
| Open to relocate | `open_to_relocate` | ✅ | Checkbox | Stored, **never used** |

All 6 API calls verified live (200 on every GET and PATCH; partial-update semantics confirmed — omitted fields preserved).

### Findings

**F1 (HIGH) — `UserProfile` and `UserPreference` are write-only; nothing ever reads them.** Repository-wide grep for `UserPreference|get_preferences|preferences` across `backend/app/**` returns matches **only** in `models/application.py`, `models/user.py`, `api/routes/profile.py`, `services/profile_service.py`, and `schemas/profile.py`. `UserProfile` likewise. **Not one** of: `matching_engine`, `matching_service`, `job_search`, `career_insights_service`, `saved_job_service`, `application_service`, or any route consumes them. Consequences: (a) users can spend real effort on 11 preference fields with zero effect; (b) the product cannot honestly claim personalised recommendations; (c) `user_preferences` sits at 0 rows in the dev DB despite being editable in the UI, confirming nothing reads it. The Phase-9 feature shipped as *storage only*.

**F2 (MEDIUM) — resume-derived data cannot be corrected by the user.** Skills, education, experience, and certifications are shown read-only with the message *"CareerOS will not overwrite changes you make here"* and instructions to re-upload. With the deterministic parser's known extraction defects (**R2**, **R3**), a user who has corrected a company name or issuer has **no way to fix it** except re-uploading and hoping the parser behaves differently. There is no `PATCH /api/resume` or profile-skills override.

**F3 (MEDIUM) — a dual-source-of-truth design with no resolution rule.** `UserProfile.profile_source` exists specifically to distinguish `"manual"` from `"resume_extracted"` (`models/profile.py:29-31`), and `upsert_profile` hard-codes `profile_source = "manual"` on every update (`profile_service.py:68`). But **no code path ever sets `profile_source = "resume_extracted"`** — the column was created for a merge/conflict-resolution policy that does not exist. It is currently a constant.

**F4 (MEDIUM) — three duplicate definitions of the preference vocabulary.** `backend/app/utils/job_fields.py` (`WORK_MODES`, `EMPLOYMENT_TYPES`), `frontend/lib/constants.js:1-10` (`WORK_MODE_OPTIONS`, `EMPLOYMENT_TYPE_OPTIONS`), and local copies in `frontend/app/student-dashboard/profile/page.js:193-205` (`WORK_MODES`, `EMPLOYMENT_TYPES`). The local copy **omits `"temporary"`**, which `job_fields.py` and `lib/constants.js:8` both include — so the UI cannot select a value the backend accepts. No test asserts the sets match.

**F5 (LOW) — duplicated save state.** `useProfile.js:78-92` maintains `saving`/`saveError`/`saved` for preferences; the page ignores them and shadows with `prefSaving`/`prefSaved`/`prefSaveError` (`profile/page.js:254-256`). Dead hook state; a latent source of confusion.

**F6 (LOW) — shared `loading`/`error` across two resources.** See §4. A preferences failure is silently discarded whenever the profile fetch succeeded (`profile/page.js:341`).

**F7 (LOW) — `profile_source` is `nullable=True` with `default="manual"`** but `ProfileOut.profile_source` defaults to `"manual"` (`schemas/profile.py:40`), so a never-written row reports `"manual"` while the DB column is `NULL` (observed live: `profile_source: null` on first GET). Cosmetic inconsistency between ORM default and schema default.

**F8 (LOW) — no phone field.** The brief lists phone; the data model has no column and there is no route or UI for it.

---

## 14. Dashboard

`frontend/app/student-dashboard/page.js` → `StudentDashboard.jsx`, composed of 10 components from 5 real endpoints. Each section renders its own loading skeleton, error state with retry, and empty state.

| Section | Source | State coverage |
| --- | --- | --- |
| ProfileSummary | `useAuth().user` + resume | ✅ all three |
| ProfileCompletion | `lib/profileCompletion.js` (6 real components, pure) | ✅ |
| ResumeStatusCard | `GET /api/resume/analysis` | ✅ + **retry analysis** wired to `POST /api/resume/analyze` |
| RecommendedJobs | 1 jobs + 15 matches | ✅ + "no resume" state |
| ApplicationStats | `GET /api/applications` | ✅ |
| RecentApplications | same list response | ✅ |
| SavedJobsSummary | `GET /api/jobs/saved` | ✅ |
| CareerOverview | resume analysis | ✅ |

**Profile completion** (`lib/profileCompletion.js`) is a pure function over 6 real components — honest, not hardcoded. **Application stats** computes proportions from the real applications list. **No mocked data.**

### Findings

**D1 (HIGH) — ~20 HTTP requests per dashboard load, up to 15 of them concurrent.** `useAuth` (1) + `useResume` (1) + `useApplications` (1) + `useSavedJobs` (1) + `useJobRecommendations` (1 + 15). Each `/match` request independently re-runs `build_candidate_profile` and re-queries the job with `selectinload`. No batching, no caching, no request coalescing, no dedupe. Browser HTTP/1.1 limits this to ~6 in-flight per origin, so the 15 matches serialise into waves. Every navigation to `/student-dashboard` repeats the full fan-out.

**D2 (MEDIUM) — `useAuth` and `useProfile` both fetch identity redundantly.** The dashboard reads user data from `useAuth()` (which calls `/api/auth/me`) while `/api/profile` also returns `name` + `email` (`schemas/profile.py:32-33`). Two sources for the same two fields.

**D3 (MEDIUM) — no `loading.tsx` at any segment.** Every dashboard route transition is a client-side blank flash, then a skeleton. `app/student-dashboard/layout.js` being `"use client"` guarantees nothing in the subtree can be streamed or prerendered — all 7 dashboard routes appear as `○ (Static) prerendered as static content` in the build output with the guard running purely on the client.

**D4 (LOW) — recommendations are gated on `hasResume`, so the empty state is the default first-run experience.** Correct by design (`StudentDashboard.jsx:42-45`), and it avoids firing 15 doomed 404s — the hook comment says so explicitly. Worth noting that a brand-new account sees the dashboard, the resume card, and a prominent "upload your CV" CTA, but no recommendations and no insights at all.

---

## 15. Career Insights

### Architecture: hybrid, deterministic-first

```
GET /api/career-insights  (auth, 404 without resume)
  → career_insights_service.analyze_career_insights(db, resume)
      1. _profile_summary(resume)          VERIFIED FACTS ONLY
         skills (deduped) · total_experience_years · education · certs · experience_entry_count
      2. fetch_active_jobs(db, limit=30)   via search_jobs (eager-loaded, no N+1)
      3. match_resume_to_job(resume, job)  × 30, in-process, same engine as everywhere else
      4. _is_job_relevant()                skill component resolved AND (shared skill OR shared qual)
                                            (or: any skill-requiring job when the user has 0 skills)
      5. sort by overall desc → cap 20
      6. strengths    = verified user skills required by relevant jobs, ranked by frequency
      7. skill_gaps   = job-required skills absent from the verified set, ranked by frequency,
                        priority = count vs max_count (high ≥ 0.6, medium ≥ 0.33)
      8. _build_directions()               group relevant jobs by normalized title, cap 6,
                                            ≤5 missing skills each, supporting skills ranked
      9. _deterministic_action_plan()      evidence-based, AI-free
     10. _run_ai_career_insights(payload)  OPTIONAL explanation layer
             status ∈ {available, disabled, failed}
             _trim_ai_insights() filters skill_development to the verified vocabulary
     11. why_it_matters / explanation strings attached to every gap and direction
```

### Verdict: **hybrid, and the hybrid is correct**

- **Deterministic is the source of truth** for every number, every skill, and every count. The service docstring is explicit: *"AI (when enabled) may only explain, prioritize, and suggest next steps; it never changes match scores or invents facts"* (`career_insights_service.py:10-12`).
- **AI cannot invent unsupported skills.** `_run_ai_career_insights` builds `allowed = verified user skills ∪ deterministic skill-gap skills` (`:324-325`) and `_trim_ai_insights` **silently drops** any `skill_development` entry whose skill is not in that set (`:267`). AI also cannot contribute to `strengths`, `skill_gaps`, `career_directions`, or `average_match`. The AI payload contains only verified facts — no salaries, no labour-market statistics.
- **Bounded:** 30 fetched / 20 relevant / 6 directions / 5 missing skills per direction / 8 skill-development items / 8 suggestions. Output is length-capped (`AI_SUMMARY_MAX_CHARS=800`, `AI_REASON_MAX_CHARS=300`).
- **No N+1:** `fetch_active_jobs` routes through `search_jobs` with `selectinload` (`career_insights_service.py:20`, `:105-111`); job skills are already loaded.
- **Nothing is persisted** — computed on the fly, so no migration was needed and results are always fresh.

### Behaviour under each condition

| Condition | Behaviour | Verified |
| --- | --- | --- |
| No resume | **404** `"No resume uploaded yet. Upload a resume to unlock Career Insights."` | ✅ live |
| Resume parsed, AI failed | All deterministic sections populated from real data; `total_experience_years: null`; `ai_insights.status = "failed"` with empty content; page keeps showing deterministic data | ✅ live — `has_resume: true`, 5 real skills, real education, real certs |
| AI available and healthy | Deterministic sections **plus** `ai_insights.status = "available"` with summary/directions/skill_development/suggestions/action_plan, all sanitised | Code path verified; **not** observed live (see §9) |
| AI disabled (`AI_PROVIDER=""`) | `ai_insights.status = "disabled"` (`career_insights_service.py:310`) | Code path verified |
| No jobs at all | `_is_job_relevant` → nothing; `relevant_job_count = 0`; `skill_gaps`/`strengths` empty; action plan gets *"We need relevant job data to identify current skill demand."*; `why_it_matters = "No relevant jobs analyzed yet."` | Code path verified |
| Many jobs | Hard-capped at 30 fetched / 20 relevant; directions capped at 6 | Code path verified |
| AI raises anything | `except Exception` (`:320-322`) logs and returns `_ai_insights_fallback()`; deterministic result untouched | ✅ live (429) |

### Findings

**CI1 (HIGH) — AI failure logging is misleading.** See **A2**. `career_insights_service.py:317-318` labels provider errors as validation failures. Verified live.

**CI2 (MEDIUM) — insight quality is bounded by demo-data scarcity.** With only 10 fictional jobs all dated `2026-08-01`, strengths and gaps are computed over a tiny, static demand signal. A user could legitimately have a skill ranked as a "high priority gap" purely because of which 10 demo listings exist. Nothing is wrong with the code; the input is not representative.

**CI3 (MEDIUM) — `experience_entries` is a count, not data.** `_profile_summary` reports `"experience_entries": len(resume.experience)` and never surfaces company/title/dates to the AI payload. The AI is therefore asked to comment on career direction while being shown no work history. Combined with **R1** (no deterministic dates), experience is effectively invisible to insights.

**CI4 (LOW) — `_run_ai_career_insights` uses local imports.** `career_insights_service.py:297-301` imports the provider, prompts, schemas, and `ValidationError` **inside the function**. Defensible as lazy-import cycle avoidance, but it means an import error surfaces per-request rather than at startup, and it is the only service in the codebase that does this.

**CI5 (LOW) — no caching.** Insights are recomputed in full on every request — 30 job matches in-process, plus a live AI call. No TTL, no memoisation. `AI` is billed per page view.

**CI6 (LOW) — `_gap_priority` thresholds are magic ratios** (0.6 / 0.33) declared as module constants without justification in code or docs. With 1 relevant job every gap is trivially "high".

---

## 16. Recommendations

### Current implementation: client-side, deterministic, resume-only

```
hooks/useJobRecommendations.js
  candidates   = RECOMMENDATION_CANDIDATES  = 15   (lib/constants.js:45)
  displayCount = RECOMMENDATION_DISPLAY_COUNT = 5  (lib/constants.js:46)
  enabled      = isAuthenticated && hasResume && !resume.loading   (StudentDashboard.jsx:43-45)

  1 × GET /api/jobs?page=1&page_size=15                       → newest 15 by posted_at
  15 × GET /api/jobs/{id}/match        (Promise.allSettled, all concurrent)
  filter:  match.status === "success"
        && match.data.overall_match_percentage != null
        && match.data.overall_match_percentage > 0
  sort:    overall_match_percentage descending
  slice:   top 5
```

**Is there a `/recommendations` endpoint?** No. Verified: `GET /api/recommendations` → **404** on both `TestClient` and a live `uvicorn` server. `GET /api/dashboard` → **404** as well.

### Assessment against the questions asked

| Question | Answer |
| --- | --- |
| Frontend or backend? | **Frontend orchestration** of backend-computed scores. No server-side ranking endpoint. |
| Number of jobs fetched? | 15 candidates, top 5 displayed. |
| Matching strategy? | Identical deterministic engine, invoked per job. |
| Sorting? | By `overall_match_percentage` descending, client-side. |
| Filtering? | `overall_match_percentage != null && > 0` — a 0-overlap job is excluded as "not a recommendation". |
| Pagination? | None. Only the newest 15 by `date_newest`. |
| Duplicate requests? | **Yes** — the same `/match` calls are issued independently by the job list (up to 12), the job detail, and recommendations. No cache or dedupe across surfaces. |
| Performance? | 16 requests per dashboard load; 15 concurrent; each re-runs `build_candidate_profile`. |
| Personalised? | **Resume-personalised only.** Uses skills + qualifications + experience from the resume. |
| Uses profile/preferences? | **No.** `UserProfile` and all 11 `UserPreference` fields are ignored. |

### Findings

**R-1 (HIGH — tracked as Issue H5) — recommendations are drawn only from the newest 15 jobs and cannot be ranked server-side.** With a real job feed (thousands of listings), this returns the 15 most recent regardless of relevance and scores only those. A strong match posted a week ago is **never considered**. The bound is documented as deliberate (`lib/constants.js:40-41`: *"Phase 5 replaces this with server-side scoring so the whole result set can be ordered by match"*) — Phase 5 shipped without it.

**R-2 (HIGH) — preferences are ignored, so "recommendations" ignore every stated user preference.** See **F1**. A user who sets `preferred_work_modes: ["remote"]`, `salary_min: 500000`, `preferred_roles: ["Data Analyst"]`, and `open_to_relocate: false` receives the same 5 recommendations as a user with no preferences at all. The backend has all the data and no consumer.

**R-3 (MEDIUM) — N+1 request fan-out.** 15 sequential-ised `/match` calls per dashboard load, each independently loading the job and rebuilding the candidate profile. A batch or list-scoring endpoint would collapse 16 requests into 1.

**R-4 (MEDIUM) — no caching or TTL.** Refetched on every dashboard mount and on every `refetch()`. With `useJobMatches` also scoring up to 12 jobs on every job-list page, match computation is the single largest source of backend load in the app.

**R-5 (LOW) — `> 0` exclusion hides legitimately-matched jobs.** A candidate whose skills overlap a job at exactly 0% is excluded — correct intent (zero overlap is not a recommendation) — but the boundary is a raw `> 0` with no explanation surfaced to the user, so a user with no recommendations sees an unexplained empty state.

---

## 17. End-to-End Workflow

All statuses below are based on live runtime verification (§19), not code reading alone.

| # | Step | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Register | **WORKING** (weak validation) | 200; duplicate → 400; **empty password → 200 (S1)** |
| 2 | Login | **WORKING** | 200 + token; wrong password → 401; **case-mismatched email → 401 (S2)** |
| 3 | `/me` | **WORKING** | 200; no token → 401; garbage token → 401 |
| 4 | Dashboard | **WORKING** | Renders all 10 sections from real data; ~20 requests (D1) |
| 5 | Upload resume | **WORKING** | 201 for DOCX; 415 bad type; 400 malformed; 413 oversized |
| 6 | Resume parsing | **WORKING** (partial fidelity) | 5 skills extracted; **company/issuer corruption (R2, R3)**; **no dates ever (R1)** |
| 7 | AI analysis | **EXTERNAL DEPENDENCY** | **3/3 resumes in `backend/careeros.db` are `ai_failed`** (plus the audit's own smoke-test resume); live 429/503; base URL/model/key all verified correct (§9) |
| 8 | Skills persistence | **WORKING** | `skills` table, 5 rows for the smoke user |
| 9 | Education persistence | **WORKING** | Institution/degree/field persisted; years always NULL |
| 10 | Experience persistence | **PARTIAL** | Rows persisted but dates/location always NULL → **no total experience** |
| 11 | Certifications persistence | **WORKING** (partial fidelity) | Persisted; **issuer may include trailing year (R3)** |
| 12 | Job discovery | **WORKING** | 200; `?search=python` → total 4; filters + 3 sorts + pagination |
| 13 | Real job APIs | **MISSING** | `DemoJobProvider` only; `get_active_provider()` hardcoded (J1) |
| 14 | Job matching | **WORKING** | 200 with correct `null` for unknown experience; weight redistribution confirmed |
| 15 | Save job | **WORKING** | 201; duplicate → 409; list → 200; unsave → 204 |
| 16 | Apply | **EXTERNAL DEPENDENCY** | Tracking works (201, duplicate → 409) but `application_url` → dead `.example` domain (J4) |
| 17 | Application tracking | **PARTIAL** | List works; **no status UI (P1)**; `applied_at` never updated (P2) |
| 18 | Career insights | **WORKING** | 200 with real strengths/gaps/directions/action plan; deterministic core sound |
| 19 | Recommendations | **PARTIAL** | Real and resume-personalised, but client-side, newest-15 only, preferences ignored |
| 20 | Profile / preferences | **PARTIAL** | Write path works end-to-end; **read path nonexistent (F1)**; resume-derived fields uneditable (F2) |
| 21 | AI career insights | **EXTERNAL DEPENDENCY** | Code path correct and sanitised; never observed `available` at runtime (429) |

**Summary:** 13 WORKING, 4 PARTIAL, 3 EXTERNAL DEPENDENCY, 1 MISSING across 21 steps. The pipeline never breaks the user experience — the deterministic fallbacks genuinely work, which is the strongest architectural property in the codebase.

---

## 18. Tests & Build

```text
Backend tests:
Passed:  274
Failed:  0
Skipped: 0
Errors:  0
Warnings: 652 (predominantly datetime.utcnow() DeprecationWarning — S9)
Duration: 112.04s

Command: venv\Scripts\python.exe -m pytest -q   (workdir: backend)

Frontend build:
PASS — Next.js 14.2.5, "✓ Compiled successfully", 17/17 static-generation steps,
       shared JS 87.1 kB, zero errors, zero warnings.
Command: npx --no-install next build   (workdir: frontend)

Alembic:
PASS — `alembic current` = a1b2c3d4e5f6 (head)
       `alembic heads`   = a1b2c3d4e5f6 (single head, no branches)
       `alembic check`   = "No new upgrade operations detected."

Frontend lint:
CANNOT RUN — `npm run lint` maps to `next lint`, but there is **no `eslint`
dependency and no ESLint config** (`.eslintrc*` / `eslint.config.*` absent).
`next lint` drops into an interactive first-run setup prompt, so the script
is non-functional in CI and in any non-interactive shell.

Frontend tests:
NOT CONFIGURED — no `test` script, no jest/vitest/playwright/cypress, no config.

Typecheck:
N/A — plain JavaScript; `jsconfig.json` sets only `baseUrl` + `@/*` path alias.

Live server startup:
PASS — `uvicorn app.main:app --host 127.0.0.1 --port 8123` started cleanly.
       /api/health → 200, /api/jobs → 200, /docs → 200, /openapi.json → 200.
```

### Test distribution (274 collected, `pytest --collect-only -q`)

| File | Tests | File | Tests |
| --- | --- | --- | --- |
| `test_matching_engine.py` | 44 | `test_profile_api.py` | 15 |
| `test_ai_resume_pipeline.py` | 43 | `test_job_normalizer.py` | 13 |
| `test_experience_duration.py` | 23 | `test_job_fields.py` | 10 |
| `test_auth.py` | 24 | `test_matching.py` | 9 |
| `test_resume.py` | 21 | `test_job_ingestion.py` | 8 |
| `test_career_insights_api.py` | 19 | `test_job_match_api.py` | 8 |
| `test_jobs_api.py` | 14 | `test_job_providers.py` | 8 |
| `test_saved_jobs_api.py` | 8 | `test_applications_api.py` | 2 |
| `test_migrations.py` | 4 | `test_health.py` | 1 |

`test_migrations.py` exists and covers the schema/migration contract, which is why drift is caught early.

### Coverage assessment

**Strong:** matching engine, AI pipeline fallback behaviour, experience-duration maths, auth, resume parsing/persistence, profile isolation, career-insights determinism, job normalization/ingestion idempotency.

**Gaps:**
- **Zero frontend tests of any kind** — 34 client components, 10 hooks, 7 services are entirely untested.
- **No test for `POST /api/auth/logout`.**
- **No live-provider test** (no provider exists to test) and **no ingestion-scale test**.
- **No PostgreSQL test run.** `conftest.py` hardcodes `sqlite://`. Every migration and query has only ever been validated against SQLite, despite PostgreSQL being the documented target. Dialect-specific behaviour (e.g. `VARCHAR` length enforcement, `JSON` column types, case-sensitive `unique` on `users.email`) is unverified.
- **No test asserts the frontend/backend status vocabulary agree** (P4) or that the work-mode/employment-type sets agree (F4).
- **No concurrency test** for duplicate save/apply race conditions (both are check-then-insert, relying on the DB constraint as the real guard).
- **The passing suite does not reflect production AI behaviour**, because all AI tests use `MockAIProvider` or monkeypatched providers. The 429/503 reality in §9 is invisible to CI.

---

## 19. Performance / Architecture

| # | Finding | Evidence | Category |
| --- | --- | --- | --- |
| 1 | **15 concurrent `/match` requests per dashboard load** | `useJobRecommendations.js:57-59`; `RECOMMENDATION_CANDIDATES = 15` | N+1 / excessive API requests |
| 2 | **Up to 12 more `/match` requests per job-list page** | `useJobMatches.js`, `MAX_LIST_MATCHES = 12` | N+1 / excessive API requests |
| 3 | **~20 requests per dashboard navigation, no caching** | `StudentDashboard.jsx:32-45` | Duplicate fetching |
| 4 | **`build_candidate_profile` re-executed per match request** | `matching_service.py:111` inside the route handler | Repeated calculation |
| 5 | **Career insights recompute 30 in-process matches + a billed AI call on every request** | `career_insights_service.py:369-370, 425` | Repeated calculation; unnecessary AI calls |
| 6 | **No batch match endpoint** — the architecture forces N round-trips | Route inventory: only `GET /api/jobs/{id}/match` exists | Architectural |
| 7 | **AI call blocks the HTTP request for up to 30 s** | `routes/resume.py:48` inline; `AI_TIMEOUT_SECONDS = 30` | Blocking operation |
| 8 | **`GET /api/resume/analysis` filters on unindexed `resumes.user_id`** | Live schema: only `ix_resumes_id` exists | Missing index (immaterial at current scale) |
| 9 | **`applications.status` not indexed**; not queried by status today | Live schema | Latent |
| 10 | **No resume-deletion path, so PII `raw_text` accumulates indefinitely** | No `DELETE` route | Data retention |
| 11 | **`_notifications` / no response compression configured** | `next.config.mjs` has no `headers()` | Minor |
| 12 | **Job lists return the full `JobResponse` including `description` for every item** | `schemas/job.py` + `GET /api/jobs` | Oversized payload (10 demo jobs hide this; a real feed would not) |
| 13 | **`useProfile` fires two independent requests on mount** | `profile/page.js:261-264` | Duplicate fetching |
| 14 | **Ingestion has no batching or chunking** | `job_ingestion.py:86-95` loops and flushes per record | Scalability (latent) |

**Positives — the backend is genuinely well-optimised where it matters:**
- `selectinload` on `Job.skills` / `Job.qualifications` in both `routes/jobs.py:112,135` and via `search_jobs` → **no N+1 on the job read path**.
- `career_insights_service.fetch_active_jobs` deliberately reuses `search_jobs` rather than writing its own query, and the docstring calls out "no N+1" explicitly.
- Indexes are well chosen for the job filters that matter: `source`, `work_mode`, `employment_type`, `city`, `posted_at`, `is_active`, `external_id`.
- Unique constraints on `job_skills(job_id, normalized_name)` and `job_qualifications(job_id, normalized_qualification)` prevent duplicate requirement rows.
- `SavedJob`/`Application` unique `(user_id, job_id)` pairs are indexed with `user_id` leading, so per-user listings are index-covered.
- `engine = create_engine(..., pool_pre_ping=True)` — resilient to dropped connections.

**Net assessment:** the *backend* is efficient; the *client-driven composition* is the bottleneck. Every significant performance problem traces back to the same root cause — matching is exposed only as a single-job endpoint, so the frontend must fan out.

---

## 20. Code Quality

### Serious (worth addressing)

| # | Item | Location |
| --- | --- | --- |
| Q1 | **Committed one-shot debug scripts** — 3 files, hardcoded fake keys, no tests, no tooling | `backend/probe_gemini_factory.py`, `backend/probe_gemini_pytest_side.py`, `backend/bin/probe_gemini.py` |
| Q2 | **Dead legacy module** with docstrings claiming AI is unimplemented | `backend/app/services/ai_service.py` |
| Q3 | **Two conflicting matching implementations** live simultaneously, one unauthenticated | `backend/app/services/matching_service.py:44-72` + `POST /api/matching` |
| Q4 | **Three false frontend comments** describing unwired code as placeholders | `applicationService.js:3`, `resumeService.js:3`, `jobService.js:7-8` |
| Q5 | **Misleading log message** misclassifying provider errors as validation errors | `career_insights_service.py:317-318` |
| Q6 | **`docker-compose.yml` cannot build** — `build: ./backend` and `build: ./frontend`, no Dockerfile in either | `docker-compose.yml:20,32` |
| Q7 | **652 deprecation warnings** from `datetime.utcnow()` across 5 modules | see S9 |
| Q8 | **Dead settings** — `LLM_API_KEY` and `JOBS_API_KEY` declared, referenced nowhere | `config.py:29-30` |
| Q9 | **Unreachable DB columns** — `user_preferences.preferred_work_mode`, `.preferred_job_type` in no schema | live schema vs `schemas/profile.py` |
| Q10 | **`profile_source = "resume_extracted"` is never set by any code path** | `models/profile.py:31` |

### Minor cleanup

- Dead frontend: `JobDetails.jsx`, `ResumePreview.jsx`, `utils/validators.js` (3 exports), `authService.logout`, `applicationService.updateApplicationStatus`, `constants.js` `JOB_TYPES`/`WORK_MODES`/`APP_NAME`, `ThemeProvider` `toggleTheme`/`resolvedTheme`, `useProfile` preference save flags, `jobService` `options`/`signal` passthrough.
- Duplicated vocabulary in 3 places (backend `job_fields.py`, frontend `lib/constants.js`, frontend `profile/page.js`) — see F4.
- Duplicated status vocabulary in 2 places with no cross-check — see P4.
- Unused imports: `career_insights_service.py` imports `Resume` (used in a type hint) — fine; `schemas/profile.py` imports `Optional` (used). No significant unused-import cluster found.
- Hardcoded demo URLs: `https://careeros-demo.example/apply/*` ×10 (`providers/demo.py`) — intentional and clearly labelled.
- Stale `__pycache__` dirs and `.pytest_cache` present locally but correctly gitignored.
- `base.py:57,61` `NotImplementedError` — `NotImplementedError` used where `AIOutputError` would be more precise for the abstract/default `generate_career_insights`.

**Overall quality assessment.** The code is well above typical prototype standards: type hints throughout, module docstrings that state *design rules* rather than restating the code, deliberate comments explaining **why** (e.g. `provider.py:115` "Body is deliberately not included: it may echo the request"; `resume_service.py:147-149` on flush ordering; `conftest.py:1-9` on the historical test-DB collision), typed exception hierarchies, and no `Any`-typed business logic. The weaknesses are **consistency and lifecycle** issues — legacy code never removed, comments never updated after wiring, duplicate definitions never consolidated — rather than structural or algorithmic ones.

---

## 21. Documentation

24 markdown files in `docs/`, 4204 lines. Extensive phase-by-phase record-keeping (Phases 0–9 plus UI and UI.1). **Materially drifted from the code.**

### Verified false/outdated claims

| # | Claim | Doc location | Contradicting evidence |
| --- | --- | --- | --- |
| D1 | "4 Alembic migrations at head `313a54989d0d`" | `CAREEROS_COMPLETE_SYSTEM_AUDIT.md:22,842,846,1183` | 5 migrations, head `a1b2c3d4e5f6`; `alembic heads` output |
| D2 | "245 tests; 244 passed, 1 failed — `test_get_ai_provider_returns_gemini_provider`" | `CAREEROS_COMPLETE_SYSTEM_AUDIT.md:24,853,1222` | 274 collected, 274 passed |
| D3 | Per-module test table (17 rows) | `CAREEROS_COMPLETE_SYSTEM_AUDIT.md:857-875` | Wrong in **15 of 17** rows; `test_profile_api.py` (15 tests) missing entirely |
| D4 | "`AI_BASE_URL` defaults to `https://api.openai.com/v1` → Gemini hits OpenAI → 401" | `CAREEROS_COMPLETE_SYSTEM_AUDIT.md:31,879-880,1203`; `PHASE_7_3_REPORT.md` (whole); `PHASE_8_REPORT.md` §root cause | `config.py:44` is `""`; `provider.py:183-184` sets the Gemini URL; live HTTP 200 |
| D5 | "`user_preferences` completely unrouted and unused; profile editing is a placeholder" (15+ claims) | `CAREEROS_COMPLETE_SYSTEM_AUDIT.md:29,406-417,722,914,928,943,967,1007,1016,1119,1128,1147-1149,1207-1208,1224,1240-1242` | `routes/profile.py:28-96` (4 endpoints), `models/profile.py`, real UI form, 15 tests |
| D6 | "`careeros.db` contains 0 jobs; not yet seeded" | `CAREEROS_COMPLETE_SYSTEM_AUDIT.md:536` | 10 jobs, 5 users, 3 resumes |
| D7 | "Use `GEMINI_API_KEY` or `OPENAI_API_KEY`" | `CAREEROS_COMPLETE_SYSTEM_AUDIT.md:1215` | Neither name exists anywhere; the setting is `AI_API_KEY` |
| D8 | `POST /jobs/{job_id}/save` "persistence not yet wired (Phase 5)" | `API_DOCUMENTATION.md:82` | Fully implemented; `GET /saved`, `DELETE /save` also exist |
| D9 | `resumes` documented as `id, user_id, file_name, raw_text, uploaded_at` | `DATABASE_SCHEMA.md:11` | Also has `total_experience_years`, `analysis_status` |
| D10 | Education/experience/certification column lists | `DATABASE_SCHEMA.md:13-15` | Missing 10 columns added by `c821c44ae290` |
| D11 | `user_profiles` table | `DATABASE_SCHEMA.md` (entire file) | **Absent from the doc**; created by `a1b2c3d4e5f6` |
| D12 | Preferences limited to 3 fields | `DATABASE_SCHEMA.md:25-26` | 14 columns after Phase 9 |
| D13 | "Phase 5 will add server-side scoring" | `ARCHITECTURE.md:294` | Phase 5 shipped without it; still deferred |
| D14 | "Saving is deliberately not wired so the UI never fakes a save" | `ARCHITECTURE.md:305-306` | Fully implemented |
| D15 | "AI: provider-agnostic LLM integration (reserved, not yet implemented)" | `PROJECT_OVERVIEW.md:35-36` | Shipped in Phase 3 |
| D16 | "matches it against **live job listings**" / "approved job data sources" | `PROJECT_OVERVIEW.md:15,21` | Demo data only |
| D17 | "AI analysis, real job providers, advanced matching, and most dashboard data flows are planned but not implemented" | `PROJECT_OVERVIEW.md:39-43` | Only "real job providers" remains true |
| D18 | 13 of 16 steps marked 🔜 (not implemented) | `USER_FLOW.md:11-28` | All implemented except real job providers |
| D19 | "Phase 8 — Platform: email, OAuth"; "Phase 9 — Testing" | `DEVELOPMENT_ROADMAP.md:98-100` | **Numbering collision** — the repo's `PHASE_8_REPORT` is Gemini stabilisation, `PHASE_9_REPORT` is Profile & Preferences |
| D20 | Roadmap "Planned" section lists only Phases 7–10 | `DEVELOPMENT_ROADMAP.md:91-102` | Omits 7.1, 7.2, 7.3, 8, 8.1, 9, UI, UI.1 — 8 shipped reports |
| D21 | "Status: Phases 0-7 complete" | `README.md:7` | 7.1 through UI.1 also shipped |
| D22 | Docs index lists only `PHASE_0`–`PHASE_7_1` | `README.md:237-247` | Omits 10 documents including both audits and 8 phase reports |
| D23 | "`AI_PROVIDER` — `openai`, `mock`, or empty" | `README.md:172-174` | `gemini` is supported and is the **currently configured value** |
| D24 | "`cp .env.example .env` from `backend/` and `frontend/`" | `README.md:129,156` | Neither directory contains `.env.example`; the copy must be made from the repo root |
| D25 | "Login 401 detail is `'Invalid email or password'`" | `RESUME_UPLOAD_AUDIT.md:73`, `frontend/lib/api.js:64` | Backend returns `'Invalid credentials'` |
| D26 | Root `.env.example` | — | Omits `APP_NAME`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ALLOWED_ORIGINS` |
| D27 | `backend/.env.example` claims to be "the full list of expected variables" (`config.py:1-14`) | — | Omits `LLM_API_KEY`, `JOBS_API_KEY` |
| D28 | `Pandas, NumPy` listed as backend stack | `PROJECT_OVERVIEW.md:33`, `README.md:101` | Present in `requirements.txt`, **never imported** anywhere |
| D29 | "17 routes" build claims (13 documents) vs "16 routes" (audit) | `PHASE_1:180`, `PHASE_3:154`, `PHASE_4:95`, `PHASE_5:161`, `PHASE_6:215`, `PHASE_7:223`, `PHASE_7_1:198`, `PHASE_7_2:192`, `PHASE_8:207`, `PHASE_9:111`, `PHASE_UI:189`, `PHASE_UI1:110`, audits | Three mutually inconsistent numbers; actual build output = **17**, but the sources contain 15 route files (14 pages + 1 route handler) — the count included `/_not-found` inconsistently |
| D30 | `PHASE_7_3`, `PHASE_8`, `PHASE_8_1` headers: "working tree only, uncommitted, no push" | those 3 docs | The work **is** committed in `f5fb003` and `2b3392b` |
| D31 | `/about` and `/contact` described as designed sections | `PHASE_UI_REPORT.md:92` | Both pages literally say "placeholder" in their rendered output |
| D32 | `.gitignore` un-ignores `.vscode/extensions.json` | `.gitignore:67` | That file does not exist |

**Still accurate:** "no real external job APIs" (audit `:28,1198`), "no UI for application status editing" (audit `:30,1223`; `README.md:88-92`), "recommendations require 16 requests" (audit `:1018,1226`), "no scheduled sync" (audit `:1211`), "no `DELETE /api/resume`" (audit `:1209`), "`POST /api/matching` is legacy" (audit `:1199`), the `AUTHENTICATION_AUDIT.md` conclusions, and the `RESUME_UPLOAD_AUDIT.md` conclusions.

### Missing documentation

`CONTRIBUTING.md` · `LICENSE` · `CHANGELOG.md` · deployment guide (production `DATABASE_URL`, secret management, `ALLOWED_ORIGINS`, migration-on-deploy) · `docs/TESTING.md` · `docs/TROUBLESHOOTING.md` (needed for `ai_failed`, Gemini throttling, CORS origins) · `docs/SECURITY.md` (bcrypt cost, 24 h token lifetime, no-revocation policy, no-logging policy) · frontend architecture doc (no equivalent of `ARCHITECTURE.md` for the `services/`/`hooks/`/`components/` conventions) · API response-schema reference (`ApplicationOut`, `ResumeOut`, `CareerInsightsResponse`, `ProfileOut`, `PreferencesOut` — the last two entirely undocumented) · a single authoritative environment-variable reference · an ERD or migration-to-model mapping.

**Nothing in `docs/` was modified by this audit.**

---

## 22. Deployment Readiness

| Area | Status | Evidence |
| --- | --- | --- |
| Containerisation | **Not implemented** | `docker-compose.yml:20,32` reference build contexts with no `Dockerfile` in `backend/` or `frontend/`. `docker compose up` **cannot work**. |
| PostgreSQL | **Needs work** | `psycopg2-binary` installed; `docker-compose.yml:8` provisions `postgres:15-alpine`; but the dev DB is SQLite and **the entire 274-test suite has only ever run against `sqlite://`** (`conftest.py:21`). PostgreSQL dialect behaviour is unverified. Also: compose pins 15-alpine while `README.md:121` says "PostgreSQL 14+" as a prerequisite. |
| Migrations | **Ready** | Single head, linear chain, zero drift, env resolution correct (`alembic/env.py:27-39`). |
| Secrets | **Needs work** | `.env` gitignored; `ENVIRONMENT=production` correctly rejects placeholder `JWT_SECRET`, `mock` provider, and missing `AI_API_KEY`. **But** `JWT_SECRET` is not currently set, so the app silently runs on the dev fallback; and `env_file=".env"` is CWD-relative (§A5). No secret manager, no rotation story. |
| CORS | **Needs work** | Correct explicit allow-list with production refusal of `mock`; but defaults are localhost-only, so a real frontend origin must be added and there is no documentation telling an operator how. |
| Frontend API URL | **Ready** | `NEXT_PUBLIC_API_URL` single variable (`lib/api.js:3`, `frontend/.env.example:1`), correct `NEXT_PUBLIC_` prefix for build-time inlining. |
| Production build | **Ready** | `next build` succeeds; 17/17 static-generation steps; 87.1 kB shared JS; largest route 7.44 kB. |
| Static assets | **Not implemented** | `frontend/public/` contains only `.gitkeep` — no logo, favicon, or OG image. `metadata` in `app/layout.js:4-8` is a bare object. |
| File uploads | **Needs work** | Working (PDF/DOCX, size/type/magic-byte validation, memory-only via `await file.read()`). But: whole file buffered in memory, no `Content-Length` pre-check, no `python-multipart` spooling limits, and no storage of the file itself (so no re-processing without re-upload). |
| AI configuration | **Needs work** | Config layer is excellent (per-provider defaults, production guards, graceful degradation, all error categories handled). Blocked in practice by upstream 429/503 with no retry (§A1). |
| External job APIs | **Not implemented** | Demo provider only; no scheduler. |
| Error handling | **Mostly ready** | Backend: typed exceptions → clean HTTP codes with human-readable details; AI failures never surface to users. Frontend: no timeout, no retry, no `AbortSignal` in `lib/api.js`. |
| Logging | **Not implemented** | No logging configuration anywhere in `app/main.py`. Default Uvicorn levels only. `logger.warning("...: %s", exc)` calls exist but go to the root logger unconfigured. No request IDs, no structured output, no correlation. |
| Rate limiting | **Not implemented** | None on any endpoint, including `/api/auth/login` (S7). |
| Security headers | **Not implemented** | `next.config.mjs` sets only `reactStrictMode` and `images.remotePatterns`. No CSP, HSTS, `X-Frame-Options`, or `Referrer-Policy`. |
| CI/CD | **Not implemented** | No `.github/`, no workflow, no test/lint gate. |
| Health checks | **Partial** | Backend `/api/health` is a static 200 — no DB or provider probe. Frontend `/api/health` (`app/api/health/route.js`) returns a hardcoded `{status:"ok"}` and does **not** call the backend, so it cannot detect a backend outage. |

### Verdict

**Not production-ready.** The application layer is in good shape (clean build, clean tests, zero schema drift, correct config guards), but the operational layer is absent: it cannot be containerised, deployed, monitored, rate-limited, or secured at the edge. `docs/DEVELOPMENT_ROADMAP.md:101-102` correctly lists containerisation and CI/CD as *planned* — the presence of a non-functional `docker-compose.yml` is the misleading part.

---

## 23. Issues & Root Causes

### BLOCKER

---

#### Issue B1 — No retry or backoff on AI provider throttling

**What is wrong.** `OpenAICompatibleProvider._chat` (`app/services/ai/provider.py:90-95`) issues exactly one `httpx.post`. HTTP 429 and 5xx are converted straight to `AIRequestError`, which `pipeline.run_resume_analysis` turns into `status="ai_failed"` and persists. No retry, no backoff, no jitter, no circuit breaker.

**Evidence.**
- `provider.py:110-113` — `if response.status_code == 429: raise AIRequestError(...)` with no second attempt.
- Live probe: `HTTP/1.1 503 Service Unavailable` ×2, then `HTTP 429` ×2, on the same endpoint that returned **200** moments earlier.
- Live smoke: `AI extraction failed (category=rate_limit, error=AI provider rate limit exceeded.); using deterministic parse.` twice during resume upload.
- `GET /api/resume/analysis` → `analysis_status: 'ai_failed'`; `POST /api/resume/analyze` retry → also `ai_failed`.
- `backend/careeros.db`: **3 of 3** resumes have `analysis_status = 'ai_failed'`, including a genuine 4596-char PDF CV. The 4th resume, created by this audit's smoke test in the throwaway copy, is also `ai_failed` — **no AI analysis has ever succeeded in this environment.**
- HEAD commit message: *"AI API Tried to Fix but still not fixed"*.

**Root cause.** The provider was fixed to the point of being *correct* — base URL, model id, key, request shape and parsing are all verified working (HTTP 200). What remains is that the free-tier key is throttled and the client treats a transient, retryable condition as terminal. The previous fixes addressed configuration; this is a resilience gap that configuration cannot solve.

**Impact.** AI resume extraction and AI career-insights explanation are effectively **never** available in practice. This cascades: no dated experience → no `total_experience_years` → the 20%-weighted Experience Match component is permanently `unknown` (§R1) → overall scores are systematically depressed for every user.

**Dependency.** AI Resume Analysis, AI Career Insights, Experience Match (20% of the overall score), `total_experience_years` persistence, and the quality of skill gaps / career directions.

**Suggested next action.** Instrument first (fix A2 so provider errors are distinguishable from validation errors). Then decide deliberately whether to add bounded retry with exponential backoff on 429/503, move the call off the request path (background task + status polling, which `analysis_status` already models), switch to a key/plan that is not throttled, or accept AI as best-effort and make the deterministic path carry experience dates.

---

#### Issue B2 — No real job provider; product served entirely demo data

**What is wrong.** `get_active_provider()` (`app/services/providers/__init__.py:15-22`) unconditionally returns `DemoJobProvider()`. 10 fictional listings with reserved-TLD apply links.

**Evidence.** `providers/__init__.py:22` — `return DemoJobProvider()`. `providers/demo.py:1-6` — *"none of these jobs are real postings and the companies are invented."* `GET /api/jobs` → `"source": "demo"`, `application_url: "https://careeros-demo.example/apply/demo-10"`. `JOBS_API_KEY_PRESENT = False`, and `JOBS_API_KEY` is referenced nowhere. `requirements.txt` has no scheduler library.

**Root cause.** Not yet implemented — and not yet designed. The abstraction, normalizer, ingestion upsert, search layer, and CLI were all built ahead of a provider that was never added.

**Impact.** Every value the product presents as market signal is synthetic: skill gaps ("Required by N relevant jobs"), career directions, `average_match`, dashboard recommendations. `PROJECT_OVERVIEW.md:15,21` advertises "live job listings", so the documentation over-promises. Apply links are dead (§J4).

**Dependency.** Job Discovery, Real Job APIs, Career Insights relevance, Recommendations, Skill Gaps, and the credibility of every score shown to a user.

**Suggested next action.** Select a provider; implement the existing `JobProvider` contract; switch `get_active_provider()` to be configuration-driven off the already-present `JOBS_API_KEY`; decide the refresh strategy (scheduled job vs on-demand) before writing provider code, because it determines whether `ingest_jobs` needs chunking (§J5).

---

### HIGH

---

#### Issue H1 — Deterministic parsing can never yield total experience, so the Experience Match component is permanently unavailable

**What is wrong.** `resume_parser.py:352-357` hard-codes `start_date`/`end_date`/`location`/`currently_employed` to `None`/`False`. `resume_service.py:109` computes `total_experience_years` only from AI output; `:112` sets `None` on the fallback path.

**Evidence.** `resume_parser.py:356-357` — `"start_date": None, "end_date": None, "currently_employed": False`. `resume_service.py:112` — `resume.total_experience_years = None`. Live DB: all 3 resumes in `backend/careeros.db` (and the 4th in the smoke copy) have `total_experience_years = NULL`. Live match response: `"experience_match_percentage": null, "experience_status": "unknown"`. `matching_service.py:99` — `experience_years = resume.total_experience_years`. `matching_engine.py:186-193` — returns `(None, "unknown")`.

**Root cause.** Date extraction was deliberately deferred ("*deterministic parser never guesses dates/roles*", `:352`) on the assumption that AI would supply dates. Because AI is unreliable (§B1), the assumption does not hold, and the fallback path has no way to recover.

**Impact.** With AI down, the 20%-weighted experience component is dead and the overall score silently becomes a skill+qualification average. Users are shown lower, less accurate scores with no indication that a component was unavailable. The fully-implemented, 44-unit-tested `experience_match` function is effectively unreachable in production.

**Dependency.** Job Matching (overall score accuracy), Career Insights, Dashboard recommendations, Resume page display.

**Suggested next action.** Determine whether deterministic date extraction from the experience section is feasible for the CV formats in scope, and whether the UI should disclose when a component is unknown. Interacts directly with B1 — if AI retry is solved, the impact shrinks but the structural fragility remains.

---

#### Issue H2 — Empty password accepted at registration

**What is wrong.** `UserCreate.password: str` has no constraints whatsoever.

**Evidence.** `app/schemas/user.py:10-11` — `class UserCreate(UserBase): password: str`. `app/api/routes/auth.py:19-27` hashes and stores it unconditionally. **Live: `POST /api/auth/register {"name":"x","email":"...","password":""}` → HTTP 200**, account created. No minimum length, no maximum length, no complexity, no confirmation field. `README.md` and the security docs claim bcrypt hashing as a protection; hashing an empty string provides none.

**Root cause.** `password` was typed as a bare `str` and no `Field(...)` constraints were ever added. Never caught because the test suite registers with fixture passwords that all satisfy an unstated policy.

**Impact.** Accounts can be created with no credential at all. Combined with the absence of rate limiting (S7), login is brute-forceable. Any real deployment inherits this.

**Dependency.** Authentication, and therefore every authenticated feature.

**Suggested next action.** Add explicit Pydantic constraints (min length, sane max ≤ 72 bytes given the `bcrypt==4.0.1` pin at `requirements.txt:16`), add a test for the empty/short/over-long cases, and confirm the frontend `RegisterForm` communicates the policy.

---

#### Issue H3 — Email is not normalised; login is case-sensitive

**What is wrong.** Registration and login both compare `User.email == payload.email` with no normalisation.

**Evidence.** `app/api/routes/auth.py:15` (register duplicate check) and `:32` (login lookup). `app/models/user.py:13` — `email = Column(String, unique=True, index=True, nullable=False)` with no functional/citext index. **Live: registered `UPPERca47fa@example.com`; `POST /api/auth/login` with `UPPERCACA47FA@EXAMPLE.COM` → HTTP 401 "Invalid credentials".**

**Root cause.** No normalisation step (`strip().lower()`) on either the write or the read path. SQLite's default `VARCHAR` comparison is case-sensitive, so `users.email` uniqueness is enforced case-sensitively too.

**Impact.** Two accounts can exist for the same mailbox, differing only in case. A user who types their address with different capitalisation is permanently locked out of their own account with a misleading "Invalid credentials". Duplicate-account support tickets are inevitable.

**Dependency.** Authentication; indirectly Saved Jobs, Applications, Resume, Profile — all keyed to `user_id`.

**Suggested next action.** Normalise email to a canonical form (lowercase, trimmed) on registration and login, and consider a functional index or `citext`/case-insensitive unique constraint so existing mixed-case rows cannot violate uniqueness.

---

#### Issue H4 — `UserProfile` and `UserPreference` are write-only

**What is wrong.** Both models are persisted via `PATCH /api/profile` and `PATCH /api/profile/preferences`, but **nothing in the application ever reads them.**

**Evidence.** Repository-wide grep across `backend/app/**` for `UserPreference|get_preferences|preferences` returns matches only in `models/application.py`, `models/user.py`, `api/routes/profile.py`, `services/profile_service.py`, `schemas/profile.py`. Same for `UserProfile|profile_service`. `matching_engine`, `matching_service`, `job_search`, `career_insights_service`, `saved_job_service`, `application_service` contain **zero** references. Live: `PATCH /api/profile/preferences {"preferred_roles":["Data Analyst"],"preferred_work_modes":["remote"],"salary_min":500000}` → **200**, and the row was verifiably written — the smoke copy's `user_preferences` table went from **0 rows** to **1 row** holding exactly `('["Data Analyst"]', '["remote"]', 500000.0)`. The write path works completely. The defect is that nothing ever reads it back: `backend/careeros.db` still holds **0** `user_preferences` rows and **1** `user_profiles` row even though both are editable from the same page, because no query in the application depends on them.

**Root cause.** Phase 9 shipped the storage and CRUD layer. The consumers — preference-aware recommendation ranking, preference-aware job filtering, preference-aware insights — were never built, and the docs of the time described the feature as complete.

**Impact.** Users invest effort in 11 preference fields for zero effect. The product cannot honestly claim personalised recommendations. The most-collected user data in the system is currently inert. `user_prefiles.profile_source` (designed to distinguish manual vs resume-extracted data) exists with no consumer and no writer for the `"resume_extracted"` value.

**Dependency.** Recommendations, Career Insights, Job Discovery filtering, Dashboard.

**Suggested next action.** Decide whether preferences are meant to (a) filter/rank the recommendation candidate set server-side, (b) bias skill-gap prioritisation, or (c) only pre-fill job-search filters. Whichever is chosen, the read path belongs behind `matching_service`/`job_search` rather than in the frontend, and a test should assert preferences actually influence output.

---

#### Issue H5 — Recommendations cover only the newest 15 jobs and cannot be ranked server-side

**What is wrong.** `useJobRecommendations.js:43` fetches `page=1&page_size=15` sorted `date_newest`, scores those 15, and returns the top 5. There is no server-side ranking endpoint.

**Evidence.** `hooks/useJobRecommendations.js:43-59`. `lib/constants.js:40-49` — `MAX_LIST_MATCHES = 12` with the comment *"Phase 5 replaces this with server-side scoring so the whole result set can be ordered by match"*, and `RECOMMENDATION_CANDIDATES = 15`. `SORT_OPTIONS` (`job_search.py`) contains only `date_newest`, `date_oldest`, `salary_desc` — no match key. `GET /api/recommendations` → **404**. `GET /api/dashboard` → **404**.

**Root cause.** Matching is exposed only as `GET /api/jobs/{id}/match`, a single-job endpoint. There is no way to order a result set by a computed score, so the frontend must fetch a page and score it. The 15-candidate bound was chosen to keep the fan-out tolerable, which is the right trade-off *given the constraint* — but it caps relevance.

**Impact.** With 10 demo jobs this is invisible. With any real feed (hundreds to thousands of listings), a strong match posted three days ago is never considered, and every user sees recommendations drawn from the same newest-15 slice. Recommendation quality degrades silently as the corpus grows.

**Dependency.** Recommendations, Dashboard, Job list sorting by match, Career Insights (shares the engine).

**Suggested next action.** Add a server-side scoring/ranking path — either a `GET /api/jobs?sort=match` backed by a scored query, or a batch `POST /api/jobs/match` accepting a list of ids, or a dedicated recommendations endpoint that applies user preferences (H4). This also collapses 16 requests into 1 and would resolve the N+1 in §19.

---

#### Issue H6 — AI errors are mislogged as validation failures

**What is wrong.** `career_insights_service.py:317-319` catches `AIProviderError` and `ValidationError` in the same `except` and logs a single message about validation.

**Evidence.**
```python
except (AIProviderError, ValidationError, ValueError, TypeError):
    logger.warning("Careers AI output failed validation; using deterministic analysis.")
```
Live log during the smoke test: `Careers AI output failed validation; using deterministic analysis.` — emitted in a run where the actual cause was HTTP 429 rate limiting, confirmed by the concurrent line `AI extraction failed (category=rate_limit, ...)`.

**Root cause.** The two failure classes have opposite diagnoses — one is a provider/credential/quota problem, the other is a schema/contract problem — but were merged for brevity. The resume pipeline (B1) does this correctly: it has a separate `except AIProviderError` branch that logs `exc.category`, and a distinct `except (ValidationError, ValueError, TypeError)` branch. The insights path never received the same treatment.

**Impact.** Actively misleads debugging. A maintainer investigating "AI not working" sees "failed validation" and goes looking at the Pydantic schema and the prompt, when the cause is quota. This is a plausible direct contributor to the "tried to fix, still not fixed" cycle described in the HEAD commit.

**Dependency.** AI Career Insights observability; indirectly all AI debugging.

**Suggested next action.** Split the exception handling to mirror `app/services/ai/pipeline.py:126-137`, logging `exc.category` for provider errors. Ensure provider errors, validation errors, and unexpected errors are distinguishable in logs.

---

#### Issue H7 — No UI to change application status

**What is wrong.** The applications page renders status as a static badge with no control.

**Evidence.** `components/applications/ApplicationStatus.jsx:27-33` — a bare `<span>` with no `<select>`, `<button>`, or `onChange`. `hooks/useApplications.js:4-7` imports only `getApplications` and `createApplication`. `services/applicationService.js:15-19 updateApplicationStatus()` is unreferenced anywhere. Backend is fully functional: **live `PATCH /api/applications/{id} {"status":"interview"}` → 200** with the updated record; invalid status → 422; no auth → 401.

**Root cause.** Phase 5 shipped the full backend and the read-only list UI; the status-editing control was never built. `README.md:88-92` documents the gap honestly.

**Impact.** A user can record an application but can never progress it. `in_review`, `interview`, `offer`, and `rejected` — 4 of the 5 states, and every state a user actually cares about — are unreachable through the product. Application tracking is therefore write-only in practice, mirroring H4 at the UI layer.

**Dependency.** Applications, Dashboard `ApplicationStats`/`RecentApplications` (which will always show 100% `applied`).

**Suggested next action.** Add a status `<select>` (or dropdown) to `ApplicationCard`, wire it to the existing `updateApplicationStatus`, and refresh the local list from the server response. The status vocabulary already exists in both layers (`ApplicationStatus.jsx:5-19` and `app/utils/validators.py`) — consider sourcing both from a shared constant.

---

#### Issue H8 — Three committed one-shot debug scripts with no place in the repo

**What is wrong.** `backend/probe_gemini_factory.py`, `backend/probe_gemini_pytest_side.py`, and `backend/bin/probe_gemini.py` are ad-hoc investigation harnesses committed to the repository.

**Evidence.** `git ls-files` confirms all three are tracked. `probe_gemini_factory.py:22-23` — `settings.AI_API_KEY = "AIza-probe"` (a fake key, harmless, but noise). `bin/probe_gemini.py:1-4` — docstring *"One-shot: why does pytest see openai when the factory reads gemini?"*. They print facts to stdout and assert nothing.

**Root cause.** Debugging artefacts created during the Phase 7.3/8 Gemini investigation were committed instead of being converted into real tests or discarded. The three associated phase reports all state the work was "uncommitted, no push", which is no longer true.

**Impact.** Minor direct impact, but real indirect harm: they imply the Gemini question is still open (it is not — §9 proves the configuration correct), they duplicate coverage that `tests/test_ai_resume_pipeline.py:242-257` already provides properly as assertions, and they confuse the next reader about the project's actual state.

**Dependency.** None functionally. Affects repository clarity and the accuracy of the historical record.

**Suggested next action.** Remove them, or convert the useful assertions into the test suite (where equivalent tests appear to already exist) and delete the scripts. Correct the "uncommitted" headers in `PHASE_7_3_REPORT.md`, `PHASE_8_REPORT.md`, and `PHASE_8_1_REPORT.md`.

---

#### Issue H9 — No frontend tests, and a non-functional lint script

**What is wrong.** Zero frontend tests of any kind, and `npm run lint` cannot run.

**Evidence.** `frontend/package.json:5-10` defines `scripts: { dev, build, start, lint }`. `devDependencies` are `autoprefixer`, `postcss`, `tailwindcss` — **no `eslint`**. No `.eslintrc*` or `eslint.config.*` exists. `npx next lint` drops into an interactive first-run setup prompt (`? How would you like to configure ESLint?`) and cannot complete non-interactively. No `test` script; no jest/vitest/playwright/cypress dependency or config. Meanwhile 34 `"use client"` components, 10 hooks, and 7 services carry the entire user-facing product. Two `eslint-disable-next-line` comments already exist (`useJobs.js:76`), implying linting was once configured and then lost.

**Root cause.** Tooling was configured for the backend (274 tests, pytest.ini, a migration-contract test) but never mirrored on the frontend. The `lint` script was declared without installing or configuring ESLint.

**Impact.** All frontend regression risk is unmitigated: no test guards the match-percentage rendering rules (`formatters.js:23-28` returns `null` rather than fabricate `0%` — a subtle rule worth protecting), the 401-message logic, the profile/preferences round-trip, or the recommendations fan-out. `npm run lint` failing non-interactively means it cannot be used as a CI gate, so the script provides false assurance. `next build` still reports "Linting and checking validity of types" — which succeeds vacuously, since there is no lint config and no TypeScript.

**Dependency.** Every frontend subsystem.

**Suggested next action.** Decide whether to add ESLint config + dependency, or remove the `lint` script so it does not imply a gate that does not exist. Frontend testing is a larger decision (unit for `lib/` pure functions and hooks, integration for the profile and applications flows) and is noted here rather than prescribed.

---

### MEDIUM

---

#### Issue M1 — `env_file=".env"` is CWD-relative, so misconfiguration fails silently

**What is wrong.** `config.py:58` uses `SettingsConfigDict(env_file=".env")`, resolved against the process working directory.

**Evidence.** `app/core/config.py:58`. Running from any directory other than `backend/` loads **no** environment file. Silent fallbacks: `DATABASE_URL` → `postgresql://user:password@localhost:5432/careeros` (`config.py:23`) and `AI_PROVIDER` → `""` (`config.py:41`), i.e. **AI silently disabled with no warning**. Note `alembic/env.py:9-13` already solves exactly this problem for Alembic.

**Root cause.** A relative `env_file` was used where an absolute, module-relative path (`Path(__file__).resolve().parent.parent / ".env"`) is required. Pydantic-settings resolves `env_file` against the process CWD, and nothing in the project documents the CWD requirement.

**Impact.** Any invocation from the wrong directory runs with a **placeholder PostgreSQL URL that does not exist locally**, a development JWT secret, no API key, and AI disabled — and reports no warning. The failure surfaces as an opaque connection error at first query rather than as a configuration error.

**Dependency.** Every runtime and CLI entry point (`uvicorn`, `pytest`, `alembic`, `python -m app.cli`).

**Suggested next action.** Resolve `env_file` to an absolute path from `__file__`. Add a startup log line emitting the *effective* provider, model, base URL, and whether an API key was found (never the key itself), so a silently-disabled AI path is impossible to miss.

---

#### Issue M2 — A second, unauthenticated matching implementation contradicts the production engine

**What is wrong.** `matching_service.calculate_skill_match` / `calculate_qualification_match` (`:44-72`) return **`0.0` for "job specifies no requirement"**, where the production engine returns `None` (unknown). Both are reachable at runtime on the same server.

**Evidence.** `POST /api/matching` — no auth dependency, **verified live HTTP 200**. `API_DOCUMENTATION.md` does not document it. The route file states it is kept for backward compatibility. The endpoint still carries 9 tests in `tests/test_matching.py`, all asserting the legacy `0.0` semantics.

**Root cause.** The engine was rewritten to adopt a rigorous unknown-vs-zero policy; the legacy helpers were retained for backward compatibility but were never given the new semantics, and the rewrite did not deprecate or remove the old entry point. Two answers to the same question now coexist.

**Impact.** Any consumer of `POST /api/matching` reads a materially **different, more pessimistic** score than the same user sees on `/api/jobs/{id}/match`. A job with no experience requirement scores 0 on experience there and `unknown` here. It is unauthenticated, so it can be called by anyone, and it accepts an arbitrary caller-supplied skills set — making it a free scoring oracle over a public endpoint.

**Dependency.** Public API surface; consistency of match semantics for any future integration.

**Suggested next action.** Either delete the route and its 9 legacy tests, or return `null` from the legacy helpers and add a deprecation header. Do not leave two contradictory semantics live.

---

#### Issue M3 — Resume truncation keeps only the head of the document

**What is wrong.** `AI_MAX_RESUME_CHARS = 30000` is applied as `raw_text[:max_chars]`, so a long CV loses everything after 30 000 characters — which is typically the entire experience section.

**Evidence.** `app/services/ai/prompts.py:43` — `raw_text[:max_chars]`. `config.py` default 30000. No warning is recorded when truncation occurs, and the truncation is not reported in `analysis_status` or in any response field.

**Root cause.** The limit was chosen to bound prompt size, but the strategy is head-truncation rather than section-aware extraction. Because the deterministic parser already identifies section boundaries, those boundaries were available and not used.

**Impact.** For any CV over 30 000 characters, the AI receives no employment history, so `total_experience_years` stays `None` and the Experience Match component is `unknown` — **the same failure mode as Issue H1, arriving for a second and independent reason**. Users get no indication that input was truncated.

**Dependency.** AI Resume Analysis, `total_experience_years`, Experience Match.

**Suggested next action.** Truncate per section (cap each section, preserve the structure) rather than per document, and record a `truncated: true` flag in the analysis result so the failure is visible rather than silent.

---

#### Issue M4 — The Gemini model id is a hardcoded source constant that will rot silently

**What is wrong.** `GEMINI_DEFAULT_MODEL = "gemini-3.6-flash"` is pinned in `provider.py:158` with no discovery mechanism and no fallback chain.

**Evidence.** `provider.py:158`. It currently works (HTTP 200). Meanwhile three other plausible ids probed live all fail: `gemini-2.0-flash` → 404 *"no longer available, use models/gemini-3.8-flash"*; `gemini-2.5-flash` → 404 *"no longer available to new users"*; `gemini-1.5-flash` → 404 *"not found for API version v1main"*.

**Root cause.** The model id was hardcoded when the provider was written and is not treated as a deployable, externally-versioned dependency.

**Impact.** A future Google deprecation surfaces only as `ai_failed` with no actionable signal — indistinguishable from the throttling in Issue B1. Note the probes also demonstrate that a naive "just downgrade the model" fix would fail: every older id is already unavailable.

**Dependency.** AI Resume Analysis, AI Career Insights.

**Suggested next action.** Treat the model id as configuration (`AI_MODEL` already exists and is already set from `.env`, so the constant is only a fallback), log the failing model id in the error path, and add a probe that verifies model availability separately from business requests.

---

#### Issue M5 — `JWT_SECRET` silently falls back to a hardcoded dev constant

**What is wrong.** `config.py:8` defines `DEV_ONLY_JWT_SECRET`, returned whenever `JWT_SECRET` is absent. `backend/.env` does not set `JWT_SECRET`, so the running application is signing tokens with a value that is public in the repository.

**Evidence.** `config.py:60-71`; runtime probe confirms `is_dev_default = True`. `config.py:65-69` correctly **raises** when `ENVIRONMENT=production`.

**Root cause.** A development convenience default was introduced without a loud runtime signal, so the risky state is indistinguishable from a configured one.

**Impact.** Safe today because `ENVIRONMENT=development`. The risk is that any deployment which forgets to set `ENVIRONMENT=production` **and** `JWT_SECRET` signs real, long-lived (24 h) tokens with a public constant — and nothing warns it. The production guard is the only thing standing between this and a full account-takeover vulnerability.

**Dependency.** Authentication, and every authenticated feature.

**Suggested next action.** Log a prominent warning on every start when the dev secret is in use, and add a startup assertion that rejects the dev secret unless `ENVIRONMENT` is explicitly `development`.

---

#### Issue M6 — No token revocation; logout is semantically void

**What is wrong.** `POST /api/auth/logout` returns `{"message": "Logged out"}` and invalidates nothing. The code comment concedes a blocklist would be required.

**Evidence.** `app/api/routes/auth.py:40-43`. **Verified live: HTTP 200 with no server-side effect.** The frontend never calls it (`hooks/useAuth.js:52-57` clears local state only; `services/authService.js:17-19 logout()` is unreferenced). `docs/API_DOCUMENTATION.md:15-16` acknowledges the gap.

**Root cause.** Stateless JWT was chosen; the revocation requirement was acknowledged in a comment and a doc but deferred, and the frontend was never updated to call the endpoint it does have.

**Impact.** A stolen 24-hour token is valid until natural expiry, and the user has no way to invalidate it. "Log out" is a UI-only affordance that gives a false sense of termination. This is also why no auth rate limiting (§S7) is materially worse than it would otherwise be.

**Dependency.** Authentication; user trust in the session model.

**Suggested next action.** Add a server-side revocation mechanism (token version on the user, or a short-lived access token plus a refresh token with rotation). Until then, do not present logout as a security control.

---

#### Issue M7 — No rate limiting on authentication endpoints

**What is wrong.** Unlimited password guessing against `POST /api/auth/login`. No lockout, no throttling, no audit log, no CAPTCHA.

**Evidence.** `app/api/routes/auth.py:30-37` — no limiter dependency. Repository-wide search finds no rate-limiting middleware, no `slowapi`/`limits` dependency in `requirements.txt`, and no proxy-level configuration. All other endpoints are equally unlimited, including the 15-way `/match` fan-out.

**Root cause.** Never implemented. The config layer has production guards for secrets and providers but no guard for abuse.

**Impact.** Credential stuffing against a 5-user database is trivial and unobservable. Combined with Issue H2 (empty passwords accepted) and M6 (no revocation), the authentication surface is the weakest part of an otherwise careful security posture.

**Dependency.** Authentication; also `/match` and `/resume/*` for abuse and cost control.

**Suggested next action.** Add rate limiting on `/api/auth/*` first, then on `/api/jobs/{id}/match` and `/api/resume/upload`. Log rejected attempts so brute-force is at least detectable.

---

#### Issue M8 — No caching anywhere; match results and insights are recomputed per request

**What is wrong.** Every match score, every career-insights computation, and every AI call is recomputed from scratch on each request, with no TTL, memoisation, or request coalescing.

**Evidence.** `career_insights_service.py` performs up to 30 in-process matches plus one **billed AI call** on every single `GET /api/career-insights`. `matching_service.build_candidate_profile` is re-executed inside each `/match` route handler. `useJobRecommendations` refetches on every dashboard mount and on every `refetch()`. `hooks/useJobMatches.js` scores up to 12 more jobs per job-list page.

**Root cause.** Nothing was designed with a read-through cache or a request-scoped memo boundary; correctness was prioritised and no invalidation strategy was ever specified.

**Impact.** Career Insights is billed per page view and will scale linearly in both latency and AI cost with no user-visible benefit. Combined with the dashboard's ~20 requests, this is the dominant cost driver in the application.

**Dependency.** Career Insights, Dashboard, Recommendations, AI cost.

**Suggested next action.** Memoise `build_candidate_profile` per resume identity within a request; add a short TTL cache to career insights keyed on `(user_id, resume_id, updated_at)`; only invoke AI when the deterministic output is non-empty.

---

#### Issue M9 — Resume-derived data cannot be corrected by the user

**What is wrong.** Skills, education, experience, and certifications are shown read-only with the message *"CareerOS will not overwrite changes you make here"* and instructions to re-upload. There is no `PATCH /api/resume` and no profile-level override for extracted data.

**Evidence.** `frontend/app/student-dashboard/profile/page.js` — resume-derived sections are link-only cards. No resume PATCH route exists in the endpoint inventory (§5). `user_profiles.profile_source` exists specifically to distinguish manual from resume-extracted data, but nothing ever writes `"resume_extracted"` (§13 F3, Issue L3).

**Root cause.** The original design assumed the parser would be accurate enough that correction was unnecessary. The parser is not (§R2, §R3), so the assumption no longer holds, but the read-only design was never revisited.

**Impact.** When the parser mis-extracts a company name or a certification issuer (both verified live), the user has **no way to fix it** except re-uploading and hoping for a different result. Bad data propagates into career insights and would propagate into any future application autofill.

**Dependency.** Profile, Resume, Career Insights.

**Suggested next action.** Either add explicit per-item editing with a `manual`/`extracted` origin flag, or make the parser conservative enough that its output does not need correcting. Pick one deliberately.

---

#### Issue M10 — `applied_at` is never updated and there is no status history

**What is wrong.** Changing an application status updates only the `status` column. There is no status-history table and no timestamp for any transition.

**Evidence.** `application_service.update_application_status` sets only `status`; `routes/applications.py:44-57` writes no history. **Verified live: `applied_at` was byte-identical before and after `applied → interview`.**

**Root cause.** The applications feature was built as a status *flag* rather than as a tracking timeline. A single `applied_at` column cannot represent the thing the feature is for.

**Impact.** A user cannot answer "when did I get an interview?", and the application tracker cannot compute time-in-stage, response-rate analytics, or anything the Dashboard `ApplicationStats` component would need to become genuinely informative.

**Dependency.** Applications, Dashboard `ApplicationStats` and `RecentApplications`.

**Suggested next action.** Add an `application_events` table recording `(application_id, from_status, to_status, occurred_at)` and derive current status from the latest event — or, minimally, add `last_status_change_at`.

---

#### Issue M11 — The application-status and preference vocabularies are duplicated across layers and already diverged

**What is wrong.** The same value sets are defined in three or four places with no shared contract and no test asserting they agree.

**Evidence.**
- Application statuses: backend `app/utils/validators.py:is_valid_application_status`; frontend `components/applications/ApplicationStatus.jsx:5-19` `STATUS_LABELS`. **No test compares them.**
- Work modes / employment types: backend `app/utils/job_fields.py`; frontend `lib/constants.js:1-10`; frontend `app/student-dashboard/profile/page.js:193-205` — and the local copy **omits `"temporary"`**, which both others include. **The UI cannot select a value the backend accepts.**

**Root cause.** The vocabulary was re-declared at each consumption point rather than exported once from a shared source of truth.

**Impact.** A divergence in the *rejecting* direction fails loudly (422), which is why the missing `"temporary"` is a minor annoyance. A divergence in the *display* direction fails silently: an unknown status renders as raw text with neutral styling (`ApplicationStatus.jsx:24-26`), so a bad value looks merely unstyled rather than wrong.

**Dependency.** Applications, Profile, Job filters.

**Suggested next action.** Export the vocabularies once — an API endpoint the frontend consumes, or a generated constants module — and add a test asserting the sets are identical.

---

### LOW

---

#### Issue L1 — Uploaded file bytes are discarded

**What is wrong.** Only `file_name` and the derived text are stored. `uploads/` is gitignored and never written.

**Evidence.** `app/services/resume_service.py:76` persists the parsed structure and `resumes.raw_text`; no file is written anywhere.

**Root cause.** A deliberate privacy-first decision — the implementation comment at `R4` frames it as positive.

**Impact.** Re-parsing without a re-upload is impossible. Low severity, and arguably correct given the PII concerns in §7 (S10) and §6; recorded so the trade-off is explicit rather than accidental.

**Dependency.** Resume.

**Suggested next action.** None required. If re-processing is ever needed, store encrypted with a documented retention policy.

---

#### Issue L2 — No way to delete a stored resume

**What is wrong.** No `DELETE /api/resume`. A user can only overwrite by re-uploading.

**Evidence.** Absent from the endpoint inventory (§5). Confirmed 404 for any reset-style path.

**Root cause.** Never implemented.

**Impact.** PII in `resumes.raw_text` (a real 4596-character CV is present in the dev DB) **accumulates indefinitely with no retention policy** and no user control. Also blocks the account-deletion story entirely.

**Dependency.** Resume, Profile, data-retention compliance.

**Suggested next action.** Add `DELETE /api/resume` that removes the row and its children, and add an account-deletion path.

---

#### Issue L3 — `profile_source` is a constant; the `"resume_extracted"` value is never written

**What is wrong.** `user_profiles.profile_source` was created to distinguish manual from resume-extracted data, but `upsert_profile` hard-codes `"manual"` on every update and **no code path ever sets `"resume_extracted"`**.

**Evidence.** `models/profile.py:29-31`; `services/profile_service.py:68`. Live first GET returned `profile_source: null` — the ORM default and the schema default disagree, so a never-written row reports `"manual"` in the schema while the column is `NULL`.

**Root cause.** The column anticipates a merge/conflict-resolution policy between resume-extracted and user-entered data. That policy does not exist, and neither does the resume→profile write path that would populate it.

**Impact.** Currently inert metadata that documents an unimplemented design. It is a trap: the next developer who writes a resume→profile merge will reasonably assume the discriminator is already maintained.

**Dependency.** Profile, and any future resume/profile merge.

**Suggested next action.** Either implement the merge that uses it, or drop the column until the merge exists.

---

#### Issue L4 — `user_preferences` carries legacy columns that no schema can reach

**What is wrong.** `preferred_work_mode` and `preferred_job_type` (singular) exist alongside the Phase-9 `preferred_work_modes` / `preferred_employment_types` (plural), but appear in **neither `PreferencesOut` nor `PreferencesUpdate`**.

**Evidence.** `schemas/profile.py:84` exposes `preferred_location` under the comment *"Legacy fields (exposed for completeness)"* while the two singular columns are absent entirely. Live schema confirms the columns exist.

**Root cause.** Columns were added in a migration without a corresponding schema change; the schema was only partially updated.

**Impact.** The columns are permanently `NULL` and permanently unreachable — dead schema surface that suggests functionality which does not exist.

**Dependency.** Profile.

**Suggested next action.** Drop them in a migration, or expose them deliberately and document which set is authoritative.

---

#### Issue L5 — No index on `resumes.user_id`

**What is wrong.** `GET /api/resume/analysis` filters on `Resume.user_id` on every request, but the only index is `ix_resumes_id`.

**Evidence.** Live schema: `resumes` has `ix_resumes_id` only. (`saved_jobs` and `applications` are fine — their unique `(user_id, job_id)` pairs have `user_id` leading.)

**Root cause.** Index coverage was applied to the job read path and not to the per-user resume lookup.

**Impact.** Immaterial at 3 rows. An unbounded full scan at scale, and a cheap fix.

**Dependency.** Resume.

**Suggested next action.** Add the index in the next migration.

---

#### Issue L6 — Experience dates are stored as `VARCHAR`, not `DATE`

**What is wrong.** `experience.start_date` / `end_date` are strings.

**Evidence.** Live schema; the migration notes this is deliberate to accept `YYYY-MM` partial dates.

**Root cause.** A defensible design choice for partial dates, documented as such.

**Impact.** Date arithmetic is string-based and unenforceable at the database level. `experience_duration.py` is careful to parse defensively, but invalid strings can be stored.

**Dependency.** Experience, total-experience calculation.

**Suggested next action.** Keep `VARCHAR` if partial dates are required, but add a check constraint on the format.

---

#### Issue L7 — No `NOT NULL` or `CHECK` constraint on `applications.status`

**What is wrong.** The 5-value vocabulary is enforced **only in Python**.

**Evidence.** `app/utils/validators.py:is_valid_application_status` is called from `routes/applications.py:51`. Live schema shows no constraint on the column.

**Root cause.** Validation was implemented at the application layer without a matching database constraint.

**Impact.** Any other write path — a migration, a data fix, a future admin script, a direct SQL session — can write an arbitrary string. The database, the single last line of defence, enforces nothing.

**Dependency.** Applications.

**Suggested next action.** Add a `CHECK` constraint via migration. SQLite supports it; verify on PostgreSQL too.

---

#### Issue L8 — bcrypt's 72-byte truncation is unhandled

**What is wrong.** `bcrypt==4.0.1` silently ignores bytes past 72, and the schema imposes no maximum length.

**Evidence.** `requirements.txt:16` documents the pin and the reason (`passlib 1.7.4` is incompatible with `bcrypt>=5`). `schemas/user.py:11` — bare `password: str`. **Live: a 100-character password was accepted (HTTP 200).**

**Root cause.** The library behaviour is known and documented in the requirements file but never surfaced as a schema constraint.

**Impact.** Two passwords sharing a 72-byte prefix are equivalent. Low probability, silent when it happens.

**Dependency.** Authentication.

**Suggested next action.** Add `max_length=72` (in bytes) to `UserCreate.password`, alongside the minimum length from Issue H2.

---

#### Issue L9 — `datetime.utcnow()` is deprecated and emits 652 warnings

**What is wrong.** Five modules call the deprecated `datetime.utcnow()`.

**Evidence.** `models/user.py:15`, `models/profile.py:33`, `core/security.py:19`, `resume_service.py:103`, `job_ingestion.py:83`. The test run reported **652 warnings**.

**Root cause.** Never updated after the deprecation.

**Impact.** Cosmetic today; will break on a future Python. The warning volume also drowns out any genuinely new warning.

**Dependency.** Everything that timestamps a row.

**Suggested next action.** Replace with `datetime.now(timezone.utc)`. Mechanical.

---

#### Issue L10 — No length limits on user-controlled text

**What is wrong.** `users.name` is an unbounded `VARCHAR`; `ProfileUpdate.bio` is an unbounded optional string.

**Evidence.** `models/user.py:12`; `schemas/profile.py:52`.

**Root cause.** Column lengths and schema constraints were never aligned.

**Impact.** Unbounded user-controlled text is stored and echoed back. No injection risk (React escapes), but it is an abuse and storage vector.

**Dependency.** Profile, Users.

**Suggested next action.** Add explicit max lengths at the schema layer and matching column widths at the model layer.

---

#### Issue L11 — JWT in `localStorage` with no Content-Security-Policy or security headers

**What is wrong.** The token is in `localStorage`, readable by any successful XSS, and no CSP or other security header is configured.

**Evidence.** `lib/auth.js:1-5` documents the trade-off explicitly and names the intended upgrade. `next.config.mjs:2-7` sets only `reactStrictMode` and `images.remotePatterns` — no CSP, HSTS, `X-Frame-Options`, or `Referrer-Policy`.

**Root cause.** An acknowledged v1 shortcut.

**Impact.** XSS becomes token theft. No CSP means nothing limits what an injected script can do. The mitigation is that no CSP means XSS is also easier to execute in the first place.

**Dependency.** Authentication; the whole frontend.

**Suggested next action.** Move to an httpOnly cookie, and add a CSP. The code comment already names this path.

---

#### Issue L12 — `MockAIProvider` returns empty objects and yields an optimistic status

**What is wrong.** In any non-production environment, `AI_PROVIDER=mock` returns `{}` from both methods.

**Evidence.** `AIResumeExtraction` validates `{}` successfully as all-empty lists, so the pipeline reports `status="ai_analyzed"` with a blank extraction and `total_experience_years = None`.

**Root cause.** The mock was written to satisfy schema validation rather than to be realistic, and the pipeline infers success from schema validity alone.

**Impact.** A developer testing locally sees `ai_analyzed` and concludes AI works, when nothing was extracted. Actively misleading during exactly the kind of debugging this project has been doing. (Not currently live — the configured provider is `gemini`.)

**Dependency.** Local development experience.

**Suggested next action.** Have the mock return a realistic extraction, or have the pipeline treat an all-empty extraction as a failure regardless of schema validity.

---

#### Issue L13 — Dead legacy `ai_service.py` with a misleading docstring

**What is wrong.** Two functions raising `NotImplementedError`, retained only for legacy imports, whose docstrings still state AI is *"reserved, not yet implemented"*.

**Evidence.** `app/services/ai_service.py`. AI shipped in Phase 3 (`docs/PHASE_3_REPORT.md`).

**Root cause.** Never removed after the real implementation landed.

**Impact.** A reader searching for the AI service finds a stub that says AI does not exist.

**Dependency.** None.

**Suggested next action.** Delete it.

---

#### Issue L14 — Ingestion has no batching and no cross-provider deduplication

**What is wrong.** `ingest_jobs` loops and flushes per record with no `chunk_size`, and uniqueness is scoped to `(source, external_id)` so the same real posting from two providers creates two rows.

**Evidence.** `job_ingestion.py:86-95`; unique constraint on `jobs (source, external_id)`. `DemoJobProvider.fetch_jobs()` returns its full list unbounded.

**Root cause.** Written for a 10-row demo source; scaling was deferred to "future scheduled syncs" (`:4`).

**Impact.** A real provider returning 10 000 records loads all of them into memory and issues 10 000 individual upserts. Cross-source duplicates would inflate `job_skills` counts and therefore skill-gap frequencies.

**Dependency.** Job ingestion (B2).

**Suggested next action.** Add chunking and a normalised cross-source content fingerprint before integrating any real provider.

---

#### Issue L15 — Verified dead frontend code and three false "placeholder" comments

**What is wrong.** A cluster of unreferenced modules, exports, and state, plus three comments that describe fully-wired code as unwired.

**Evidence.**
- Unreferenced: `components/jobs/JobDetails.jsx` (75 lines, superseded by `JobDetailView.jsx`); `components/resume/ResumePreview.jsx`; all 3 exports of `utils/validators.js` (the resume input uses a raw `accept` attribute instead); `authService.logout`; `applicationService.updateApplicationStatus`; `constants.js` `JOB_TYPES`/`WORK_MODES`/`APP_NAME`; `ThemeProvider` `toggleTheme`/`resolvedTheme`; the `options`/`signal` passthrough in `jobService.js:15,22` (no caller passes either); `useProfile` preference save flags.
- False comments: `services/applicationService.js:3` and `services/resumeService.js:3` both say *"Placeholder… Connect to backend"*; `services/jobService.js:7-8` says saving is *"intentionally not wired"*. **All three describe code that is fully wired.**

**Root cause.** Phase-by-phase development with no cleanup pass, and comments written at scaffolding time and never revisited.

**Impact.** `useProfile`'s dead preference flags are a genuine trap — the page shadows them with its own `prefSaving`/`prefSaved`, so a maintainer editing the hook would see no effect. The false comments actively mislead.

**Dependency.** Frontend maintainability.

**Suggested next action.** Delete the dead files and exports, and correct the three comments.

---

**Scope note.** The 37 issues above are a **curated register**, not an exhaustive index. §4–§22 additionally record secondary LOW observations that were not promoted here (shared `loading`/`error` state across two resources, no `loading.tsx`, redundant identity fetches, `experience_entries` exposed as a count rather than data, `_gap_priority` magic thresholds, `is_active` never recomputed outside ingestion, no withdrawn status, `POST /api/applications` not verifying job activity, the `> 0` recommendation filter boundary, and several duplicated `datetime` call sites). They are recorded in their sections with the same evidence standard.

---

## 24. Investigation Order

Ordered by dependency — each step makes the next one cheaper or safer. This is a diagnostic ordering, not a development plan.

**Tier 1 — Instrument first.** Fix Issue H6 (AI errors mislogged as validation failures). It costs minutes, changes no behaviour, and is the single change that would have accelerated every previous attempt at the AI problem. Until provider errors and validation errors are distinguishable in the logs, every subsequent AI investigation is guesswork. Add an effective-config startup log (M1) at the same time so a silently-disabled AI path is visible.

**Tier 2 — Confirm the blockers with the people who own them.**
- **B1 (AI throttling)** requires a decision that is not a code change: accept best-effort AI, purchase a non-throttled key, or keep the current key and add bounded retry. Establish which, then implement. Note that the code is already correct — the probes prove URL, model, key, and request shape all work (HTTP 200).
- **B2 (no real job provider)** requires a vendor decision. Select the provider *before* writing code, because the refresh strategy determines whether `ingest_jobs` needs chunking (L14). The abstraction, normalizer, upsert, search, and CLI are all already built — the integration needs no refactor.

**Tier 3 — Close security gaps.** H2 (empty password) and H3 (email normalisation) are small, self-contained, and affect every deployment. M7 (rate limiting) is the smallest change that materially reduces the blast radius of H2 and M6. L8 can ride along with H2.

**Tier 4 — Restore correctness of the score.** H1 (no deterministic experience dates) is the highest-impact remaining defect *because it is independent of B1*: even with AI fully working, the fallback path can never produce a total experience, so the 20%-weighted component stays `unknown` and the score silently becomes a two-component average. M3 is the same failure arriving by a second route. Decide whether the parser should extract dates deterministically, and whether the UI should disclose unknown components to users.

**Tier 5 — Close product gaps that are already half-built.** H7 (application status UI) has a **fully working backend endpoint** — verified 200/401/404/422 — and needs only a `<select>` wired to an existing, unreferenced service function. H4 (preferences) has a complete write path and needs a read path; the decision required is where preferences should influence output, not whether to store them. Both are cheap because the backend is done.

**Tier 6 — Address the architectural bottleneck.** H5 and the dashboard fan-out share one root cause: matching is exposed only as a single-job endpoint, so the client must fan out 15–20 requests. A batch or scored-listing endpoint collapses both. It is last because it is a larger change and its value is bounded by B2 — with 10 demo jobs, server-side ranking over the whole set is not yet meaningful.

**Tier 7 — Lifecycle and hygiene.** M8 (caching) matters mainly for AI cost once B1 is resolved. H8 (committed debug scripts), H9 (no frontend tests, non-functional lint), and the deployment gap — `docker-compose.yml` references build contexts with **no Dockerfile in either** (§Q6, §22) — are cleanup that should be batched into a single pass rather than done individually. §21's documentation corrections should be last, so they describe the code as it ends up rather than as it is now.

**Deliberately not prioritised:** M9 (resume data editing) requires a product decision — edit-in-place versus fix-the-parser — that should not be made by default. L2 (resume deletion) is low severity but is a prerequisite for any account-deletion story, so it should be picked up when that story starts rather than before.

---

## 25. Consolidated Status Matrix

### By capability

| Capability | Backend | Frontend | End-to-end | Status |
| --- | --- | --- | --- | --- |
| Authentication | Complete | Complete | Yes | **WORKING** (empty password, case-sensitivity) |
| Job listing / search / filter | Complete | Complete | Yes | **WORKING** |
| Job matching | Complete | Complete | Yes | **WORKING** (experience component `unknown`) |
| Resume upload / parse | Complete | Complete | Yes | **WORKING** (partial fidelity) |
| AI resume analysis | Complete | Complete | No | **EXTERNAL DEPENDENCY** (throttled) |
| Skills / education / certs persistence | Complete | Complete | Yes | **WORKING** |
| Total experience computation | Complete | Partial | No | **PARTIAL** (AI-dependent) |
| Saved jobs | Complete | Complete | Yes | **WORKING** |
| Application tracking | Complete | **Partial** | Partial | **PARTIAL** (no status UI) |
| Application status change | Complete | **None** | No | **PARTIAL** (backend works, no UI) |
| Career insights (deterministic) | Complete | Complete | Yes | **WORKING** |
| Career insights (AI layer) | Complete | Complete | No | **EXTERNAL DEPENDENCY** (throttled) |
| Recommendations | Partial (no ranking) | Partial (client fan-out) | Partial | **PARTIAL** |
| Profile | Complete | Complete | Yes | **WORKING** (write-only) |
| Preferences | Complete | Complete | **No** | **PARTIAL** (no consumer) |
| Real job data | **None** | Complete | No | **MISSING** |
| Dashboard | Composite | Complete | Yes | **WORKING** (~20 requests) |
| Public pages (`/about`, `/contact`) | n/a | **Placeholder** | No | **MISSING** |
| Deployment / CI | **None** | — | No | **MISSING** |

**Totals across 21 capabilities: 8 WORKING, 7 PARTIAL, 4 EXTERNAL DEPENDENCY, 3 MISSING.**

### By layer

| Layer | State | Blocking issues |
| --- | --- | --- |
| Database / migrations | Clean — single head, zero drift, 14 tables | none |
| Backend services | Coherent, deterministic, well-tested | B1, B2, M2 |
| Backend auth | Functional, carets taken | H2, H3, M5, M6, M7 |
| Frontend | Every feature wired to real endpoints, no mocks | H7, H9 |
| AI integration | Correct, graceful, observable only after H6 | B1 |
| Job data | Demo only | B2 |
| Deployment | Absent | Q6 / §22 (no Dockerfile, no CI/CD) |
| Documentation | Extensive, materially drifted | §21 (32 claims) |

### What actually works

Stated plainly, because the issue count is misleading on its own: **274 backend tests pass, the frontend builds, migrations have zero drift, all 24 endpoints respond correctly, and no user journey breaks.** The deterministic fallback path is the strongest architectural property in the codebase — a Gemini 429 during resume upload still produced a 201, five correctly extracted skills, a usable analysis, a working match, and working career insights. The problems are gaps in breadth and operational maturity, not broken foundations.

---

## 26. Terminal Summary

**Audit scope.** Read-only inspection of `CareerOS` at `main` / `2b3392b`, 2026-10-01. No source file, `.env`, migration, test, or project database row was modified. Runtime writes were confined to a copy of the database at `%TEMP%\opencode\audit_smoke.db`.

**Verification performed.** Backend suite: **274 passed, 0 failed** (112.04s). Frontend: `next build` **PASS**; `npm run lint` **cannot run** (no ESLint config or dependency); **no frontend tests exist**. Migrations: `alembic current` = `a1b2c3d4e5f6 (head)`, single head, `alembic check` = no drift. Live server: started cleanly; all 24 endpoints probed including auth failure paths, upload validation paths, and boundary conditions. Database: 14 tables inspected; both the project database and the smoke copy queried directly.

**Findings.** **37 issues: 2 BLOCKER, 9 HIGH, 11 MEDIUM, 15 LOW**, plus 32 documented false or outdated claims in `docs/`.

**The central conclusion.** The previous audit's diagnosis of the AI integration was wrong in a way that mattered. Gemini is **not misconfigured**. The base URL, model id, API key, request shape, and response parsing are all verified correct — a live probe returned **HTTP 200**. The provider is being **throttled upstream (429/503)**, and the code treats a transient, retryable condition as terminal: one request, no retry, no backoff, and the failure is persisted as `ai_failed`. Every one of the 3 resumes in `backend/careeros.db` is `ai_failed`, as is the 4th created during this audit. **No AI analysis has ever succeeded in this environment.**

**The second conclusion.** The AI problem is not the only cause of degraded results, and fixing it alone would not make matching correct. The deterministic parser deliberately never extracts employment dates, and `total_experience_years` is computed *only* from AI output. When AI fails — which is always, here — the 20%-weighted Experience Match component is permanently `unknown` and the overall score silently becomes a skill-and-qualification average. **AI is load-bearing for a third of the match score**, which makes it a correctness dependency rather than an enhancement. Issue M3 is the same failure arriving by an independent route.

**The third conclusion.** The product's personalization is inert. `UserProfile` and all 11 `UserPreference` fields are fully writable through a working UI and API — verified live, the row was written — and **nothing in the application ever reads them back.** The most-collected user data in the system currently has no consumer.

**What is genuinely solid.** The database layer, migrations, deterministic matching engine, resume parser, career-insights sanitisation layer, and error-handling taxonomy are all above typical prototype quality. Type hints throughout; docstrings that state design rules rather than restate code; comments that explain *why*; typed exception hierarchies; no `Any`-typed business logic. The 274-test suite is real coverage, not smoke tests, and the fallback design means no user journey breaks.

**What is absent.** Real job data, server-side ranking, frontend tests, deployment, CI/CD, logging configuration, rate limiting, and security headers. Two of the largest gaps are already half-built: the application-status backend works completely (200/401/404/422 verified) and needs only a `<select>` in the UI, and the job-provider abstraction, normalizer, ingestion, search, and CLI are all done and need only a vendor implementation.

**Recommended first action.** Fix the misleading AI error log (Issue H6). It is a small, behaviour-neutral change that would have accelerated every previous attempt at this problem, because it currently reports upstream rate limiting as a Pydantic schema failure.

**Documentation status.** 32 specific false or outdated claims across 24 markdown files, including the migration count, test count, profile support, the Gemini base URL claim, and the "uncommitted work" headers on three phase reports whose work is in fact committed. **No file in `docs/` was modified by this audit.**

---

*End of report.*