# CareerOS — Development Roadmap

- **Phase 0 — Foundation & Stabilization** ✅ Complete. See
  `docs/PHASE_0_REPORT.md` for details. Fixed the frontend login flow, added
  Alembic migrations for the full schema, hardened JWT secret configuration,
  aligned the frontend/backend job contract, added a mobile dashboard menu and
  active nav states, prevented duplicate applications (404/409) with
  `Application`/`SavedJob` → `Job` ORM relationships, and added tests for
  migrations, matching utilities, and application uniqueness/relationships.
- **Phase 1 — Foundation**: Repository scaffolding, tooling, and base
  frontend/backend setup (this initial version).
- **Phase 2 — Authentication**: ✅ Real registration/login flows, JWT
  issuance and validation via a shared `get_current_user` dependency
  (`app/api/deps.py`), `GET /auth/me`, protected dashboard endpoints
  (resume, applications, job save), and a frontend `useAuth` session hook
  wired to real tokens/user. Application routes now query the DB scoped to
  the authenticated user. `test_auth.py` covers the auth flow with an
  in-memory database, including `401` behavior for missing/malformed/
  invalid/expired tokens, tokens referencing nonexistent users, and
  cross-user ownership isolation on applications.
- **Phase 3 — Resume Upload**: ✅ PDF and DOCX resume parsing and
  persistence. `resume_parser.py` deterministically extracts skills,
  education, experience, and certifications from sectioned resumes using
  PyMuPDF and python-docx (no LLM). Parsed data is stored per user in
  `Resume`/`Skill`/`Education`/`Experience`/`Certification`; re-uploading
  replaces the previous resume instead of duplicating. The resume dashboard
  page is wired to the live endpoints. `test_resume.py` covers auth, size,
  type, malformed/empty documents, and replace-on-reupload behavior with an
  in-memory database.
- **Phase 4 — AI Resume Analysis**: Connect an LLM provider for deeper
  analysis beyond the deterministic structured extraction (e.g., keyword
  suggestions, tailored summaries).
- **Phase 5 — Job APIs**: Integrate one or more approved job data sources
  via the `JobProvider` adapter pattern.
- **Phase 6 — Matching Engine**: Implement and refine Skill Match % and
  Qualification Match % logic; consider NLP/embeddings for better accuracy.
- **Phase 7 — Dashboard**: Build out the full student dashboard experience
  with real data (profile completion, recommendations, stats).
- **Phase 8 — Applications**: Full application tracking lifecycle and
  notifications.
- **Phase 9 — Testing**: Expand automated test coverage across frontend
  and backend.
- **Phase 10 — Deployment**: Containerize, configure CI/CD, and deploy to
  a production environment.