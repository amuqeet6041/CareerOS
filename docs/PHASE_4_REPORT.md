# Phase 4 Report — Jobs Frontend

## Objective
Turn the placeholder public `/jobs` and dashboard `/jobs` pages into a
production-quality, database-backed jobs UI: search, filters, sorting,
pagination, job cards and detail pages, personalized match scores with
explanations, and an Apply Now flow — all live against `GET /api/jobs` and
`GET /api/jobs/{id}/match`, with no fake data, no invented saves, and no
backend changes.

## What Was Implemented

### New files
- `frontend/lib/jobQuery.js` — query-string ↔ filter mapping. `queryToFilters`
  (URL → filters, strings kept lossless), `filtersToQuery` (filters → URL),
  `initialFilters`, `serializeFilters`.
- `frontend/hooks/useJobMatch.js` — single-job match with explicit states:
  `idle | loading | success | no-resume | sign-in | error` + `refetch`.
- `frontend/hooks/useJobMatches.js` — bounded per-page list matches
  (`MAX_LIST_MATCHES = 12`) as a `jobId → { status, data }` map; race-safe via
  a batch counter.
- `frontend/components/jobs/` — `JobHero.jsx` (public dark band),
  `JobSearch.jsx` (submit-committed search), `JobFilters.jsx` (controlled
  panel + mobile drawer usage), `JobPagination.jsx` (ellipsis window),
  `ApplyButton.jsx`, `MatchPill.jsx`, `MatchScore.jsx` (reworked),
  `MatchCard.jsx`, `Skeletons.jsx`, `JobsExplorer.jsx` (orchestrator),
  `JobDetailView.jsx`.
- `frontend/app/(public)/jobs/[id]/page.js` — new public job detail route.
- `docs/PHASE_4_REPORT.md` (this report).

### Modified files
- `frontend/lib/constants.js` — full canonical `EMPLOYMENT_TYPES` (adds
  `temporary`/`freelance` to the old 4), `WORK_MODE_OPTIONS`,
  `EMPLOYMENT_TYPE_OPTIONS`, `SORT_OPTIONS`, `DEFAULT_SORT`, `PAGE_SIZE`,
  `MAX_LIST_MATCHES`.
- `frontend/services/jobService.js` — `getJobs(filters, options)` (cleans
  empty values), `getJobById`, `getJobMatch`; **removed** the dead `saveJob`
  (Phase 5 persistence), so the UI never fakes a save.
- `frontend/hooks/useJobs.js` — reworked: paginated (page/pageSize/totalPages),
  URL-synced, external-URL re-apply on back/forward, race-safe fetches,
  filter/sort changes restart at page 1.
- `frontend/utils/formatters.js` — `formatMatchPercentage` (null-safe),
  `humanizeLabel`, `formatExperienceRequirement`, `EXPERIENCE_STATUS_LABELS`.
- `frontend/components/jobs/JobCard.jsx` / `JobList.jsx` — rebuilt with match
  pill, skeleton/error/empty states; removed the dead Save button.
- `frontend/components/jobs/MatchScore.jsx` — null-safe component rows.
- `frontend/app/(public)/jobs/page.js`, `frontend/app/student-dashboard/jobs/
  page.js` — Suspense-wrapped explorers; `frontend/app/student-dashboard/
  saved-jobs/page.js` — honest Phase 5 placeholder.
- `docs/ARCHITECTURE.md`, `docs/DEVELOPMENT_ROADMAP.md`, `README.md`.
- `backend/requirements.txt` — pinned `bcrypt==4.0.1` (see Constraints).

## API Integration & UX Decisions
- **One orchestrator, two surfaces**: `JobsExplorer({ variant })` powers the
  public page (dark hero band matching the Navbar palette + light results
  area) and the dashboard (compact search row, match banner, match pills).
- **URL is state**: every applied filter/sort/page change is pushed with
  `router.replace` (no-op-guarded so it never loops); back/forward and shared
  paginated links re-apply the external filter state.
- **Request discipline**: searches commit on submit (never per keystroke);
  the filter panel edits a draft and commits only on **Apply Filters**;
  work-mode/employment-type/sort selects apply immediately.
- **Points of note**:
  - Envelope is `{ items, total, page, page_size, total_pages }`; the client
    trusts `page_size`/`total_pages` from the response.
  - Dashboard matches are fetched for the visible page only (≤12 jobs) and
    only when authenticated; the detail page is the primary match surface.
    Match data is React state only — never persisted (backend design).
  - Unknown match components are shown as visible text **Not enough data**,
    never 0%; overall uses `—` when unknown. `component_weights`
    (`skill/qualification/experience` = 50/30/20) are displayed so scores stay
    transparent.
  - Match states handled explicitly: 401 → "Sign in", 404-with-resume-message →
    "Upload your resume" (links to `/student-dashboard/resume`), other errors →
    retry.
  - Apply Now opens `application_url` in a new tab; disabled with an
    explanatory tooltip when no URL exists. No fake Save anywhere.
  - `saveJob`, `WORKS_MODES`/`JOB_TYPES` were grep-verified to have no other
    consumers before changes; `JobDetails.jsx` remains a standalone (unused)
    presentational component.

## Frontend Files (new/changed summary)
| Area | Files |
| --- | --- |
| State/hooks | `useJobs`, `useJobMatch`, `useJobMatches` |
| Services/data | `jobService`, `lib/jobQuery`, `lib/constants`, `utils/formatters` |
| List UI | `JobCard`, `JobList`, `MatchPill`, `JobPagination`, `Skeletons` |
| Detail UI | `JobDetailView`, `MatchScore`, `MatchCard`, `ApplyButton` |
| Controls | `JobSearch`, `JobFilters`, `JobsExplorer`, `JobHero` |
| Routes | `(public)/jobs`, new `(public)/jobs/[id]`, `student-dashboard/jobs`, `student-dashboard/saved-jobs` |

## Verification (all run in this session)
- **Backend**: `python -m pytest -q` → **212 passed, 0 failed** (unchanged
  baseline; no backend code changed).
- **Frontend**: `npm run build` → **17 routes**, success. `/jobs` static
  (Suspense fallback prerendered, no `useSearchParams` flash), `/jobs/[id]`
  server-rendered on demand.
- **Live API smoke** (fresh temp SQLite DB, alembic `upgrade head` →
  `seed-jobs` = 10 demo rows, uvicorn on :8001):
  - `GET /api/jobs` → `items=10`, envelope fields `total/page/page_size/
    total_pages` present; job carries `skills[.skill_name]`,
    `qualifications[.qualification]`, `application_url`.
  - Filters: `work_mode=remote&employment_type=full-time` → only matching rows;
    `search=python` → 4; `city=Lahore` → 3; `salary_min=100000` → 6.
  - `GET /api/jobs/999999` → 404. `GET /api/jobs/1/match` unauthenticated →
    401. Authenticated without resume → 404 with detail containing "resume"
    (drives the "Upload your resume" CTA).
  - Server stopped; temp DB confined to `%TEMP%` (dev `careeros.db` untouched).

## Constraints Encountered
- **Server component limits**: a Suspense fallback cannot pass handler props to
  a client component — the `/jobs` fallback search is a shimmer placeholder,
  not a live input (the interactive search mounts with the explorer).
- **Environment dependency drift (not caused by this phase)**: the global
  Python env had picked up `bcrypt==5.0.0` (transitive of
  `passlib[bcrypt]==1.7.4`), which raises `ValueError` for >72-byte passwords
  and broke 44 auth-assisted tests. Pinned `bcrypt==4.0.1` in
  `backend/requirements.txt` (the last 4.x compatible with passlib 1.7.4) and
  re-ran the full suite → 212 green. Also installed the documented
  `python-docx==1.2.0` (required by `tests/test_resume.py` and the resume
  upload path), which was likewise missing from this environment.
- ESLint is not configured in the project (`next lint` interactively proposes
  a setup) and remains out of scope; `npm run build` is the gate and it passes.

## Limitations (next phases)
- Saved jobs are not persisted yet — the UI shows an honest Phase 5 placeholder
  instead of faking saves.
- List matches are per-page and not used for ordering; Phase 5 will add
  server-side scoring to rank the full result set.
- Job details are shared routes for both surfaces; saved-job/application
  actions on detail pages arrive with Phase 5.

## Next Phase
**Phase 5 — Saved Jobs & Applications UI**: persist `SavedJob` and drive the
applications flow end-to-end (including Server-Side match ordering for list
ranking), replacing the placeholder and the bounded per-page scoring.