# CareerOS — Development Roadmap

- **Phase 0 — Foundation & Stabilization** ✅ Complete. See
  `docs/PHASE_0_REPORT.md`. Fixed the frontend login flow, added Alembic
  migrations for the full schema, hardened JWT secret configuration, aligned
  the frontend/backend job contract, added a mobile dashboard menu and active
  nav states, prevented duplicate applications (404/409) with
  `Application`/`SavedJob` → `Job` ORM relationships, and added tests for
  migrations, matching utilities, and application uniqueness/relationships.
- **Phase 1 — Core Job System** ✅ Complete. See `docs/PHASE_1_REPORT.md`.
  Replaced the placeholder job browse with a real database-backed job system:
  extended `Job` model (employment_type/application_url/city/country/dates/
  experience/is_active), new `JobSkill`/`JobQualification` relational models
  with normalization + uniqueness, a provider abstraction with a bundled demo
  provider (10 fictional jobs), a normalization layer, idempotent ingestion
  with per-run stats and `(source, external_id)` dedup, a public
  search/filter/paginate/sort API, a new Alembic migration + indexes, and a
  `python -m app.cli seed-jobs` command. 104 backend tests pass.
- **Phase 2 — Matching Engine** ✅ Complete. See `docs/PHASE_2_REPORT.md`.
  Deterministic, explainable resume↔job matching: a pure calculation engine
  (`app/services/matching_engine.py`) with skill/qualification/experience/
  overall scores, matched/missing item lists, an explicit
  unknown-vs-missing policy (never returns misleading 100s), weight-transparent
  overall scoring (50/30/20), and a deterministic summary generator. Wired to
  `GET /api/jobs/{id}/match` (auth-required, uses caller's own resume, 404 on
  missing job/resume). No schema change and no AI. 156 backend tests pass.

- **Phase 3 — AI Resume Intelligence** ✅ Complete. See
  `docs/PHASE_3_REPORT.md`. Provider-agnostic AI structured extraction
  (`app/services/ai/`: base provider interface + typed errors, httpx-based
  OpenAI-compatible provider, mock provider, JSON-only prompt, Pydantic
  validation, and a resilient pipeline) layered on the deterministic parser.
  Uploads now enrich skills/education/certifications/dated experience; a strict
  deterministic employment-duration calculation
  (`app/services/experience_duration.py`) plus schema columns power
  experience scoring in the Phase 2 engine; a retry endpoint
  (`POST /api/resume/analyze`); graceful fallback on every AI failure mode
  (`ai_failed` never breaks uploads); a reversible Alembic migration; and
  privacy by construction (no resume text/prompts/responses/keys logged).
  212 backend tests pass.
- **Phase 4 — Jobs Frontend** ✅ Complete. See `docs/PHASE_4_REPORT.md`.
  Production-quality jobs UI wired end-to-end: public `/jobs` and
  `/jobs/[id]`, and the authenticated `/student-dashboard/jobs` (matching
  surface). Search, filters, sort, pagination and a URL that stays in sync
  (back/forward + shareable links), skeleton/empty/error states, match-score
  presentation (bounded per-page, detail-page primary) with every endpoint
  state handled (sign-in, missing resume, transient error, full score), and
  Apply Now that only navigates when an application URL exists. No fake data;
  no backend changes; 212 backend tests still pass and `next build` is green.

## Completed (historical foundation phases)
- **Authentication** ✅ Real registration/login flows, JWT issuance and
  validation via a shared `get_current_user` dependency (`app/api/deps.py`),
  `GET /auth/me`, protected dashboard endpoints (resume, applications, job
  save), and a frontend `useAuth` session hook wired to real tokens/user.
  Application routes query the DB scoped to the authenticated user.
  `test_auth.py` covers `401` behavior for missing/malformed/invalid/expired
  tokens, tokens referencing nonexistent users, and cross-user ownership
  isolation on applications.
- **Resume Upload** ✅ PDF and DOCX resume parsing and persistence.
  `resume_parser.py` deterministically extracts skills, education, experience,
  and certifications from sectioned resumes using PyMuPDF and python-docx (no
  LLM). Parsed data is stored per user; re-uploading replaces the previous
  resume instead of duplicating. The resume dashboard page is wired to the
  live endpoints. `test_resume.py` covers auth, size, type, malformed/empty
  documents, and replace-on-reupload behavior.

## Planned
- **Phase 5 — Saved Jobs & Applications UI**: Wire job saving (`SavedJob` +
  `POST /jobs/{id}/save`) and the applications flow end-to-end, plus server-side
  match ordering so lists can be ranked by score.
- **Phase 6 — Dashboard & Insights**: Profile completion, recommendations, and
  stats on the student dashboard.
- **Phase 7 — Real Job Providers**: Integrate one or more approved external job
  sources behind the existing `JobProvider`/normalizer/ingestion pipeline, plus
  scheduled ingestion. Provider identity becomes config-driven
  (e.g. `JOBS_API_KEY`).
- **Phase 8 — Platform**: Email, password reset, OAuth, notifications.
- **Phase 9 — Testing**: Expand automated test coverage across frontend and
  backend.
- **Phase 10 — Deployment**: Containerize, configure CI/CD, and deploy to a
  production environment.