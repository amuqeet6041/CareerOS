# CareerOS — User Flow

> Status tags: ✅ implemented today · 🔜 planned / not yet implemented.

1. **Landing page** — User learns what CareerOS does and how it works. ✅
2. **Registration / login** — User creates an account or signs in with JWT
   auth. ✅
3. **Resume upload** — User uploads a CV (PDF/DOCX) from the dashboard. ✅
4. **Resume analysis** — Backend extracts text and performs deterministic
   structured extraction (skills, education, experience, certifications). ✅
   (AI-based analysis is planned, not implemented.)
5. **Profile creation** — Extracted data populates the user's profile
   dashboard. 🔜 (stored in DB; dashboard wiring is partial)
6. **Job discovery** — CareerOS fetches live jobs from approved sources. 🔜
   (the jobs API exists but returns `[]` until a provider is integrated)
7. **Job matching** — Each job is scored against the user's profile
   (Skill Match %, Qualification Match %). 🔜 (matching utilities exist;
   the score API/UI is planned)
8. **Job details** — User views full job details, including salary,
   location, and work mode when available. 🔜
9. **Save job** — User bookmarks jobs of interest for later. 🔜 (backend
   route exists; persistence & UI are planned)
10. **Apply** — User applies via the provided application link. 🔜
11. **Application tracking** — User tracks status (applied, in review,
    interview, offer, rejected). ✅ backend only (create/list/update, owner
    scoping); frontend UI is planned.
12. **Career insights** — User sees an overview of their career progress
    and (eventually) suggested skill gaps or learning paths. 🔜