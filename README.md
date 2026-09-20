# CareerOS

A career platform that reads your resume, extracts structured information
(skills, education, experience, certifications), and will later match you to
real job opportunities with Skill Match % and Qualification Match % scores.

> **Status:** Phases 0–3 complete: the app boots, registers/logs in, uploads
> and parses resumes, ingests a database-backed job catalog
> (search/filter/paginate API), matches a user's resume against a job with
> explained skill/qualification/experience scores, and (Phase 3) enriches
> resumes with provider-agnostic AI-structured analysis (dated experience, AI
> skill spelling, education/certification detail) that feeds — but never
> replaces — the deterministic matching engine. Real external job providers and
> the jobs/saved-jobs UIs remain **not implemented yet** — see
> [`docs/DEVELOPMENT_ROADMAP.md`](docs/DEVELOPMENT_ROADMAP.md) and
> [`docs/PHASE_3_REPORT.md`](docs/PHASE_3_REPORT.md).

## Implemented
- User registration and JWT-based login (HS256), protected routes
- Resume upload with structured extraction (placeholder parse/extract logic)
- **Core job system (Phase 1)**: database-backed jobs with provider
  abstraction, normalization, idempotent ingestion/upsert (dedup by
  `(source, external_id)`), demo job provider, migration, and a public
  browse/search/filter/paginate/sort API
- **Demo job seeding**: `python -m app.cli seed-jobs` upserts 10 fictional
  jobs (see "Seeding Demo Jobs" below)
- Application tracking backend (create/list/update), per-user scoping
- SQLAlchemy models + Alembic migrations for the full schema
- **Matching engine (Phase 2)**: deterministic, explainable resume↔job
  matching (`GET /api/jobs/{id}/match`) with skill/qualification/experience/
  overall scores, matched/missing items, and weight-transparent summaries
- **AI resume intelligence (Phase 3)**: provider-agnostic AI structured
  extraction (`skills`, `education`, `certifications`, dated `experience`)
  layered on the deterministic parser, with a typed error/fallback chain
  (`POST /api/resume/upload` + retry `POST /api/resume/analyze`), a strict
  deterministic employment-duration calculation, and AI data flowing into the
  Phase 2 matching engine

## Not Yet Implemented (planned phases)
- Real/live external job provider integrations or scraping (demo provider only)
- AI-assisted/semantic matching (AI extracts candidate *data* only; scoring
  remains the deterministic engine)
- Jobs, saved-jobs, and applications frontend UI
- Career insights / dashboard analytics
- Email, password reset, OAuth

## Tech Stack
**Frontend:** Next.js (App Router), React, Tailwind CSS, Lucide icons
**Backend:** FastAPI, Pydantic, SQLAlchemy, Alembic, Pandas, NumPy
**Database:** PostgreSQL (SQLite supported for tests)
**AI:** Provider-agnostic resume intelligence (OpenAI-compatible provider via
httpx; mock provider for dev/tests; AI optional — empty `AI_PROVIDER` = fully
deterministic)

## Project Structure
```
CareerOS/
├── frontend/     # Next.js application
├── backend/      # FastAPI application
├── backend/alembic/  # Database migrations
├── data/         # Raw/processed/sample data (gitignored except structure)
├── docs/         # Project documentation
└── scripts/      # Setup helper scripts
```

## Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 14+

## Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate                     # Windows; use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env                      # then set real values (see below)
```

## Database Setup & Migrations
Create the database (adjust for your Postgres install):
```sql
CREATE DATABASE careeros;
```

Set `DATABASE_URL` in `backend/.env`, then apply migrations from `backend/`:
```bash
cd backend
venv\Scripts\alembic upgrade head         # creates all tables
```

The migration tooling resolves `DATABASE_URL` from the same place as the
application (backend/.env), so migrations always target the configured
database. To create a new migration after model changes:
```bash
venv\Scripts\alembic revision --autogenerate -m "describe change"
venv\Scripts\alembic upgrade head
```

## Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
```

## Environment Variables
See `backend/.env.example`, `frontend/.env.example`, and the root
`.env.example`. Never commit real secrets.

Key variables:
- `DATABASE_URL` — PostgreSQL connection string (also used by Alembic)
- `JWT_SECRET` — signing secret for access tokens. **Required** in
  production (`ENVIRONMENT=production` fails startup if it is empty or a
  placeholder). Generate with:
  `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- `ENVIRONMENT` — `development` (default) or `production`
- `NEXT_PUBLIC_API_URL` — URL the frontend uses to reach the backend
- `LLM_API_KEY`, `JOBS_API_KEY` — reserved (unused now)
- `AI_PROVIDER` — `openai` (any OpenAI-compatible `/chat/completions` endpoint
  via httpx), `mock` (dev/tests only), or empty to disable AI (default).
  Setting `AI_PROVIDER=openai` in production requires `AI_API_KEY`.
- `AI_API_KEY`, `AI_MODEL`, `AI_BASE_URL`, `AI_MAX_RESUME_CHARS`,
  `AI_TIMEOUT_SECONDS` — AI resume analysis configuration (see
  `backend/.env.example`). No key is needed for the test suite or for
  deterministic operation.

## How to Run
### Backend
```bash
cd backend
uvicorn app.main:app --reload
```
Docs at http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm run dev
```
App at http://localhost:3000

### Health Check
`GET http://localhost:8000/api/health` → `{"status": "ok", ...}`

## Seeding Demo Jobs
The job catalog starts empty. To load the bundled fictional demo jobs (10
postings across fictitious companies — clearly-marked demo apply links, no
real companies or external APIs), run from `backend/`:

```bash
cd backend
set DATABASE_URL=sqlite:///./careeros.db   # or your Postgres URL; also read from backend/.env
venv\Scripts\python.exe -m app.cli seed-jobs
```

Seeding is idempotent — running it again updates or skips instead of
duplicating (dedup key: `source` + `external_id`). Report:
`fetched=10 inserted=10 updated=0 skipped=0 failed=0`.

## Running Tests
```bash
cd backend
venv\Scripts\python.exe -m pytest -q
```
Tests use an in-memory SQLite database — no Postgres required. They also run
`alembic upgrade head` against a temp SQLite DB to verify migrations produce
the expected schema (including the Phase 2 `job_skills`/`job_qualifications`
tables and Phase 3 resume-analysis columns). The AI pipeline is tested with the
mocked provider — no real API key required.

## AI Resume Analysis (Phase 3)
Enabled entirely by configuration — nothing changes if it's off:
1. Leave `AI_PROVIDER` empty in `backend/.env` for deterministic-only parsing.
2. Set `AI_PROVIDER=openai` (+ `AI_API_KEY`) to enable provider-agnostic,
   OpenAI-compatible structured extraction on every upload.
3. Test locally without a key: `AI_PROVIDER=mock` (development only).

AI never breaks a workflow: every failure (timeout, bad key, malformed output)
falls back to the deterministic parse with `analysis_status="ai_failed"`, and
`POST /api/resume/analyze` retries on the stored resume text. Only status and
error *category* are logged — resume text, prompts, responses, and keys are
never logged.

## Documentation
See [`docs/`](docs/) for architecture, schema, API, user-flow, and the phased
development roadmap. Phase reports: [`docs/PHASE_0_REPORT.md`](docs/PHASE_0_REPORT.md),
[`docs/PHASE_1_REPORT.md`](docs/PHASE_1_REPORT.md),
[`docs/PHASE_2_REPORT.md`](docs/PHASE_2_REPORT.md), and
[`docs/PHASE_3_REPORT.md`](docs/PHASE_3_REPORT.md).