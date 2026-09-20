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
- **Phase 2 — Matching Engine**: Expose Skill Match % and Qualification Match %
  for jobs against a user's resume, as a scored counterpart to the Phase 1 job
  catalog (reuse `matching_service`; upgrade `JobMatchOut`, which is currently
  removed from the API surface).
- **Phase 3 — AI Resume Analysis**: Connect an LLM provider for deeper resume
  analysis beyond the deterministic structured extraction (keyword
  suggestions, tailored summaries).
- **Phase 4 — Jobs Frontend**: Wire the public and dashboard jobs pages to
  `GET /api/jobs` (search, filters, pagination, detail, apply).
- **Phase 5 — Saved Jobs & Applications UI**: Wire job saving (`SavedJob` +
  `POST /jobs/{id}/save`) and the applications flow end-to-end, plus any new
  backend work needed.
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