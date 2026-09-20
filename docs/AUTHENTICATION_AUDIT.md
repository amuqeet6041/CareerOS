# AUTHENTICATION AUDIT — CareerOS

Date: 2026-09-20
Scope: `frontend/` + `backend/` authentication & redirection flow.

## 1. Symptoms reported
- "Fetch error" when logging in / registering.
- Login "Sometimes" fails (intermittent).
- Registration does not appear to complete.
- User is not redirected to `/student-dashboard` after registering.
- Logout / auth state behavior uncertain when sessions go stale.

## 2. Root causes found (and fixes)

### 2.1 Backend could not reach its database — every auth request 500'd
The backend is started as `uvicorn app.main:app` with **no `backend/.env`**
and **no `DATABASE_URL`** in the environment. `config.py` therefore fell back
to the example value `postgresql://user:password@localhost:5432/careeros`
(`backend/.env.example`). The local PostgreSQL server answered:

> FATAL: password authentication failed for user "user"

Every auth request that touches the DB (`register`, `login`, `me`) threw an
unhandled `OperationalError` → **HTTP 500 "Internal Server Error"**. After a
burst of failures the uvicorn reload worker also dropped connections, producing
the browser-level "Failed to fetch" the user saw.

**Fix:** created `backend/.env` (not committed; gitignored by convention) pointing
the dev instance at the project's real on-disk dev database:

```
DATABASE_URL=sqlite:///./careeros.db
ENVIRONMENT=development
```

The running uvicorn `--reload` process re-imported app code when `config.py`
changed and picked up the new settings automatically. Postgres remains fully
supported — anyone who prefers it just edits `backend/.env`, e.g.
`DATABASE_URL=postgresql://user:password@localhost:5432/careeros`.

### 2.2 CORS allow-list was too narrow — intermittent "Failed to fetch"
`ALLOWED_ORIGINS` defaulted to `["http://localhost:3000"]` only. The dev
environment legitimately runs **two** Next.js dev servers (port 3000 **and**
3001, because 3000 was already bound) and users commonly open the app via
`http://127.0.0.1:3000` or `http://localhost:3001`. Those origins were
blocked by the same-origin policy, so their API calls failed with the browser's
generic "Failed to fetch" — matching the **intermittent** login failures.

**Fix:** expanded the explicit allow-list in `backend/app/core/config.py:45`:

```
["http://localhost:3000", "http://127.0.0.1:3000",
 "http://localhost:3001", "http://127.0.0.1:3001"]
```

No wildcard (`allow_origins` stays explicit, `allow_credentials=True`). Verified
live: responses echo the allowed origin back, and a disallowed origin (e.g.
`http://evil.com`) gets no `Access-Control-Allow-Origin` header.

### 2.3 Raw "Failed to fetch" error surfaced to users
`lib/api.js` let the browser's network `TypeError` propagate unchanged, so the
user saw the unhelpful native message.

**Fix:** `frontend/lib/api.js` now wraps the fetch call:
- network-level failure → friendly dev-safe error *"Unable to connect to
  CareerOS API. Please check that the backend is running."*, `err.status = 0`
  (so 401/404/409 consumers are unaffected);
- HTTP errors with a `detail` **array** (FastAPI 422 validation) are
  stringified into readable messages instead of an array object;
- string `detail` (e.g. "Email already registered", "Invalid credentials") is
  preserved.

### 2.4 Registration did not land on the dashboard
`RegisterForm.jsx` redirected to `/login` after a successful registration. The
expected behavior is a registration that *completes* and reaches
`/student-dashboard`.

**Fix:** `frontend/components/auth/RegisterForm.jsx` now performs the existing
auth flow after registration: `register(form)` → `signIn({email, password})` →
`router.push("/student-dashboard")`. The automatic sign-in reuses the battle-
tested login path (token save → `getMe` → auth state), no backend auth change,
no weakened security. If automatic sign-in ever fails, it falls back to
`/login` so the user can still sign in normally.

## 3. What was deliberately NOT changed
- Backend auth design: register still returns `UserOut` (no token); login still
  issues the HS256 bearer token; passlib/pbkdf2-bcrypt hashing, `bcrypt==4.0.1`
  pin, and the JWT dev fallback rules are untouched.
- No `middleware.js/ts` guard was added; `/student-dashboard/layout.js` already
  redirects unauthenticated users to `/login` (verified correct ordering:
  waits for `isLoading`, then `router.replace("/login")`).
- `useAuth.signIn` already saves the token **before** `getMe()` (historical
  ordering bug is not present).
- The dev database file `careeros.db` was preserved (2 real users). The single
  temporary audit account created during smoke testing was deleted afterwards.

## 4. Verification
- Backend suite: `python -m pytest -q` → **222 passed** (no regressions).
- Frontend build: `npm run build` → success, 17 routes.
- Live API smoke against the running backend (port 8000):
  - `GET /api/health` → 200
  - register → 200 (user created)
  - login → 200 with `access_token`
  - `GET /api/auth/me` with token → 200
  - duplicate email register → 400 "Email already registered"
  - wrong password → 401 "Invalid credentials"
  - invalid email → 422 (validation detail list)
  - garbage token `me` → 401 "Invalid or expired token"
  - logout → 200
  - CORS: allowed origins echo correctly; disallowed origin rejected.

## 5. Operational notes
- `uvicorn` and the Next.js dev servers must be (re)started from their own
  directories so they read the local `.env` files:
  - backend: `python -m uvicorn app.main:app --reload` (cwd = `backend/`, needs
    `backend/.env`)
  - frontend: `npm run dev` (cwd = `frontend/`, `NEXT_PUBLIC_API_URL` defaults
    to `http://localhost:8000`)
- If the backend port, DB, or host changes, update `backend/.env` and/or
  `frontend/.env` (`NEXT_PUBLIC_API_URL`) and restart both servers.
- `backend/.env` and `frontend/.env` must never be committed (they sit next to
  their `.env.example` peers).

## 6. Limitations
- End-to-end browser automation was out of scope for this audit; the flows were
  verified at the API level plus the exact request sequences the frontend
  performs, and the frontend changes compile/green-build. A manual pass through
  the UI on `http://localhost:3000` and `http://localhost:3001` is recommended.