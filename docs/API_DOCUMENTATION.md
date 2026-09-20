# CareerOS — API Documentation (Planned Endpoints)

Base URL: `http://localhost:8000/api`

## Health
- `GET /health` — Service health check. ✅ implemented.

## Auth
- `POST /auth/register` — Create a new user account. Returns `UserOut`.
  ✅ implemented.
- `POST /auth/login` — Authenticate and receive a JWT access token (bearer).
  ✅ implemented.
- `GET /auth/me` — Return the authenticated user resolved from the access
  token. ✅ implemented. Requires `Authorization: Bearer <token>`.
- `POST /auth/logout` — Log out. ✅ implemented (stateless; the client
  discards its token — real invalidation would need a blocklist).

## Resume
- `POST /resume/upload` — Upload a resume file (PDF or DOCX) for parsing and
  persistence. ✅ implemented. Requires auth. Accepts `multipart/form-data`
  with a `file` field.
  - Uploads larger than `MAX_RESUME_SIZE_MB` (default `5`) return `413`.
  - Unsupported file types/extension–content-type conflicts return `415`.
  - Malformed or empty documents return `400`.
  - Returns `201` with the parsed `ResumeOut` payload:
    ```
    {
      "id": 1,
      "file_name": "Resume.pdf",
      "uploaded_at": "2026-09-19T12:00:00Z",
      "skills": [{"id": 1, "name": "Python"}],
      "education": [{"id": 1, "institution": "...", "degree": "...", "field_of_study": "..."}],
      "experience": [{"id": 1, "company": "...", "title": "...", "description": "..."}],
      "certifications": [{"id": 1, "name": "...", "issuer": "..."}]
    }
    ```
  - Re-uploading replaces the user's previous resume (children are replaced,
    not duplicated).
- `GET /resume/analysis` — Retrieve the structured analysis of the current
  user's latest resume. ✅ implemented. Requires auth. Returns `ResumeOut`
  (same shape as above) or `404` when the user has no resume yet.

## Jobs
Implemented in Phase 1. Job browsing is **public** (no auth). Datasets come
from ingestion (see "Job ingestion" below — there is no public write
endpoint).

- `GET /jobs` — List/search jobs. ✅ implemented. Query parameters:
  - `search` — free-text, case-insensitive match over title, company,
    description, location, and skill names. LIKE wildcards (`%`, `_`) in the
    input are escaped and matched literally.
  - `location` — substring match on the free-form location text.
  - `city` — substring match on the job city.
  - `work_mode` — one of `remote | hybrid | onsite`.
  - `employment_type` — one of `full-time | part-time | contract | internship |
    temporary | freelance`.
  - `salary_min` — include jobs whose max salary is at/above this value.
  - `salary_max` — include jobs whose min salary is at/below this value.
  - `source` — provider id, e.g. `demo`.
  - `include_inactive` — `true` also returns expired/inactive jobs (default
    excludes them).
  - `sort` — `date_newest` (default) | `date_oldest` | `salary_desc`.
  - `page` — 1-based page number (default `1`).
  - `page_size` — items per page (default `20`, max `100`).
  - Returns a paginated envelope:
    ```
    {
      "items": [ { ...JobResponse } ],
      "total": 100,
      "page": 1,
      "page_size": 20,
      "total_pages": 5
    }
    ```
  - Errors: `400` for invalid `work_mode`/`employment_type`/`sort` values;
    `422` for out-of-range `page`/`page_size`.
- `GET /jobs/{job_id}` — Get the full record for one job, including its
  `skills` and `qualifications`. ✅ implemented. Returns `404` when the job
  does not exist. Returning an inactive/expired job by id is allowed (the
  record keeps its `is_active=false`).
- `POST /jobs/{job_id}/save` — Save a job for the current user.
  ⚠️ Requires auth; persistence to `SavedJob` not yet wired (Phase 5).

`JobResponse` shape:
```
{
  "id": 1,
  "source": "demo",
  "external_id": "demo-01",
  "title": "Junior Data Analyst",
  "company": "DataWorks Pakistan",
  "description": "...",
  "employment_type": "full-time",
  "work_mode": "remote",
  "location": "Lahore, Pakistan",
  "city": "Lahore",
  "country": "Pakistan",
  "salary_min": 600000.0,
  "salary_max": 800000.0,
  "currency": "PKR",
  "application_url": "https://careeros-demo.example/apply/demo-01",
  "minimum_experience_years": 0.0,
  "maximum_experience_years": 2.0,
  "posted_at": "2026-08-01T00:00:00",
  "expires_at": "2027-01-01T00:00:00",
  "created_at": "2026-09-20T12:00:00",
  "updated_at": "2026-09-20T12:00:00",
  "is_active": true,
  "skills": [{"id": 1, "skill_name": "Excel", "normalized_name": "excel"}],
  "qualifications": [{"id": 1, "qualification": "Bachelor's in Data Science", "normalized_qualification": "bachelor's in data science"}]
}
```

### Job ingestion
Ingestion is intentionally **not an HTTP endpoint** (nothing can write jobs
over the network). It runs via the CLI:
```
cd backend
python -m app.cli seed-jobs      # uses the demo provider, upserts, idempotent
```
The demo provider loads 10 fictional jobs (invented companies, clearly-marked
demo apply URLs) so the browse/search APIs can be exercised without any
external API key. Real providers will plug into the same
`JobProvider` -> `NormalizedJob` -> upsert pipeline in a later phase.

## Matching
- `POST /matching` — Calculate skill/qualification match percentages given
  user and job attributes. ✅ implemented (set-overlap logic).

## Applications
- `GET /applications` — List the current user's tracked applications.
  ✅ implemented. Requires auth; results are scoped to the token's user.
- `POST /applications` — Create a new application record (status `applied`).
  ✅ implemented. Requires auth. Body: `{ "job_id": 1 }`.
  - Returns `201` with the new `ApplicationOut`.
  - Returns `404` when the referenced `job_id` does not exist.
  - Returns `409` when the user already has an application for that job
    (duplicate prevention is enforced by a DB unique constraint too).
- `PATCH /applications/{application_id}` — Update an application's status.
  ✅ implemented. Requires auth; only the owner can update their own
  application. Valid statuses: `applied | in_review | interview | offer |
  rejected`.

## Auth requirements
Endpoints marked "requires auth" expect an `Authorization: Bearer <JWT>`
header where the scheme is exactly `Bearer` followed by the token issued by
`POST /auth/login`. The token stores only the user identifier (`sub`) and an
`exp` claim; no password data is included.

`401` is returned for:
- a missing `Authorization` header,
- a malformed header (wrong scheme or empty `Bearer`),
- an invalid or expired JWT,
- a token with a missing/invalid `sub` claim,
- a token whose `sub` references a user that no longer exists.

Dashboard-only endpoints (resume upload/analysis, applications, job save)
return `401` when no valid token is provided. Public endpoints (`GET /jobs`,
`POST /matching`) remain publicly accessible; `POST /matching` is a stateless
calculation over the attributes sent in the request body and does not read
user-owned data.