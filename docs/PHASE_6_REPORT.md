# CareerOS — Phase 6 Report: Real Personalized Dashboard

Phase 6 replaces the static student-dashboard placeholder with a live,
personalized dashboard composed entirely from existing backend APIs. No fake
statistics, no invented fields, no local fakes, and no Phase 7 features.

---

## 1. Overview

The dashboard now shows the authenticated user's real profile, resume status,
a bounded set of genuinely scored job recommendations, application statistics,
recent applications, saved jobs, and a factual career overview. Every number
comes from a real API response; every empty or failed section presents an
honest state with a recovery path.

## 2. Design decisions

- **Dashboard is a frontend composition of existing APIs.** No backend
  changes were required and no `GET /api/dashboard` aggregator was created
  (the brief allowed it only if "genuinely necessary" — it wasn't, since the
  data is three independent resources and each section owns its loading and
  error state).
- **Per-section independence.** Each card fetches via its own hook and renders
  its own skeleton, error/retry, and empty state, so a transient failure in one
  section never hides the rest of the dashboard.
- **No invented resume statuses.** Only the backend's real values
  (`parsed | ai_analyzed | ai_failed`) are mapped; nothing else is implied.
- **Recommendations are real and bounded.** One jobs fetch (15 newest) plus one
  `/api/jobs/{id}/match` per candidate; only jobs with a meaningful (non-null,
  above-zero) overall score can appear, sorted best-first, top 5.
- **Profile completion is a transparent, deterministic formula** over the six
  profile components the platform actually supports today (see section 3).

## 3. Profile completion formula

`frontend/lib/profileCompletion.js` — a pure function over real data:

```
completion = number of met components / 6 × 100
```

The six components and how each is met:

| Component | Met when |
| --- | --- |
| Account | `GET /api/auth/me` returns a user with name and email |
| Resume uploaded | `GET /api/resume/analysis` returns a resume |
| Skills extracted | resume analysis has ≥ 1 skill |
| Education recorded | resume analysis has ≥ 1 education entry |
| Experience recorded | resume analysis has ≥ 1 experience entry |
| Certifications recorded | resume analysis has ≥ 1 certification |

The denominator is always 6, so the number is stable and explainable:

- Newly registered user, no resume: `1/6 = 17%`
- Resume uploaded but no data extracted: `2/6 = 33%`
- Fully populated resume: `6/6 = 100%`

Each component is rendered as a legend item under the bar with a check / empty
state, so the number can always be traced back to real data. The formula is
exactly what is documented here; nothing is weighted, scored, or cached.

## 4. Data → API map

| Dashboard data | Endpoint | Hook used |
| --- | --- | --- |
| Profile (name, email, joined) | `GET /api/auth/me` | `useAuth` |
| Resume status + career overview | `GET /api/resume/analysis` | `useResume` |
| Resume re-analysis (retry) | `POST /api/resume/analyze` | `useResume.retryAnalysis` |
| Recommended jobs (bounded) | `GET /api/jobs?page_size=15` + `GET /api/jobs/{id}/match` | `useJobRecommendations` |
| Applications + stats + recent | `GET /api/applications` (job embedded) | `useApplications` |
| Saved jobs summary | `GET /api/jobs/saved` | `useSavedJobs` |

`GET /api/jobs/{id}/match` is only called when a resume exists, so a fresh user
never fires a doomed batch of no-resume 404s.

## 5. Recommended jobs

- **Candidate set:** 15 newest jobs (`page_size=15`), matching the brief's
  12–20 window.
- **Scoring:** one `GET /api/jobs/{id}/match` per candidate (up to 15
  requests), the existing deterministic engine.
- **Eligibility:** a job is only "recommended" when its `overall_match_percentage`
  is **non-null AND above zero**. Null means the engine could not score it
  (never shown as 0%); zero means zero overlap with the resume (not a
  recommendation). Per the brief: no job is presented as recommended without a
  meaningful match.
- **Ranking:** eligible jobs sorted by `overall_match_percentage` descending,
  top 5 shown via `RECOMMENDATION_DISPLAY_COUNT`.
- **Empty states:** no resume → "Upload and analyze your resume" CTA; resume
  present but nothing meaningfully matches → "No strong matches right now" with
  a Browse jobs CTA. During scoring, a section skeleton is shown.
- Configurable in `frontend/lib/constants.js`
  (`RECOMMENDATION_CANDIDATES`, `RECOMMENDATION_DISPLAY_COUNT`).
- Server-side match ordering for full job lists remains deferred (see section
  "Deferred").

## 6. Application stats

`ApplicationStats` computes from the real `GET /api/applications` records:

- Total count.
- Per-status counts **only for statuses that actually appear in the data**
  (`applied | in_review | interview | offer | rejected`), so the summary never
  claims an "Interview" count that doesn't exist. Bars are proportional to
  totals (role="progressbar" with real aria values).

## 7. Recent applications

The 3 newest applications (the API returns newest-first) with company, title,
applied date, explicit status badge, and a link to the job detail page. The
Phase 5 embedded job data means no per-application requests.

## 8. Saved jobs summary

Real count plus the 3 most recent entries from the single
`GET /api/jobs/saved` request, each linking to the job detail page, with a
"View saved jobs" action.

## 9. Career overview

Factual only, built from the stored resume analysis: total recorded experience
years, skills, education, experience, and certifications (reusing the existing
`SkillsList` / `EducationList` / `ExperienceList` / `CertificationsList`
components). No advice, skill-gap analysis, or market projections — those are
Phase 7.

## 10. Resume status logic

`ResumeStatusCard` maps the backend `analysis_status` only:

| Backend status | Card shows | Actions |
| --- | --- | --- |
| (no resume) | "No resume uploaded yet" | Upload Resume → resume page |
| `parsed` | "Basic parse complete" | View resume |
| `ai_analyzed` | "AI analysis complete" | View resume |
| `ai_failed` | "AI analysis failed" | **Retry analysis** + View resume |
| anything else | raw status, never re-labeled | View resume |

Retry calls the real `POST /api/resume/analyze`; the backend replaces the
previous analysis in place (it never returns a duplicated resume). Pending /
anything else is never invented.

## 11. Profile summary

Name, email, join date, avatar initial, and live summary counts (skills,
education, experience, certifications) derived from the resume analysis, plus
a View Profile link to `/student-dashboard/profile`. While the resume loads,
counts show a dash rather than a guessed number.

## 12. Loading, error, and empty states

- **Auth restore:** whole-page skeleton while the session resolves.
- **No session:** inline "Sign in to view your dashboard" card (matches how the
  rest of the app surfaces 401s today).
- **Per-section skeletons:** pulse placeholders matching each section layout;
  never shown for sections that already finished loading.
- **Per-section errors:** a red panel with a Retry button wired to that
  section's own `refetch`/`load`.
- **Empty states:** meaningful for every section (no resume, no applications,
  no saved jobs, no strong matches) with the relevant CTA to the matching page.

## 13. Responsive design

One layout, three widths: single column below `lg`, two columns at `lg`, the
profile row going three columns at `xl`. Tailwind breakpoints were chosen to
match the brief (375 mobile, 768 tablet, 1280 desktop). Job cards reuse the
grid used by the Jobs and Saved Jobs pages.

## 14. Accessibility

- Status is never color-only (`ApplicationStatus` shows a label + color).
- Match scores and progress bars carry `aria-label` / `role="progressbar"`
  with numeric `aria-valuemin/valuemax/valuenow`.
- Skeleton blocks declare `role="status"`.
- Save/apply controls keep their existing `aria-label` behavior.

## 15. Backend changes

**None.** All dashboard data composes existing, tested endpoints. No new
migrations, no new routes, no schema changes.

## 16. Files created

- `frontend/lib/profileCompletion.js` — pure completion formula
- `frontend/hooks/useJobRecommendations.js` — bounded recommendation hook
- `frontend/components/dashboard/StudentDashboard.jsx` — page orchestrator
- `frontend/components/dashboard/DashboardSection.jsx` — section wrapper +
  `SectionError` + `SectionSkeleton`
- `frontend/components/dashboard/DashboardSkeleton.jsx`
- `frontend/components/dashboard/ProfileCompletion.jsx`
- `frontend/components/dashboard/ResumeStatusCard.jsx`
- `frontend/components/dashboard/RecentApplications.jsx`
- `frontend/components/dashboard/SavedJobsSummary.jsx`

## 17. Files modified

- `frontend/app/student-dashboard/page.js` — render the new orchestrator
- `frontend/components/dashboard/ProfileSummary.jsx` — real user + resume
- `frontend/components/dashboard/RecommendedJobs.jsx` — real scored cards
- `frontend/components/dashboard/ApplicationStats.jsx` — real record counts
- `frontend/components/dashboard/CareerOverview.jsx` — factual overview
- `frontend/hooks/useResume.js` — added `retryAnalysis`
- `frontend/services/resumeService.js` — added `analyzeResume`
- `frontend/lib/constants.js` — recommendation bounds constants
- `frontend/components/applications/ApplicationStatus.jsx` — exported
  `STATUS_LABELS` for reuse
- `docs/DEVELOPMENT_ROADMAP.md`, `README.md`, this report

## 18. Tests & build

- `cd backend && python -m pytest -q` → **222 passed** (unchanged; no backend
  code touched).
- `cd frontend && npm run build` → **green, 17 routes** (dashboard route now
  9.74 kB of page-specific JS).

## 19. Live smoke (temp SQLite, demo provider)

Verified against a fresh temporary database and the bundled demo job provider:

- Register/login/`/api/auth/me` return the real user.
- Fresh user: applications `[]`, saved `[]`, resume analysis → 404.
- Upload a sectioned DOCX resume → 201, `analysis_status=parsed`, 7 skills,
  1 education, 3 experience entries, 1 certification.
- `/api/jobs/{id}/match` without a resume → 404 "No resume uploaded yet…"
  (recommendations stay disabled); with a resume → real component + overall
  scores.
- `GET /api/jobs?page_size=15` → 10 items; a 0-overlap job scored 0.0
  (filtered by the recommendations hook, since 0 is not a recommendation).
- `POST /api/resume/analyze` (retry) → 200, retains stored data.
- Apply → 201 (with embedded job); save → 201; both lists then return the
  record with the embedded job.
- Completion formula spot-checked in Node: new user 17%, empty resume 33%,
  fully populated 100%, no user 0%.
- Server stopped and temp DB removed; the dev `backend/careeros.db` was not
  touched at any point.

## 20. Remaining Phase 5 sub-item

Server-side match ordering for the full job result set remains deferred. The
Phase 6 dashboard recommendation hook documents its request bound and the
eventual move to server-side ordering.

## 21. Deferred to Phase 7

AI career advice, skill-gap analysis, career path suggestions, salary
prediction, trending roles, resume rewriting, real job providers, scheduled
ingestion, administrative analytics, payments/messaging. The dashboard only
states facts that are on record.

## 22. Known limitations

- Responsive and visual verification at 375/768/1280 was via layout/classes +
  production build; a final in-browser pass on the three widths is recommended.
- The dashboard's `CareerOverview` mirrors the Resume page's factual lists
  (consistency, not duplication of backend logic).
- An `ai_failed` smoke could not be exercised end-to-end with AI disabled
  (default config); the state, its label, and the Retry action are covered by
  the existing AI pipeline tests and the mapped UI state.