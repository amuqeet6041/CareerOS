# CareerOS — Phase 0 Report (Foundation & Stabilization)

Date: 2026-09-20

## 1. What This Phase Covered

Phase 0 stabilized the existing CareerOS codebase so it can support the later
feature phases. It made the project bootable and testable end-to-end, added a
real database migration toolchain, fixed the broken frontend login flow,
hardened security defaults, aligned the job data contract between frontend
and backend, and shored up application-data integrity. No new product features
were added; every change either fixed an existing defect or prepared the
foundation for future work (see §12 for the honest status of AI/jobs/matching).

## 2. Baseline at Start

- Backend test suite: **36 passed** (`venv\Scripts\python.exe -m pytest -q`).
- Frontend production build: **success**, 17 static routes.
- No database migrations existed; `create_all` was test-only and app startup
  created nothing, so a fresh database had **no tables**.
- Frontend login was broken: `useAuth.signIn` called `getMe()` before the JWT
  was saved, so every fresh login 401'd.
- `JWT_SECRET` had an insecure default (`"change-me"`).
- `email-validator` was installed in the venv but **missing** from
  `requirements.txt`; `alembic` was not installed at all.
- No `.env` files existed (only `.env.example`).
- No PostgreSQL server was running locally.
- `docker-compose.yml` references `Dockerfile`s that do not exist.

## 3. What Changed (Files)

### Created
- `backend/alembic.ini`, `backend/alembic/env.py`,
  `backend/alembic/script.py.mako`,
  `backend/alembic/versions/9032a41514cb_initial_schema.py` — migration toolchain
  and initial full-schema migration.
- `backend/pytest.ini` (`pythonpath = .`), `backend/tests/__init__.py`,
  `backend/tests/conftest.py` — shared in-memory test database and a single
  FastAPI dependency override (see §8 for the reason).
- `backend/tests/test_migrations.py` — migration must run, produce the expected
  tables/constraints, be idempotent, and enforce uniqueness at the row level.
- `docs/PHASE_0_REPORT.md` — this report.

### Modified
- `backend/requirements.txt` — added `alembic==1.20.0` and
  `email-validator==2.3.0`.
- `backend/app/core/config.py` — JWT secret policy (see §5).
- `backend/app/models/application.py`, `backend/app/models/job.py`,
  `backend/app/models/__init__.py` — `Application.job` / `SavedJob.job`
  relationships, unique `(user_id, job_id)` constraints, central model imports.
- `backend/app/api/routes/applications.py`,
  `backend/app/services/application_service.py` — `404` for unknown jobs,
  `409` for duplicate applications (see §7).
- `backend/tests/test_auth.py`, `backend/tests/test_resume.py`,
  `backend/tests/test_matching.py` — see §8.
- `frontend/hooks/useAuth.js` — login order fix (see §5).
- `frontend/components/jobs/JobCard.jsx`, `JobDetails.jsx`, `JobFilters.jsx` —
  aligned to the backend job contract (see §6).
- `frontend/components/shared/Navbar.jsx` — removed a stray ```` ``` ```` text
  node rendered in the header.
- `frontend/components/dashboard/DashboardSidebar.jsx` — Next `<Link>` based
  nav, active-state highlighting, and a mobile menu (sidebar was previously
  hidden with no alternative on small screens).
- `frontend/components/shared/Loading.jsx` — replaced invalid Tailwind classes
  (`h-4.5`, `w-4.5`, `border-2.5`) that produced an invisible spinner.
- `.env.example`, `backend/.env.example` — documented `JWT_SECRET` requirement,
  added `ENVIRONMENT`.
- `.gitignore` — ignore `*.db` / `*.sqlite3` (keeps `backend/careeros.db` out).
- `scripts/setup_backend.bat` — runs `alembic upgrade head` after install.
- `README.md` and `docs/` (`PROJECT_OVERVIEW`, `ARCHITECTURE`,
  `DATABASE_SCHEMA`, `API_DOCUMENTATION`, `USER_FLOW`,
  `DEVELOPMENT_ROADMAP`) — accurate status, migration instructions, schema,
  API behavior.

### Deleted
- None (debug scratch files created only in the OS temp directory).

## 4. Database & Migrations

- Added **Alembic** as the migration tool. The initial migration
  (`9032a41514cb`) creates the full 10-table schema from the SQLAlchemy models.
- `alembic/env.py` resolves `DATABASE_URL` from the exact same source as the
  application (script option → env var → `backend/.env`), so `alembic upgrade
  head` always targets the configured database. Tests override the URL so a
  stray environment variable can never point a test at a real database.
- `app/models/__init__.py` now imports every model so `Base.metadata` is fully
  populated for autogenerate.
- Application startup does **not** auto-create or auto-drop tables; schema is
  created only via migrations (`venv\Scripts\alembic upgrade head`).
- Verified on SQLite: migration applies cleanly (twice — idempotent), produces
  all tables plus the `(user_id, job_id)` uniqueness constraints, and rejects
  duplicate application rows.

## 5. Authentication & Security

- **Frontend login bug fixed.** `useAuth.signIn` now saves the token before
  calling `getMe()`, so a fresh login resolves the user correctly
  (`frontend/hooks/useAuth.js`). The session-restore / sign-out paths were
  already correct and are unchanged.
- **JWT secret policy** (`backend/app/core/config.py`): the insecure
  `"change-me"` default is gone. Empty, `change-me`, and the placeholder
  `replace-with-a-secure-random-secret` are rejected:
  - `ENVIRONMENT=production` → startup fails with a clear error,
  - otherwise a named **development-only** secret is used (documented).
  - `.env.example` instructs generating a secret via
    `python -c "import secrets; print(secrets.token_urlsafe(64))"`.
- No refresh tokens, OAuth, or password changes were introduced (deferred —
  and JWT algorithm remains HS256).

## 6. Job Data Contract & UI

- The backend `JobOut` contract is authoritative: `id, title, company,
  location, work_mode, job_type, salary_min, salary_max, currency,
  description, apply_url`.
- `JobCard`/`JobDetails` no longer read nonexistent frontend-only fields
  (`skillMatch`, `qualificationMatch`, `salary`, `workMode`) and instead
  render `work_mode` / `job_type` / salary range via the existing
  `formatSalary` util (`frontend/utils/formatters.js`).
- `JobFilters` state keys now match the backend query parameters
  (`work_mode`, `job_type`), so `getJobs` serializes to the correct query
  string; added the missing `contract` job-type option.

## 7. Applications & Data Integrity

- `Application.job` and `SavedJob.job` ORM relationships added (with
  back-population on `Job`).
- Added unique `(user_id, job_id)` constraints on both `applications` and
  `saved_jobs` (via migration), preventing duplicate applications/saves.
- `POST /api/applications` now returns:
  - `404` when the referenced job does not exist (previously this would either
    silently record a dangling FK — SQLite — or crash — PostgreSQL),
  - `409` when the user has already applied to that job.
- Tests enable `PRAGMA foreign_keys=ON`, so test behavior matches PostgreSQL's
  FK enforcement.

## 8. Tests Added/Updated

- **Suite now 51 tests (was 36): 51 passed.**
- New migration tests (`tests/test_migrations.py`): 4 — upgrade creates all
  tables; uniqueness constraint present; repeat-upgrade idempotency; duplicate
  row rejected at the DB level.
- New application tests (`tests/test_auth.py`): 4 — apply to nonexistent job →
  `404`; duplicate application → `409`; two users may apply to the same job;
  `Application.job` relationship resolves.
- Matching tests (`tests/test_matching.py`): 7 — skill match partial/case- and
  requirements-edge cases dominated by **qualification-match** coverage
  (partial/full/none/empty-requirements).
- **Test-hygiene refactor:** `test_auth.py` and `test_resume.py` each created
  their own DB and overwrote the shared `app.dependency_overrides[get_db]`,
  so whichever file imported last silently replaced the other's database
  (this made suite order matter). A single shared in-memory DB now lives in
  `tests/conftest.py`, and `pytest.ini` ensures the tests package is
  importable. Existing assertions were not weakened.

## 9. Verification Results

- Backend: `51 passed` (fresh run on Windows, venv).
- Migrations: `alembic upgrade head` creates all 10 tables; verified twice and
  via the automated migration tests. (PostgreSQL not running locally — see §10.)
- Frontend: `npm run build` success, 17 static routes (same as baseline).
- Backend startup: uvicorn on a dedicated port → `GET /api/health` `200`
  (`{"status":"ok","service":"backend"}`), `/docs` `200`, no startup
  errors.
- Frontend startup: `next start` on a dedicated port → `/login` `200` and
  `/api/health` `200`.
- JWT guard: `ENVIRONMENT=production` + empty secret → `ValueError`;
  production + real secret and development fallback both verified.
- `pip install -r requirements.txt` is reproducible with the pinned additions
  (already installed in the venv and importable).

## 10. Remaining Known Issues & Notes

- **No local PostgreSQL running** — the default `DATABASE_URL`
  (`postgresql://user:password@localhost:5432/careeros`) cannot connect until
  a server is available. DB-backed endpoints and migrations against Postgres
  require creating the database and running `alembic upgrade head`. Migration
  behavior on Postgres itself was not exercised here (verified on SQLite with
  generic SQL types).
- No `.env` files are present; a fresh setup must copy the `.env.example`
  files and set real values.
- `docker-compose.yml` still references `Dockerfile`s that don't exist.
  Deliberately deferred to the deployment phase (README documents local
  setup instead).
- Pre-existing deprecation warnings remain (Pydantic class-based `Config`,
  `datetime.utcnow`) — candidates for a later cleanup pass.
- `MatchScore.jsx` is currently unused (kept as a generic display component
  for when matching ships).
- The job `Save` action on `JobCard` remains a no-op button (save-job
  persistence/UI is out of scope for this phase).
- Frontend login fix is verified by code review and API contract, not browser
  automation (no frontend test framework in the repo yet).
- `backend/careeros.db` is a legacy local SQLite artifact (now gitignored);
  it is not used by the app.

## 11. Recommendation for Next Phase

Build the first real user-facing verticals on top of the now-stable
foundation:
1. **Saved jobs + applications UI** wired to the existing backend routes
   (they already enforce ownership and deduplication).
2. **Wire the dashboard cards** to real data (profile summary, application
   stats) instead of placeholder/empty states.
3. **Real job provider** integration via the existing `JobProvider` adapter
   (fills `jobs` and makes the matches meaningful).
4. Then the **matching score API + UI** and, after that, **AI resume
   analysis**.
Parallel items: formal token rotation/revocation policy, a frontend test
framework, and replacing deprecated pydantic/datetime calls.

## 12. Honest Status of AI, Job Discovery & Matching

- **AI/LLM resume analysis:** NOT implemented. No AI provider, SDK, or API
  call exists; `LLM_API_KEY` is reserved and unused. Resume parsing is
  deterministic (PyMuPDF/python-docx text + section matching).
- **Job discovery:** NOT implemented. The `/api/jobs` route is wired to a
  placeholder provider that returns `[]`; no job data source, scraper, or
  crawler exists. `JOBS_API_KEY` is reserved and unused.
- **Matching:** Only utility functions exist
  (`calculate_skill_match`, `calculate_qualification_match` — simple,
  case-insensitive set overlap). There is no match-score API and no match UI;
  frontend cards no longer display fabricated scores.
- Saved jobs, applications UI, career insights, and dashboard analytics are
  backend-only (or empty placeholders) pending the phases above.