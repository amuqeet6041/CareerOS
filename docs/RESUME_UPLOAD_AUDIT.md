# RESUME UPLOAD / ANALYSIS FETCH ERROR — AUDIT REPORT

**Status:** Fixed
**Date:** 2026-09-21
**Scope:** Focused root-cause audit of the resume upload failure reported on
`/student-dashboard/resume` ("Fetch error", analysis not performed). No Phase 8
work, no page redesign.

---

## Symptom

After selecting a PDF/DOCX and clicking **Upload Resume** on the resume dashboard,
the UI surfaced an error and `ResumeAnalysis` never showed the newly uploaded
data. The user resumed that result as a "Fetch error".

## Investigation

1. **API-level reproduction** — POST `/api/resume/upload` with a real generated
   PDF and DOCX (multipart, field `file`, `Authorization` header) against the
   running backend:
   - PDF → **201**, `analysis_status="parsed"`, skills/education/experience/
     certifications extracted.
   - DOCX → **201**.
   - unsupported `.txt` → **415** with a useful detail message.
   - The backend upload flow (route → parser → DB → AI) is healthy.
2. **CORS** — Preflight `OPTIONS` for the upload path from all four configured
   origins (`localhost/127.0.0.1` × `3000/3001`) returns the correct
   `Access-Control-Allow-Origin/Headers/Methods`; the real POST also carries the
   correct headers. No CORS failure. `allow_origins=["*"]` is not used.
3. **Multipart field name** — browser sends `file`; FastAPI expects
   `file: UploadFile = File(...)` → match.
4. **Shared API wrapper** (`frontend/lib/api.js`) — correctly omits
   `Content-Type` for `FormData` (browser generates the boundary); token header
   is attached. No JSON-encoding of FormData.
5. **Auth** — upload guarded by `get_current_user`; upload binds to
   `current_user.id`, never a client-supplied id (verified in
   `backend/app/api/routes/resume.py:16-20`).
6. **AI disabled** — with `AI_PROVIDER` empty, `run_resume_analysis` returns
   `(None, "parsed")`; upload succeeds with `analysis_status="parsed"`.
   AI failure degrades to `ai_failed` without breaking upload (covered by tests).
7. **Error strings** — no literal "Fetch error" exists anywhere in the frontend.
   The UI can only show `apiFetch`'s messages (network / status / backend detail).

## Root Cause (frontend logic bug)

`ResumeManager.jsx` wired `<ResumeUpload onUploaded={upload} />`, but
`ResumeUpload` calls `onUploaded(result)` with the **parsed resume object** while
the hook's `upload` is the *file uploader*. The hook then "uploaded" the resume
object as if it were a file:

- `FormData.append("file", result)` coerces the object to the string
  `[object Object]` (browser sets filename `blob`, text part).
- The backend rejects that phantom second request with **422**:
  `Value error, Expected UploadFile, received: <class 'str'>`.
- The hook sets its `error` state (raw/technical message), never updates
  `analysis`, so the analysis panel shows an error/empty state even though the
  real file was uploaded and saved on the first request.

A live simulation confirmed the second request's exact response: 422
`Expected UploadFile`.

## Affected Files

### Frontend (fixed)
- `frontend/hooks/useResume.js` — removed the erroneous `upload` (double
  uploader); added `applyResult(result)` that mirrors a completed upload into
  state without any HTTP call.
- `frontend/components/resume/ResumeManager.jsx` — passes `onUploaded={applyResult}`.
- `frontend/lib/api.js` — clearer error classification: network failure keeps
  "Unable to connect to CareerOS API..." ; authenticated `401` without a backend
  detail now reads "Your session has expired. Please sign in again."; backend
  validation/business detail messages are shown verbatim; login's own 401 detail
  ("Invalid email or password") is preserved.

### Backend (no functional change; tests added)
- `backend/tests/test_resume.py` — added
  `test_upload_pdf_with_ai_disabled_returns_parsed` and
  `test_upload_with_nonfile_part_rejected` (documents the guard against the
  `[object Object]` FormData case).

## Fix

- Stop re-uploading the upload result (the actual defect).
- Make the analysis state reflect the successful upload immediately.
- Give users meaningful error messages instead of raw framework output.

## Tests

`python -m pytest -q` → **243 passed** (241 baseline + 2 new). Coverage already
present for: authenticated upload, PDF parsing, DOCX parsing, parser success,
invalid/unsupported/empty/oversized files, content-type conflicts, AI disabled
(`parsed`), AI failure/degraded (`ai_failed`, upload still 201), AI success
(`ai_analyzed`), auth isolation, re-upload replacement, and 401 without token.

`npm run build` → green (17 routes).

## Live Verification (API-level, browser-equivalent requests)

Against the live backend + dev DB, with temporary users removed afterwards:

| Step | Result |
| --- | --- |
| register/login | 200 |
| PDF upload | 201, `analysis_status="parsed"`, skills/education/experience/certifications extracted |
| Refresh (GET /api/resume/analysis) | 200, same parsed resume |
| DOCX re-upload (replacement) | 201, `parsed`, replaces previous |
| Career Insights after upload | 200 (deterministic; `ai_status` unset because AI disabled) |
| Invalid file | 415 with useful detail message |
| Non-file form part (old bug) | 422 `Expected UploadFile` |

Dev DB restored to baseline after the smoke (3 users, the pre-existing resume is
untouched; all temp users/rows removed). `alembic check` still reports no
schema drift.

## AI-Disabled Behavior

- With `AI_PROVIDER` empty (default), upload **must** and **does** succeed; the
  resume is stored via the deterministic parser with
  `analysis_status = "parsed"`.
- AI providers are invoked only when configured; every AI failure path falls
  back to deterministic parsing (`ai_failed`) without failing the upload.

## Remaining Limitations

- A real click-through in a physical browser was not performed in this run; the
  browser-equivalent multipart/CORS/preflight requests were verified directly.
  The fix removes the only request the browser made that the backend could not
  accept for a valid file.
- The deterministic parser still merges a trailing date into an experience
  company line for some layouts (e.g. `"Rocket Labs 2022 - Present"`); this is a
  parser-precision limitation, not an upload failure, and is outside this bug.