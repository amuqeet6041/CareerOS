# CareerOS

A career platform that reads your resume, extracts structured information
(skills, education, experience, certifications), and will later match you to
real job opportunities with Skill Match % and Qualification Match % scores.

> **Status:** Foundation/Phase 0 is complete: the app boots, registers/logs in,
> uploads and parses resumes, exposes a jobs API (placeholder provider), has
> database migrations, and a passing test suite. AI resume analysis, real job
> providers, and matching UIs are **not implemented yet** — see
> [`docs/DEVELOPMENT_ROADMAP.md`](docs/DEVELOPMENT_ROADMAP.md).

## Implemented
- User registration and JWT-based login (HS256), protected routes
- Resume upload with structured extraction (placeholder parse/extract logic)
- Placeholder job browse/filter API (`/api/jobs`) — returns `[]` until a real
  job provider is integrated
- Application tracking backend (create/list/update), per-user scoping
- SQLAlchemy models + Alembic migrations for the full schema
- Matching utilities (skill/qualification overlap) as reusable functions

## Not Yet Implemented (planned phases)
- AI/LLM resume analysis
- Live job provider integrations / scraping / crawling
- Advanced matching & match-score APIs
- Saved-jobs and applications frontend UI
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

## Running Tests
```bash
cd backend
venv\Scripts\python.exe -m pytest -q
```
Tests use an in-memory SQLite database — no Postgres required. They also run
`alembic upgrade head` against a temp SQLite DB to verify migrations produce
the expected schema.

## Documentation
See [`docs/`](docs/) for architecture, schema, API, user-flow, and the phased
development roadmap. The Phase 0 report is at
[`docs/PHASE_0_REPORT.md`](docs/PHASE_0_REPORT.md).