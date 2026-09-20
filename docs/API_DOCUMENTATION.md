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
- `GET /jobs` — List/search jobs, with optional `location`, `work_mode`,
  `job_type` query parameters. ⚠️ Wired to a placeholder provider (returns
  `[]`).
- `GET /jobs/{job_id}` — Get details for a single job. ⚠️ Placeholder (404).
- `POST /jobs/{job_id}/save` — Save a job for the current user.
  ⚠️ Requires auth; persistence to `SavedJob` not yet wired.

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