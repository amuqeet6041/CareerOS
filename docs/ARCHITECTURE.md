# CareerOS — Architecture

## High-Level Diagram

```
┌────────────┐     HTTPS      ┌────────────┐     SQL      ┌──────────────┐
│  Frontend   │ ─────────────▶ │   Backend   │ ───────────▶ │  PostgreSQL   │
│  (Next.js)  │ ◀───────────── │  (FastAPI)  │ ◀─────────── │              │
└────────────┘                └─────┬──────┘               └──────────────┘
                                     │
                       ┌─────────────┼─────────────┐
                       ▼             ▼             ▼
                 ┌──────────┐ ┌────────────┐ ┌──────────────┐
                 │ AI Service│ │ Resume     │ │ Job Provider  │
                 │ (LLM API) │ │ Parser     │ │ Adapters      │
                 └──────────┘ └────────────┘ └──────────────┘
```

## Layers

### Frontend
- Next.js App Router with route groups for `(auth)`, `(public)`, and the
  authenticated `student-dashboard` area.
- Components are organized by domain (`auth`, `resume`, `jobs`, `dashboard`,
  `shared`).
- `services/` holds thin API-client wrappers; `hooks/` holds stateful logic
  built on top of those services.

### Backend
- FastAPI app (`app/main.py`) mounting routers under `app/api/routes/`.
- `app/core/` holds cross-cutting concerns: settings, security (JWT/password
  hashing), and the SQLAlchemy engine/session.
- `app/models/` are SQLAlchemy ORM models; `app/schemas/` are Pydantic
  request/response schemas.
- `app/services/` contains the business logic: resume parsing, AI analysis,
  job provider adapters, and matching logic.

### Data
- PostgreSQL is the system of record. Models cover users, resumes and their
  extracted sub-entities, jobs, saved jobs, applications, and preferences.
- Schema changes are managed with **Alembic migrations** (`backend/alembic/`).
  The schema source of truth is the SQLAlchemy models; `alembic upgrade head`
  (run from `backend/`) applies the current migration chain. Alembic resolves
  `DATABASE_URL` from the same configuration as the application.
- The matching utilities and the placeholder job provider are laid out here
  but the live providers/AI calls are not implemented yet (see the roadmap).

### AI Integration
- The AI service module (`app/services/ai_service.py`) is intentionally
  provider-agnostic. No provider is hard-coded; configure `LLM_API_KEY` and
  implement the actual call once a provider is chosen. **Not yet implemented** —
  no AI calls are made in this phase.

### Job Data
- The `JobProvider` abstraction in `app/services/job_service.py` allows new
  job API adapters to be added without touching the rest of the system. Each
  adapter normalizes results into the shared `Job` shape.
