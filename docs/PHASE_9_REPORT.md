# CareerOS — Phase 9 — Profile & Career Preferences

Date: 2026-09-24 — working tree only, no commit, no push (matching the repo's
established Phase discipline).

## 1. Objective

Add a per-user Profile (basic + professional information) and Career
Preferences (roles, work modes, employment types, industries, skills, salary,
career level, relocation) to CareerOS, with authenticated API access, a
matching Alembic migration, a frontend Profile page reachable from the student
dashboard, and full test coverage — without regressing Phase 8's AI work.

## 2. Requirements Summary

- **Profile data**: identity is immutable (user_id, name, email from User);
  editable fields are headline, bio, location, country, profile_source
  ("manual" when the user edits). Resume-derived data stays on the Resume
  page — the Profile page links to it and CareerOS never overwrites it.
- **Preferences data**: location, work mode, employment type, desired roles,
  industries, salary min/max, currency, career level, skills, open_to_relocate.
  Values align with existing job enums (WORK_MODES: remote/hybrid/onsite;
  EMPLOYMENT_TYPES: full-time/part-time/contract/internship/temporary/freelance;
  career level: entry/junior/mid/senior/lead).
- **API**: all endpoints derive user_id from `get_current_user()` — never from
  client input. Cross-user isolation required.
- **Schema**: `user_profiles` table (1:1 with users via unique FK) plus new
  columns on the existing `user_preferences` table. Backward compatibility with
  legacy preference columns (preferred_location, preferred_work_mode,
  preferred_job_type).
- **Frontend**: profileService.js using the existing `@/lib/api` client, a
  useProfile hook (loading/saving/error states, no infinite loops), and a
  Profile page linked in the dashboard sidebar that persists across refreshes.

## 3. What Was Found on Audit

The prior implementation (uncommitted, as with Phase 8) was verified end-to-end:

- Models, schemas, service, routes, main.py registration, migration, frontend
  service/hook/page, and `tests/test_profile_api.py` all existed and were fully
  consistent with each other and with the existing codebase conventions.
- Alembic chain was linear and healthy:
  `9032a41514cb -> bf773dd3d573 -> c821c44ae290 -> 313a54989d0d -> a1b2c3d4e5f6`.
  `alembic current` = `a1b2c3d4e5f6 (head)`; `alembic check` reported
  `No new upgrade operations detected`.
- `test_profile_api.py` passed on first run (15/15) with no changes required.

## 4. Implementation (verified final state)

### Backend

- `backend/app/models/profile.py` — `UserProfile` model, table `user_profiles`,
  unique FK `user_id -> users.id` (1:1), fields headline/bio/location/country,
  `profile_source` (default "manual"), `updated_at`.
- `backend/app/models/application.py` — `UserPreference` extended with Phase 9
  columns: `preferred_roles`, `preferred_skills`, `preferred_work_modes`,
  `preferred_employment_types`, `preferred_industries` (JSON-encoded strings),
  `salary_min`/`salary_max` (strings), `currency` (default "USD"),
  `career_level`, `open_to_relocate` ("true"/"false"/NULL). Legacy columns
  retained.
- `backend/app/models/user.py` — `profile` and `preferences` relationships
  (both 1:1, `uselist=False`, `back_populates` matched).
- `backend/app/models/__init__.py` — `UserProfile` imported and exported.
- `backend/app/schemas/profile.py` — `ProfileOut` (identity read-only +
  editable fields), `ProfileUpdate`, `PreferencesOut`, `PreferencesUpdate`;
  `ConfigDict(from_attributes=True)` (Pydantic v2 style).
- `backend/app/services/profile_service.py` — `get_profile`/`upsert_profile`
  (partial update, only non-None fields), `get_preferences`/`upsert_preferences`,
  `_encode_list`/`_decode_list` JSON helpers, `preference_to_dict`/
  `profile_to_dict`. Security note: `user_id` is always passed by the route from
  the authenticated user.
- `backend/app/api/routes/profile.py` — GET/PATCH `/api/profile`,
  GET/PATCH `/api/profile/preferences`. Unauthenticated → 401 (via
  `get_current_user`). New users get an empty profile (identity only) and empty
  preferences ([] lists, null scalars, "USD" currency) — no 404s.
- `backend/app/main.py` — router registered under prefix `/api/profile`.
- `backend/alembic/versions/a1b2c3d4e5f6_phase9_profile_preferences.py` —
  creates `user_profiles` (idempotent `_has_table` guard, index + unique
  constraint), adds the 10 Phase 9 preference columns via `batch_alter_table`
  (guarded by `_has_column`, SQLite-safe), with full `downgrade()`.

### Frontend

- `frontend/services/profileService.js` — `getProfile`/`updateProfile`/
  `getPreferences`/`updatePreferences` via the existing `apiFetch` from
  `@/lib/api` (Bearer token + JSON handling already centralized there).
- `frontend/hooks/useProfile.js` — state for profile/preferences/loading/saving/
  error/saved; `loadProfile`/`saveProfile`/`loadPreferences`/`savePreferences`
  all `useCallback`-memoized with stable deps (no infinite fetch loops).
- `frontend/app/student-dashboard/profile/page.js` — fully client-rendered page:
  Basic Information (identity card + headline/location/country/bio inputs),
  Resume Data card (read-only link to `/student-dashboard/resume`), and Career
  Preferences (tag inputs for roles/industries/skills, checkbox groups for work
  mode/employment type, career-level select, preferred location + relocation
  checkbox, salary range with currency). Two independent save bars. Data loads
  from the API and re-syncs on save; page persists across refresh.
- Navigation: `/student-dashboard/profile` already listed in
  `frontend/components/dashboard/DashboardSidebar.jsx`.

## 5. Validation

| Check | Result |
|---|---|
| `pytest tests/test_profile_api.py -q` | 15 passed |
| Full backend suite `pytest tests/ -q` | 266 passed, 0 failed |
| Phase 8 regression (AI provider/config tests) | Included in the 266, all passing |
| `alembic current` | `a1b2c3d4e5f6 (head)` |
| `alembic heads` | single head: `a1b2c3d4e5f6` |
| `alembic check` | No new upgrade operations detected |
| `backend/app/core/config.py` defaults | `AI_MODEL=""`, `AI_BASE_URL=""` (unchanged from Phase 8) |
| `npm run build` (frontend) | Success, 17 routes incl. `/student-dashboard/profile` (6.07 kB) |
| `npm run lint` | Cannot run — ESLint is not configured in this repo (`next lint` opens the interactive setup prompt). Pre-existing condition, not introduced by Phase 9. |
| Secret scan (untracked + modified Phase 9 files) | Clean — only reference is `settings.AI_API_KEY` in provider.py |

Test coverage in `test_profile_api.py` (15 tests): unauth → 401 for all four
endpoints; new-user defaults for profile and preferences; create/upsert for
profile and preferences; persistence after create; partial updates (omitted
fields unchanged) for both; `open_to_relocate=False` round-trip; and cross-user
isolation (profile + preferences) proving user A cannot read/overwrite user B.

## 6. Results Summary

- Phase 9 (Profile & Preferences) is fully implemented, wired, migrated, and
  tested. All required coverage is exercised and passing.
- No Phase 8 regression: provider factory tests and deterministic
  parsing/matching/insights suite remain green; provider-agnostic config
  defaults (empty `AI_MODEL`/`AI_BASE_URL`) are intact.
- Working tree contains both Phase 8 and Phase 9 changes, uncommitted by design
  (established repo discipline); no secrets introduced.

## 7. Blockers / Notes

- ESLint is not configured in this repository; `npm run lint` cannot run
  non-interactively. The frontend is validated via `npm run build`, which
  succeeds. If linting is wanted, set up ESLint config first (out of scope).
- `npm run lint`/Gradle: no other blockers for Phase 9.