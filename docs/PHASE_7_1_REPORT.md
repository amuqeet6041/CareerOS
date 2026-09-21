# PHASE 7.1 REPORT — Database Schema Integrity & Alembic Reconciliation

**Status:** COMPLETE
**Date:** 2026-09-21
**Scope:** Non-destructive reconciliation of the development database schema with
the authoritative SQLAlchemy models and the Alembic migration chain. No product
features added, no application behavior changed.

---

## 1. Background & Scope

Phase 7.0 finished with a manually repaired `backend/careeros.db` (tables/columns
created via `create_all(checkfirst)` + `ALTER TABLE`, then `alembic stamp head`).
That left a known drift: the database was *stamped* at the migration head while
its physical schema still lagged the schema the migration chain declares. This
phase made the actual schema, the models, and the migration chain agree again —
without deleting the database, dropping/recreating tables, deleting user data,
resetting migration history, or modifying the three pre-existing migration files.

## 2. Audit Method

Three independent sources were compared for every table:

1. **SQLAlchemy models** (`backend/app/models/`, source of truth for the app)
   and the `Job` `__table_args__` indexes.
2. **Alembic migration chain final state** — derived by running
   `alembic upgrade head` against a throwaway temp SQLite DB and inspecting it,
   plus full reads of all three migration files.
3. **Actual development database** (`backend/careeros.db`) — full read-only dump:
   `sqlite_master` DDL, per-table `PRAGMA table_info/xinfo`, indexes, foreign keys,
   and row counts.

Verification commands used (from `backend/`):

```bash
python -m alembic history | current | heads
python -m alembic check
python -m alembic upgrade head
```

## 3. Findings Per Source

### 3.1 Models (authoritative)
- `jobs`: `employment_type`/`application_url` canonical names; unique
  `(source, external_id)`; `id`/`external_id` indexed.
- `job_skills` / `job_qualifications`: PK `id` columns marked `index=True`
  (=> `ix_job_skills_id`, `ix_job_qualifications_id`); unique
  `(job_id, normalized_name)` / `(job_id, normalized_qualification)`.
- `applications` / `saved_jobs`: unique `(user_id, job_id)`.
- `education.institution` nullable; `experience.currently_employed` NOT NULL
  default `0`; `resumes.analysis_status` NOT NULL default `'parsed'`.

### 3.2 Migration chain final state (fresh `upgrade head`)
- Phase 1 (`bf773dd3d573`) **renames** `job_type -> employment_type`,
  `apply_url -> application_url`, adds `uq_jobs_source_external_id`, creates
  `job_skills`/`job_qualifications`, and creates the six query indexes
  `ix_jobs_{is_active, posted_at, city, work_mode, employment_type, source}`.
- Phase 3 (`c821c44ae290`) adds the resume/education/experience/certification
  columns and the three NOT NULL/nullable declarations above.
- **Gap:** the two PK indexes `ix_job_skills_id` / `ix_job_qualifications_id`
  are declared by the models but absent from the migration-generated tables.
- **Gap:** the six `ix_jobs_*` indexes are created by the phase-1 migration but
  were not declared by the `Job` model, so `alembic check` flagged them as
  "removed".

### 3.3 Actual dev DB (`backend/careeros.db`)
- Created by an early `create_all`, then partially patched in Phase 7.0. It was
  stamped at `c821c44ae290` while still missing constraints/nullability and while
  still carrying the obsolete pre-rename columns.

## 4. Reconciliation Table (drift inventory)

| Item | Models | Chain (fresh) | Dev DB (before) | Resolution |
| --- | --- | --- | --- | --- |
| `js.job_type` column | absent | absent | **present** | data-preserving drop |
| `js.apply_url` column | absent | absent | **present** | data-preserving drop |
| `uq_jobs_source_external_id` | yes | yes | **missing** | add |
| `uq_applications_user_job` | yes | yes | **missing** | add |
| `uq_saved_jobs_user_job` | yes | yes | **missing** | add |
| `education.institution` | nullable | nullable | **NOT NULL** | alter nullable |
| `experience.currently_employed` | NOT NULL | NOT NULL | **nullable** | alter NOT NULL (`0`) |
| `resumes.analysis_status` | NOT NULL | NOT NULL | **nullable** | alter NOT NULL (`'parsed'`) |
| `ix_jobs_{is_active,posted_at,city,work_mode,employment_type,source}` | (not declared) | created | **missing** | declare in model + create |
| `ix_job_skills_id`, `ix_job_qualifications_id` | declared | **missing** | present | add (fresh DBs only) |

`alembic check` on the dev DB before this phase reported exactly the first eight
rows as detected changes; after reconciliation it reports **no** changes.

## 5. Decision: a Reconciliation Migration Was Required

Yes. The dev DB physically differed from the schema the chain already declares,
so the fix could not be a no-op or a pure model edit. Per the phase guidance a
single clean migration was created — it does not restate already-migrated DDL and
has **no effect on databases built through the chain** (guarded, idempotent).

## 6. The Reconciliation Migration

`backend/alembic/versions/313a54989d0d_reconcile_schema_drift.py` (new head,
revises `c821c44ae290`) performs, in order:

1. Create `ix_job_skills_id` / `ix_job_qualifications_id` if missing (fresh-DB
   gap closure).
2. `jobs`: copy `job_type -> employment_type` and `apply_url -> application_url`
   where the new columns are NULL (data-preserving), then drop the legacy columns
   if present.
3. Add `uq_jobs_source_external_id` via batch table rebuild if missing.
4. Create the six `ix_jobs_*` query indexes if missing.
5. Add `uq_applications_user_job` / `uq_saved_jobs_user_job` via batch rebuilds
   if missing.
6. Set `education.institution` nullable, `experience.currently_employed` NOT NULL
   (default `'0'`), `resumes.analysis_status` NOT NULL (default `'parsed'`) when
   the DB differs.

Every operation is guarded by `sa.inspect(op.get_bind())` so a compliant database
is untouched. `downgrade()` reverses only what this migration itself adds on such
a database (the two PK indexes); the constraint/NOT NULL/legacy-column fixes bring
databases *toward* the chain's own declared target, so reversing them in a
downgrade would reverse the chain itself and is intentionally left intact.

## 7. SQLite Safety

- All constraint/nullability changes use `op.batch_alter_table(...)` so SQLite
  rebuilds tables within transactions (recreate + copy pattern) instead of
  attempting unsupported `ALTER TABLE ADD CONSTRAINT`.
- Legacy-column drops are plain nullable columns with no constraints; data is
  copied to the new names *before* the drop.
- A pre-migration file backup was taken (`careeros.db` -> temp `.pre-7.1.bak`)
  and the upgrade ran successfully; no restore was needed.

## 8. Data Preservation

Row counts captured before and after the migration (identical):

| Table | Before | After |
| --- | --- | --- |
| users | 3 | 3 |
| resumes | 1 | 1 |
| jobs, job_skills, job_qualifications, applications, saved_jobs, skills, education, experience, certifications, user_preferences | 0 | 0 |

Spot-check of preserved rows: `admin@career.com` (id 3) still has resume id 1
(`Abdul Muqeet CV (Data).pdf`, `analysis_status='parsed'`); the three seed users
are unchanged. The smoke user created during testing was removed afterwards.

## 9. Fresh Database Test

```bash
$env:DATABASE_URL="sqlite:///<temp>/fresh71.db"; python -m alembic upgrade head
python -m alembic check   # -> "No new upgrade operations detected."
```

A brand-new DB built through all four revisions matches the models exactly.

## 10. Existing Database Test

```bash
python -m alembic upgrade head   # dev DB: ran 313a54989d0d only
python -m alembic current        # -> 313a54989d0d (head)
python -m alembic heads          # -> 313a54989d0d (head)  [single head]
python -m alembic check          # -> "No new upgrade operations detected."
```

Physical schema re-dumped and confirmed: obsolete `job_type`/`apply_url` gone,
all three unique constraints present, three nullability fixes applied, all six
`ix_jobs_*` indexes plus `ix_job_skills_id`/`ix_job_qualifications_id` present.

## 11. Migration Round Trip (temp DB)

```bash
python -m alembic downgrade base   # all four revisions reversed cleanly
python -m alembic upgrade head     # rebuilt cleanly
python -m alembic check            # -> no changes
```

Both directions execute without error; the re-upgraded DB still matches models.

## 12. Model ↔ Migration Consistency

- `Job` model now declares the six `ix_jobs_*` filter indexes in
  `__table_args__` with the exact names the phase-1 migration created, so the
  model, the chain, and any migrated DB agree (and query-time job filtering
  keeps its indexes).
- The two PK indexes the models always declared for `job_skills` /
  `job_qualifications` are now also produced by the chain (via the
  reconciliation migration).
- No existing model columns, constraints, or nullability were changed;
  `alembic check` is clean in all environments tested.

## 13. Backend Test Suite

```bash
python -m pytest -q   # 241 passed (baseline maintained), 714 pre-existing warnings
```

## 14. Frontend Build

```bash
cd frontend && npm run build   # success; 17 routes, shared JS 87.1 kB
```

## 15. Live API Smoke

Against the migrated dev DB on `127.0.0.1:8000` (temp user, removed afterwards):

- `GET /` and `GET /api/health` — ok
- register / login / `GET /api/auth/me` — ok
- `GET /api/jobs`, `/api/jobs/saved`, `/api/applications` — 200
- `GET /api/resume/analysis` — 404 (no resume) as designed
- `GET /api/career-insights` — 404 (no-resume path) as designed

## 16. Alembic Configuration

- `backend/alembic.ini` keeps `sqlalchemy.url` empty; URL is resolved at runtime
  from script option > `DATABASE_URL` env > `settings.DATABASE_URL`
  (`backend/.env`), so plain `alembic upgrade head` targets the same DB the API
  uses.
- `backend/.env` is git-ignored; `backend/.env.example` (and `.env.example`) are
  tracked and document `DATABASE_URL`, JWT, and AI settings — the configuration
  is reproducible from a fresh checkout.
- Migrations run from a fresh checkout: `venv\Scripts\alembic upgrade head`
  (see README).
- Migration chain is a single, linear head: `9032a41514cb -> bf773dd3d573 ->
  c821c44ae290 -> 313a54989d0d`.

---

**Commit suggestion:** `fix: reconcile database schema with alembic`