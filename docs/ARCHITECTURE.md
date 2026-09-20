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

### AI Resume Intelligence (Phase 3)
The AI layer (`app/services/ai/`) extracts **structured information only** from
resume text. It never computes match scores, never recommends, and never
scrapes or invents data.

```
Raw resume text (from the deterministic parser)
        │
        ▼
app/services/ai/pipeline.py   run_resume_analysis(raw_text) -> (structured | None, status)
        │
        ▼
provider.get_ai_provider() ──► None (AI disabled)            → status "parsed"
        │
        ├──► OpenAICompatibleProvider (httpx → /chat/completions)
        │      · strict JSON-only prompt (app/services/ai/prompts.py)
        │      · you get what's in the text; no scoring/guessing instructions
        ├──► MockAIProvider (development/tests only; refused in production)
        ▼
app/services/ai/schemas.py   AIResumeExtraction (Pydantic validation)
        │
        ▼
structured_to_persist()      dedupe skills by normalized key (same as matching),
                             compute deterministic experience years, persist shape
        ▼
resume_service.save_resume(..., analysis_status, structured)
```

- **Provider abstraction** (`base.py`): `AIProvider` interface plus typed
  errors — `AIConfigurationError`, `AIRequestError` (timeout / unavailable /
  invalid key / rate limit), `AIOutputError` (unparseable body). Responses and
  resume text are never logged; only the error *category* is.
- **Factory** (`provider.py`): `get_ai_provider()` returns `None` when
  `AI_PROVIDER` is empty (fully deterministic), the configured provider, or
  raises `AIConfigurationError`. `Settings` refuses `AI_PROVIDER` in production
  without `AI_API_KEY` and disallows `mock` in production.
- **Validation** (`schemas.py`): dates are normalized to strict `YYYY-MM`
  (`YYYY-MM-DD`/`MM/YYYY` accepted and truncated); anything unrecognized stays
  `None` so downstream code treats it as *missing*, never guesses. Education
  `institution` became nullable so entries without an institution still persist.
- **Fallback guarantee**: every AI failure mode (config, provider, timeout,
  non-JSON, schema-invalid, enrichment) degrades to the deterministic parse
  with `analysis_status = "ai_failed"`. Uploads never break because of AI.
  `POST /api/resume/analyze` retries AI on the stored `raw_text` and, if it
  fails again, preserves the existing data untouched.
- **Statuses**: `parsed` (deterministic only), `ai_analyzed`, `ai_failed`.
- **Privacy**: the prompt never includes job data (the model cannot tailor
  answers to any employer). Resume text, prompts, and provider responses are
  never logged. `LLM_API_KEY` reserved name remains but the active setting is
  `AI_API_KEY`.

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

Since Phase 3, candidate experience years come from the resume's deterministic
`total_experience_years` (set by the AI pipeline from validated `YYYY-MM`
employment dates via `app/services/experience_duration.py`). It stays `None`
(unknown) whenever any date is missing, malformed, or inconsistent — never
assumed to be zero.

### Experience-duration policy (`app/services/experience_duration.py`)
- Each job counts its start month inclusive and end month exclusive:
  `2024-01 → 2025-01` is exactly 12 months (1.0 year).
- `currently_employed` roles run through the current month; end dates in the
  future are clamped to the current month.
- Overlapping and adjacent jobs are merged so shared months are not double
  counted.
- If ANY job's interval is unreliable (missing/malformed start, missing end
  that is not "current", end before start, start in the future), the total is
  `None` — unknown, not zero. No jobs at all is also `None`.
- Years = merged months / 12, rounded to 2 decimals.

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

### Why AI never computes scores
The Phase 2 engine is deliberately deterministic and explainable so results are
reproducible and testable. Phase 3 AI resume intelligence (structured
skills/education/certifications/experience with dates) layers on top of — not
replaces — this deterministic core: AI supplies candidate *data*, and the
engine turns that data into scores using the same fixed rules. No AI provider
is ever asked for a percentage, a match reason, or a recommendation.

### Job Data
- The `JobProvider` abstraction (`app/services/providers/`) allows new job API
  adapters to be added without touching the rest of the system. Each adapter
  exposes `fetch_jobs()` (and optionally `fetch_job(external_id)`) and returns
  `ProviderJob` records that the normalizer converts into the shared `Job`
  shape. Real external providers arrive in a later phase; until then the
  bundled `DemoJobProvider` is the active provider.

## Jobs Frontend (Phase 4)

Two surfaces are wired to the backend through a single client orchestrator:

```
             ┌────────────────────────────────────────────────┐
             │           JobsExplorer (client)                │
             │  · reads the URL query string as filter state   │
             │  · pushes every filter/sort/page change back to │
             │    the URL (router.replace, no-op guarded)      │
             │  · loading/empty/error/pagination states        │
             └──────┬────────────────────────────┬─────────────┘
                    │                            │
        GET /api/jobs (public + dashboard)       │
                    │                            │
                    ▼                            ▼
   jobService.getJobs → { items, total, page,    jobService.getJobMatch (job detail match,
        page_size, total_pages }                 dashboard list matches)
```

- **URL as state**: `lib/jobQuery.js` maps between the query string and the
  filter object consumed by `useJobs`. `queryToFilters`/`filtersToQuery` keep
  values as strings so URL → filter → URL round-trips losslessly. Back/forward
  navigation and shared paginated links work because `useJobs` re-applies the
  external filter key when it changes (and never clobbers it when identical).
- **No per-keystroke requests**: free-text search commits on submit (Enter or
  the Search button, `JobSearch`); the filter panel collects edits in a local
  draft and commits only on **Apply Filters**; selects (work mode, employment
  type, sort) apply immediately on change. Filter/sort changes restart at
  page 1; explicit pagination keeps the current position.
- **List matches are bounded**: `useJobMatches` computes match status for the
  *visible page only* (`MAX_LIST_MATCHES = 12`), and only in the dashboard
  variant for authenticated users. The primary match presentation lives on the
  job detail page (`useJobMatch`); Phase 5 will add server-side scoring to
  order the full result set. Match data is React state only — never cached in
  the database (scores stay on-demand per the backend design).
- **Match never guesses**: `MatchScore`/`MatchCard` render every state of the
  match endpoint — `sign-in` (login CTA), `no-resume` (upload CTA to the
  resume dashboard), transient `error` (retry), or the full score. Unknown
  components are labelled **Not enough data** in visible text (never 0%),
  and the backend's `component_weights` are shown so overall scores stay
  transparent.
- **Apply Now** navigates to `application_url` in a new tab
  (`target="_blank" rel="noopener noreferrer"`); without a URL the control is
  disabled with an explanatory title. Saving is deliberately **not** wired
  (Phase 5 persistence) so the UI never fakes a save.
- **No fake data**: every card/score/company comes from the live API. Lists
  show skeletons while loading, a retryable error state, and a "Clear filters"
  empty state. The public surface reuses the marketing dark band (`#07111F`)
  with the existing light app theme for the results area; both routes wrap the
  client explorer in `<Suspense>` so `/jobs` stays statically prerendered.
- **Routes**: `/(public)/jobs` (public browse), `/(public)/jobs/[id]`
  (detail + match), `/student-dashboard/jobs` (authenticated matches). The
  retired dead services (`saveJob`) were removed; the demo contract
  (`careeros-demo.example` apply links) is unchanged.
