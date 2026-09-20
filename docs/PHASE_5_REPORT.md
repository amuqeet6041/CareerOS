# Phase 5 Report — Saved Jobs & Applications

## Objective
Turn saving and applying into real, persisted, end-to-end flows: save/unsave
jobs via the existing `SavedJob` model, track every application a signed-in
user starts via the existing `Application` model, and build the Saved Jobs and
My Applications dashboard pages. No fakes, no localStorage, no new persistence
layer — the backend already had the tables, uniqueness constraints, and the
application routes; this phase completes the missing saved-job endpoints, makes
application responses self-sufficient, and wires the UI.

## Audit (start of phase)

### A. Existing SavedJob backend functionality
- `SavedJob` model (`app/models/application.py`) with tables already created by
  migration `9032a41514cb` (`saved_jobs`), unique `(user_id, job_id)`
  constraint `uq_saved_jobs_user_job`, `saved_at`, and ORM relationships on
  `User.saved_jobs`, `Job.saved_jobs`.
- Only **one** endpoint existed: `POST /api/jobs/{job_id}/save` returning a
  placeholder message ("... saved ... (placeholder)") — it never persisted and
  its test (`test_save_job_requires_auth_and_returns_placeholder`) asserted a
  fake success.
- **Missing:** a real save implementation, an unsave route, and any way to list
  a user's saved jobs.

### B. Existing Application backend functionality
- `Application` model with unique `(user_id, job_id)`, `status` (default
  `applied`), `applied_at`; statuses restricted to
  `applied | in_review | interview | offer | rejected` by
  `ALLOWED_APPLICATION_STATUSES`.
- Routes in `app/api/routes/applications.py`: `GET /api/applications` (list,
  auth), `POST /api/applications` (`{job_id}` → 201, 404 missing job, 409
  duplicate), `PATCH /api/applications/{id}` (`{status}` → 422 invalid, 404).
  Auth via `get_current_user`, always scoped to the caller. Well tested in
  `test_auth.py` (auth, cross-user isolation, 404/409/422, patch).
- **Missing:** `ApplicationOut` carried no job data, so a frontend list would
  need N detail requests (or render nothing).

### C. Existing frontend functionality
- `applicationService.js` already called `GET/POST /api/applications` and
  `PATCH /api/applications/{id}` — but **nothing consumed it**; the
  Applications page was a static placeholder ("Wire up to
  applicationService.js").
- `saved-jobs/page.js` was a Phase 4 placeholder EmptyState ("coming soon").
- Phase 4 `JobCard` had no save control; `ApplyButton` was a passive `<a>`.
  `getSavedJobs`/`saveJob`/`unsaveJob` did not exist in any service.

### D. Missing pieces required for Phase 5
- Backend: real `POST /{job_id}/save` (409 on duplicate, 404 if job missing),
  a `DELETE /{job_id}/save` (idempotent 204), `GET /api/jobs/saved` (auth,
  newest-first, job embedded), a `SavedJobOut` schema, and embedded job data on
  `ApplicationOut` with eager loading (avoid N+1).
- Frontend: saved-job + application services/hooks, a reusable save control and
  an apply control that records tracking before opening the external URL,
  real Saved Jobs and My Applications pages, status badges, and wiring into the
  card lists and detail page.

## Backend Changes
- `app/schemas/job.py` — added `SavedJobOut` (`id`, `job_id`, `saved_at`,
  `job: JobResponse | None`).
- `app/schemas/application.py` — `ApplicationOut` now embeds
  `job: JobResponse | None` (additive; the existing contract is untouched).
- `app/services/saved_job_service.py` — **new**: `create_saved_job`,
  `get_saved_job`, `delete_saved_job` (idempotent), `list_saved_jobs`
  (newest-first, eager-loads job + skills + qualifications).
- `app/api/routes/jobs.py`:
  - `GET /api/jobs/saved` (auth) → `list[SavedJobOut]`; declared **before**
    `/{job_id}` so the literal segment wins.
  - `POST /api/jobs/{job_id}/save` → 201 `SavedJobOut`; 404 missing job; 409
    already saved.
  - `DELETE /api/jobs/{job_id}/save` → 204, idempotent; 404 missing job.
- `app/services/application_service.py` — `list_applications` eager-loads the
  job (skills + qualifications) so the embedded `ApplicationOut.job` is served
  without N+1 detail queries.
- No schema change and no migration: `saved_jobs`/`applications` tables and
  constraints already existed from Phase 0.

## API Contract (saved jobs)
| Method | Path | Auth | Success | Errors |
| --- | --- | --- | --- | --- |
| GET | `/api/jobs/saved` | required | 200 `SavedJobOut[]` (newest first) | 401 |
| POST | `/api/jobs/{id}/save` | required | 201 `SavedJobOut` | 401, 404 job, 409 duplicate |
| DELETE | `/api/jobs/{id}/save` | required | 204 | 401, 404 job |

Unauthenticated requests to any of these return 401 before any work happens.

## Frontend Changes
### New files
- `frontend/services/savedJobService.js` — `getSavedJobs`, `saveJob`,
  `unsaveJob` (token attached by `apiFetch`).
- `frontend/hooks/useSavedJobs.js` — single `GET /api/jobs/saved` loads a
  `savedIds` Set (one request per surface, never per card); `toggle(jobId,
  saved)` mutates backend-first and only updates state **after** success.
- `frontend/hooks/useApplications.js` — same pattern for applications:
  `appliedIds` Set, `createApplication`, `markApplied` (used after a 409 so the
  UI converges without duplicating records).
- `frontend/components/jobs/SaveJobButton.jsx` — Save/Saved toggle with busy,
  disabled (while the saved list loads), `aria-pressed`, and aria-labels
  (`Save {title}` / `Remove {title} from saved jobs`); shows inline error on
  API failure; renders a **sign-in link** for unauthenticated users.
- `frontend/components/jobs/ApplyNowButton.jsx` — apply + tracking. External
  URL is opened **synchronously** in the click handler (popup-safe); for
  authenticated users `createApplication` runs in the background so the job
  appears in My Applications. States: Apply / Applying… / Applied (409
  converges to Applied). No fake submission ever.
- `frontend/components/applications/ApplicationStatus.jsx` — color + always
  visible text badges for the five backend statuses.
- `frontend/components/applications/ApplicationCard.jsx` — one tracked
  application with embedded job (title, company, location, work mode, applied
  date, status, View Job, Open application); muted fallback if the job was
  removed.

### Modified files
- `frontend/components/jobs/JobCard.jsx` — added save control and
  applied-aware apply; new props (`saved`, `applied`, `saveDisabled`,
  `authenticated`, `onToggleSave`, `onApplyTracked`).
- `frontend/components/jobs/JobList.jsx` — pass-through of the above from a
  `savedIds`/`appliedIds` Set and callbacks.
- `frontend/components/jobs/JobsExplorer.jsx` — dashboard variant mounts
  `useSavedJobs` + `useApplications` (auth only); public variant passes
  `authenticated` so unauth users get sign-in links instead of failed saves.
- `frontend/components/jobs/JobDetailView.jsx` — Apply section now records
  tracking (`My Applications` copy only for signed-in users) and adds an
  explicit save control.
- `frontend/app/student-dashboard/saved-jobs/page.js` — real saved-jobs list
  (skeleton/error/empty/unsave-inline, unavailable-job fallback card).
- `frontend/app/student-dashboard/applications/page.js` — real My Applications
  list (skeleton/error/empty).
- Removed `frontend/components/jobs/ApplyButton.jsx` (superseded by
  `ApplyNowButton`; verified no other consumers).
- `docs/DEVELOPMENT_ROADMAP.md`, `README.md` (below).

## Flow & UX Decisions
- **Signed-in Apply** → creates the tracking record then opens the employer's
  `application_url` in a new tab; the job now shows under My Applications. A
  duplicate attempt (409) is not an error — it converges to the Applied state.
- **Signed-out Apply** → unchanged behavior from Phase 4: the external URL
  opens immediately, no record (backend requires auth). Copy on the detail page
  reflects this.
- **Save state** is derived from one `GET /api/jobs/saved` per surface
  (dashboard list, detail page, saved-jobs page) — never per card. While that
  list loads, the save button is disabled so it can't act on stale state.
- Errors from save/unsave/apply-tracking show inline and never masquerade as
  success.
- Statuses are shown exactly as the backend reports them (`applied`, etc.);
  there is no client-side status editing.

## PHASE 5 STATUS
- **Backend**: saved-job endpoints fully implemented and tested; application
  responses embed the job with eager loading. No schema changes; no migrations
  added.
- **Frontend**: all four surfaces wired — public + dashboard card lists
  (save/apply state), public + dashboard detail page (save + tracked apply), a
  real Saved Jobs page, and a real My Applications page.
- **Saved Jobs**: save, unsave (idempotent), saved list newest-first for the
  authenticated user; per-user isolation.
- **Applications**: create on Apply, list, status update; interacts with the
  existing PATCH endpoint for future status changes.
- **Tests**: `python -m pytest -q` → **222 passed, 0 failed** (212 baseline +
  10 new: 8 saved-jobs, 2 application-embed).
- **Build**: `npm run build` → **17 routes**, compiled with no errors.
  `/student-dashboard/saved-jobs` and `/student-dashboard/applications` are now
  real client-rendered pages.
- **Files created**: `app/services/saved_job_service.py`,
  `tests/test_saved_jobs_api.py`, `tests/test_applications_api.py`,
  `frontend/services/savedJobService.js`, `frontend/hooks/useSavedJobs.js`,
  `frontend/hooks/useApplications.js`,
  `frontend/components/jobs/SaveJobButton.jsx`,
  `frontend/components/jobs/ApplyNowButton.jsx`,
  `frontend/components/applications/ApplicationStatus.jsx`,
  `frontend/components/applications/ApplicationCard.jsx`, `docs/PHASE_5_REPORT.md`.
- **Files modified**: `app/schemas/job.py`, `app/schemas/application.py`,
  `app/api/routes/jobs.py`, `app/services/application_service.py`,
  `tests/test_jobs_api.py`, `frontend/components/jobs/JobCard.jsx`,
  `JobList.jsx`, `JobsExplorer.jsx`, `JobDetailView.jsx`,
  `frontend/app/student-dashboard/saved-jobs/page.js`,
  `frontend/app/student-dashboard/applications/page.js`,
  `docs/DEVELOPMENT_ROADMAP.md`, `README.md`.
- **Files removed**: `frontend/components/jobs/ApplyButton.jsx` (replaced by
  `ApplyNowButton`).
- **Known limitations**:
  - List matches remain per-page (no server-side ordering yet; that was already
    deferred to this phase and is the only remaining Phase 5 item — Phase 6+ or
    a small follow-up).
  - Application status changes are not editable in the UI (the backend PATCH is
    ready); the applications page reflects whatever the backend reports.
  - Inactive/expired saved jobs still list (with their `is_active` flag) rather
    than being hidden; removed jobs render a "no longer available" card.

## Live API Smoke (this session)
Fresh temp SQLite DB (`%TEMP%\opencode\phase5_smoke.db`, tables created,
`seed-jobs` = 10 demo rows), uvicorn on :8001:
- 401 on unauthenticated `GET /api/jobs/saved`, `POST/DELETE /api/jobs/1/save`,
  `GET /api/applications`.
- Register + login → save a real job → **201** with job embedded
  (`job.title`, `skills`); `GET /api/jobs/saved` lists it newest-first;
  duplicate save → **409**; `DELETE` → **204**; list empty after; unsave of a
  missing job → **404**.
- Applications: **201** (`status=applied`, `job.title` embedded) → duplicate →
  **409** → list shows 1 → `PATCH` to `interview` → 200.
- Server stopped; temp DB removed; dev `careeros.db` untouched.

## Exact Review Commands
```bash
# Backend tests (from backend/)
python -m pytest -q

# Frontend build (from frontend/)
npm run build
```
Backend suite: 222 passed, 0 failed. `npm run build`: 17 routes, success.