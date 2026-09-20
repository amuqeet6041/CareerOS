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
  extracted sub-entities, jobs (plus job skills/qualifications), saved jobs,
  applications, and preferences.
- Schema changes are managed with **Alembic migrations** (`backend/alembic/`).
  The schema source of truth is the SQLAlchemy models; `alembic upgrade head`
  (run from `backend/`) applies the current migration chain. Alembic resolves
  `DATABASE_URL` from the same configuration as the application.
- Matching utilities are laid out here but match scores are not exposed to the
  job API yet (Phase 2).

### Job Ingestion Pipeline
Jobs flow from providers into the database through a normalized pipeline:

```
External source / demo data
        │  fetch_jobs()
        ▼
JobProvider (app/services/providers/)        ── raw records, no DB/SQLAlchemy
        │  ProviderJob DTO
        ▼
Normalizer (app/services/job_normalizer.py)  ── canonicalizes employment_type
        │  NormalizedJob (validated)             & work_mode, derives city/country,
        ▼                                        raises JobNormalizationError
Job ingestion (app/services/job_ingestion.py) ── upsert keyed on (source, external_id)
        ▼
jobs (+ job_skills, job_qualifications)
```

- **Providers** implement the `JobProvider` interface
  (`app/services/providers/base.py`) and return `ProviderJob` records. They
  never touch the database. Providers that fail to fetch raise
  `JobIngestionError`, which surfaces loudly instead of being swallowed.
- **The bundled `DemoJobProvider`** (`app/services/providers/demo.py`) serves
  10 fictional jobs using invented company names and clearly-marked demo apply
  links (`careeros-demo.example`), so the whole pipeline works with no API key.
- **Normalization** maps free-form employment types/work modes to the canonical
  sets (`full-time | part-time | contract | internship | temporary | freelance`,
  `remote | hybrid | onsite`), collapses skill/qualification casing, and
  derives `city`/`country` from a free-form `location` when missing.
- **Ingestion** upserts each job (dedup key: `source` + `external_id`) and
  returns per-run stats: `fetched / inserted / updated / skipped / failed`.
  Invalid records are counted as `failed`; the valid ones still commit.
- **Search** (`app/services/job_search.py`) is a database query with
  case-insensitive matching over title/company/description/location/skills,
  filters, pagination (max `page_size` 100), and sorting. No Elasticsearch.

### Ingestion is not publicly writable
There is **no HTTP endpoint** for ingesting jobs. Ingestion runs through the
admin/CLI command `python -m app.cli seed-jobs` (from `backend/`) or
future internal schedulers. Public `GET /api/jobs` remains read-only.

### AI Integration
- The AI service module (`app/services/ai_service.py`) is intentionally
  provider-agnostic. No provider is hard-coded; configure `LLM_API_KEY` and
  implement the actual call once a provider is chosen. **Not yet implemented** —
  no AI calls are made in this phase.

### Job Data
- The `JobProvider` abstraction (`app/services/providers/`) allows new job API
  adapters to be added without touching the rest of the system. Each adapter
  exposes `fetch_jobs()` (and optionally `fetch_job(external_id)`) and returns
  `ProviderJob` records that the normalizer converts into the shared `Job`
  shape. Real external providers arrive in a later phase; until then the
  bundled `DemoJobProvider` is the active provider.
