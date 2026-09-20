# CareerOS

A career platform that reads your resume, extracts structured information
(skills, education, experience, certifications), and will later match you to
real job opportunities with Skill Match % and Qualification Match % scores.

> **Status:** Phase 0 (foundation/migrations/tests), **Phase 1 (core job
> system)**, and **Phase 2 (deterministic matching engine)** are complete: the
> app boots, registers/logs in, uploads and parses resumes, ingests a
> database-backed job catalog (search/filter/paginate API), and matches a
> user's resume against a job with explained skill/qualification/experience
> scores. AI resume analysis, real external job providers, and the
> jobs/saved-jobs UIs are **not implemented yet** — see
> [`docs/DEVELOPMENT_ROADMAP.md`](docs/DEVELOPMENT_ROADMAP.md) and
> [`docs/PHASE_2_REPORT.md`](docs/PHASE_2_REPORT.md).

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

## Not Yet Implemented (planned phases)
- AI/LLM resume analysis (planned Phase 3)
- Live/external job provider integrations or scraping (demo provider only)
- AI-assisted/semantic matching (current engine is deterministic)
- Jobs, saved-jobs, and applications frontend UI
- Career insights / dashboard analytics
- Email, password reset, OAuth

## Tech Stack
**Frontend:** Next.js (App Router), React, Tailwind CSS, Lucide icons
**Backend:** FastAPI, Pydantic, SQLAlchemy, Alembic, Pandas, NumPy
**Database:** PostgreSQL (SQLite supported for tests)
**AI:** Provider-agnostic (reserved, not yet wired)

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
- `LLM_API_KEY`, `JOBS_API_KEY` — reserved for later phases (unused now)

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
the expected schema (including the `job_skills`/`job_qualifications` tables).

## Documentation
See [`docs/`](docs/) for architecture, schema, API, user-flow, and the phased
development roadmap. Phase reports: [`docs/PHASE_0_REPORT.md`](docs/PHASE_0_REPORT.md),
[`docs/PHASE_1_REPORT.md`](docs/PHASE_1_REPORT.md), and
[`docs/PHASE_2_REPORT.md`](docs/PHASE_2_REPORT.md).