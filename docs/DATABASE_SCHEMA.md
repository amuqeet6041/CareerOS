# CareerOS — Database Schema

The source of truth for the schema is the SQLAlchemy models in
`backend/app/models/`. Alembic (in `backend/alembic/`) is used to create and
evolve the database; run `alembic upgrade head` from `backend/` to apply
migrations (see the README).

## Entities

- **User** — id, name, email, hashed_password, created_at
- **Resume** — id, user_id (FK → User), file_name, raw_text, uploaded_at
- **Skill** — id, resume_id (FK → Resume), name
- **Education** — id, resume_id (FK → Resume), institution, degree, field_of_study
- **Experience** — id, resume_id (FK → Resume), company, title, description
- **Certification** — id, resume_id (FK → Resume), name, issuer
- **Job** — id, source, external_id, title, company, location, work_mode,
  job_type, salary_min, salary_max, currency, description, apply_url, fetched_at
- **SavedJob** — id, user_id (FK → User), job_id (FK → Job), saved_at
- **Application** — id, user_id (FK → User), job_id (FK → Job), status, applied_at
- **UserPreference** — id, user_id (FK → User, unique), preferred_location,
  preferred_work_mode, preferred_job_type

## Relationships

- A `User` has many `Resume`, `SavedJob`, and `Application` records.
- A `Resume` has many `Skill`, `Education`, `Experience`, and `Certification`
  records.
- A `Job` can appear in many `SavedJob` and `Application` records:
  both `SavedJob.job` and `Application.job` are ORM relationships.
- A `User` has exactly one `UserPreference` record.

## Constraints

- `users.email` is unique.
- `user_preferences.user_id` is unique (one preference row per user).
- `saved_jobs` and `applications` have a unique `(user_id, job_id)` pair, so a
  user cannot save the same job twice or apply to the same job twice.
- All foreign keys are validated (`PRAGMA foreign_keys=ON` is enabled in
  tests, matching PostgreSQL behavior).

This schema is intentionally normalized and simple to extend as matching
logic and AI extraction mature.
