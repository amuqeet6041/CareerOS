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

## Matching Engine (Phase 2)

### Matching flow
```
Stored resume (user)                    Job listing (public)
        │                                    │
        ▼                                    ▼
build_candidate_profile()      skill_name / qualification (display)
(matching_service.py)          minimum/maximum_experience_years
        │
        ▼
Normalized CandidateProfile ─────► app/services/matching_engine.py
                                     (pure, deterministic, no DB, no AI)
        │
        ▼
 Skill Match % │ Qualification Match % │ Experience Match % │ Overall Match %
        │
        ▼
 Summary (deterministic rule buckets + missing items)
        │
        ▼
GET /api/jobs/{job_id}/match  (authenticated, uses caller's own resume)
```

### Skill normalization
`normalize_skill`/`normalize_qualification` (reused from
`app/utils/job_fields.py`) lowercase, `strip()`, and collapse inner whitespace:
`" Python "` → `"python"`, `"Power BI"` → `"power bi"`. No synonym/thesaurus
dictionary is used, so `"B.Sc"` and `"Bachelor of Science"` are different
qualifications.

### Skill formula
```
Skill Match % = matched required skills / total required skills × 100
```
Matching is done on normalized keys, is case/whitespace-insensitive, and
deduplicates both sides. `matched_skills`/`missing_skills` report the job's
display names.

### Qualification formula
```
Qualification Match % = matched required qualifications / total required qualifications × 100
```
The candidate's qualification tokens are derived **only from stored resume
data**: each education entry contributes its `degree`, its `field_of_study`,
and (when both exist) `"{degree} in {field_of_study}"`; each certification
contributes its name. Nothing is invented.

### Experience logic
Uses the job's `minimum_experience_years`/`maximum_experience_years` against
the candidate's experience years:

- Job has neither min nor max → `no_requirement` (unknown).
- Candidate years unknown → `unknown` (never assumed to be zero).
- `min <= candidate <= max` → 100%, `meets_requirement`.
- Below min → `candidate / min × 100` (min > 0), `below_minimum`.
- Above max → `max / candidate × 100`, `above_maximum`.

The current resume schema does not store employment dates, so Phase 2 returns
candidate experience years as unknown; the rules above power unit tests and
become live when the resume model captures durations.

### Overall score weights
```
Overall Match % = skill×0.50 + qualification×0.30 + experience×0.20
```
Constants live at the top of `matching_engine.py` and the nominal weights
(`{"skill": 50, "qualification": 30, "experience": 20}`) are returned in the
API response (`component_weights`) so scores are transparent.

### Unknown / missing-data policy
- A component is **`null` (unknown)** only when the **job has no requirement**
  for it (no required skills, no required qualifications, no experience
  range). `null` never means "100 because the job asked for nothing".
- When the candidate has data that simply does not match (e.g. skills that
  match none of the required skills), the score is a **real 0** — that is
  evidence-based, not missing information.
- If the user has **no resume**, the endpoint returns 404 (no fabricated
  scores). If a resume exists but yields no parsed data, components are
  computed honestly (0 or unknown) rather than assumed.
- Missing components are excluded from the overall score and their weight is
  redistributed over the known components; overall is `null` when nothing is
  known. This never produces misleading certainty.

### Why scores are calculated on demand
Match scores are **not persisted**. There is no `match_scores`,
`job_matches`, or recommendation table — the engine is stateless and computes
a result per request (one job query with eager-loaded children + one resume
query). This keeps scores always consistent with the latest resume/job data
and avoids a schema change. Persisting/recommending scores belongs to a later
phase.

### Why AI is not involved yet
The Phase 2 engine is deliberately deterministic and explainable so results
are reproducible and testable. AI-based resume intelligence (deeper parsing,
synonym/degree-level semantics, tailored summaries) is planned for Phase 3 and
will layer on top of — not replace — this deterministic core.

### Job Data
- The `JobProvider` abstraction (`app/services/providers/`) allows new job API
  adapters to be added without touching the rest of the system. Each adapter
  exposes `fetch_jobs()` (and optionally `fetch_job(external_id)`) and returns
  `ProviderJob` records that the normalizer converts into the shared `Job`
  shape. Real external providers arrive in a later phase; until then the
  bundled `DemoJobProvider` is the active provider.
