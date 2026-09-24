# CareerOS — Phase UI — Premium User Interface & Light/Dark Theme

Date: 2026-09-24 — working tree only, no commit, no push (matching the repo's
established Phase discipline). Frontend-only: no backend/API/data changes.

## 1. Objective

Transform CareerOS from a functional-but-plain interface into a premium,
polished product surface with a coherent design system, dual Light/Dark theme,
and refined interactions — while preserving every byte of existing backend and
API behavior. All work is strictly inside `frontend/`.

## 2. Design Tokens (palette for both themes)

All colors are CSS variables defined in `frontend/app/globals.css` and exposed
as Tailwind tokens in `frontend/tailwind.config.js` (`rgb(var(--color-x))` so
opacity modifiers keep working).

- **Light theme — "Warm White + Navy + Gold"** (warm-white canvas):
  - `canvas` `#F8F6F1` (warm off-white), `surface` `#FFFFFF` (cards),
    `elevated` `#F0EEE7`, `elevated-strong` `#E7E3D9`.
  - Ink/navigation: `navy` `#172033`, `navy.light` `#4B5563`, `line`
    `#E5E1D7`, `line-subtle` `#ECE9E0`.
  - Functional accent: `accent` `#2563EB`, `accent.light` `#3B82F6`,
    `primary`/`primary.bright` sliding blue scale.
  - Decorative Gold accent: `gold` `#C9973E` (eyebrows, hero badge).
  - Status: `success` `#0B7A4B`, `warning` `#B45309`, `danger` `#B91C1C`,
    `info` `#2563EB`, `violet` `#7C3AED`.
- **Dark theme — "Midnight + Electric accents"**:
  - `canvas` `#070B14`, `surface` `#0D1422`, `elevated` `#131B2E`,
    `elevated-strong` `#1B2740`, `line` `#24304A`, `line-subtle` `#1A2438`.
  - `navy` `#F1F5FB` (text), `navy.light` `#A9B4C8`, `ink` `#E2E8F0`,
    `muted` `#94A3B8`.
  - Functional accent: `accent` `#3B82F6`, `accent.light` `#60A5FA`.
  - Decorative gold token flips to electric blue `#38BDF8` for pops.
  - Status tones use dark-appropriate variants of the same hue families.
- Shadows: `card`, `card-hover`, `glow-primary` (accent halo),
  `glow-gold`. Keyframes: `fade-in`, `fade-in-up`, `scale-in`, `slide-up`,
  `shimmer`.
- Decision: `accent` is always the functional blue; `gold` is the decorative
  pop that adapts per theme (gold in Light, electric blue in Dark).

## 3. Theme Switcher — persistence, system-sync, and no-flash

- `components/shared/ThemeProvider.jsx` (client, wraps the whole app from
  `app/layout.js`): reads localStorage key `careeros_theme`, applies the
  `dark` class to `<html>`, falls back to `prefers-color-scheme`, and listens
  to OS theme changes via `matchMedia`.
- `components/shared/ThemeToggle.jsx`: sun/moon morphing icon button with
  three variants (ghost/solid/soft) used in the public navbar and dashboard
  topbar.
- No-flash: an inline `<script>` in `app/layout.js` `<head>` applies the
  stored/OS theme before first paint, so refreshes never flash the wrong theme.
- Root shell classed `bg-canvas font-sans text-navy antialiased`, so every
  page inverts correctly by default.

## 4. Typography & Base Layer

- Font stack `Inter → Geist → Manrope → system` in `tailwind.config.js`.
- `app/globals.css` base layer: default `border-color: var(--color-line)`,
  selection color, visible focus-visible outlines, keyframe utilities,
  `prefers-reduced-motion` kill switch for all animation utilities, plus
  `no-scrollbar`, `bg-grid`, `bg-dots`, `text-gradient-blue`, and
  `text-gradient-gold` decorative utilities.

## 5. Shared Component Library

All rebuilt on the token system with the same APIs (callers unchanged):

- `Button.jsx` — primary/secondary/outline/ghost/dark variants, glows,
  hover lift, `active:scale-[0.98]`, focus ring, motion-safe transitions.
- `Loading.jsx` — shimmer spinner with ∫-shaped design accent.
- `EmptyState.jsx` — centered decorative-state component with icon/action slots.
- `Modal.jsx` — backdrop fade + `scale-in` panel, danger-tinted heads.
- `Footer.jsx` — premium glow header line, brand, dual-mode links, tagline.
- `Navbar.jsx` — floating glass nav pill, theme-adaptive, logo wordmark
  (gradient + gold), desktop + mobile menu, auth-aware actions, wrapped in
  theme-aware shadow/backdrop; `ThemeToggle` present in both modes.

## 6. Landing Page (`/`)

- Hero: warm/cool grid + radial glows, staggered `fade-in-up` intro,
  gradient "OS" accent word, animated CTAs, and a Dashboard match-preview
  card mock (match ring, stat chips, surface card with glow).
- INDICATORS strip, feature grid (premium tinted cards + icon chips),
  How It Works (numbered steps with progress line), AI Matching section,
  Trusted-by band, final CTA banner. Eyebrows use the gold/electric accent.

## 7. Public Pages — About & Contact

Rebuilt with the section system: premade eyebrow badge + two-column layout,
profile-card + glow stats (About), and a channel-card layout with dual-side
illustration (Contact). Same routing logic and copy preserved.

## 8. Authentication Pages & Forms

- `login`/`register` pages: full-viewport grid + glow backdrop, brand row with
  `ThemeToggle`, centered premium card, footer links intact.
- `LoginForm.jsx`/`RegisterForm.jsx`: restyled inputs via a shared
  `INPUT_CLASS`-style constant and premium Button; **zero logic changes**
  (validation, error display, auth flow untouched).

## 9. Dashboard Command Center

- New `components/dashboard/DashboardShell.jsx` (client): consistent page
  envelope + max-width responsive wrapper adopted by all 7 dashboard pages.
- `DashboardSidebar.jsx`: brand wordmark, icon nav with active pill, sign-out
  footer card, and a mobile top bar with slide-down nav.
- `DashboardHeader.jsx`: route-derived title, sticky translucent bar,
  `ThemeToggle`, and an avatar menu with sign-out.
- `student-dashboard/layout.js` guard classes now `bg-canvas`.
- All 10 `components/dashboard/*` sections (ProfileSummary, ProfileCompletion,
  ResumeStatusCard, RecommendedJobs, ApplicationStats, RecentApplications,
  SavedJobsSummary, CareerOverview, StudentDashboard, DashboardSection,
  DashboardSkeleton) migrated to tokens: surfaces, neutral `elevated` fills,
  color-coded pills/tints, and elevated skeleton states. Logic unchanged.

## 10. Job Explorer (public + student)

- `JobHero.jsx` rewritten theme-aware: `bg-canvas`, radial glow + grid mask,
  `text-navy` headline, newsletter-less search intro (public `jobs` Suspense
  fallback also tokenized).
- `JobSearch.jsx`: single theme-safe input style (no undefined-`dark`
  reference), preserving both `variant` call sites.
- `JobCard`, `JobFilters`, `JobList`, `JobPagination`, `MatchCard`,
  `MatchPill`, `MatchScore`, `SaveJobButton`, `ApplyNowButton`, `Skeletons`,
  `JobDetailView`, `JobDetails`, `JobsExplorer`: full token sweep — surface
  cards, `shadow-card`/`hover:shadow-card-hover`, neutral match pills on
  `elevated`/`canvas`, slate-free borders, tinted focus rings. All hooks,
  fetch/refetch behavior, and copy preserved.

## 11. Job Detail Page (`/jobs/[id]`)

JobDetailView + JobDetails tokenized: main card with premium title row,
info chips, description sections, apply/save actions, and recommendation
cards using the match palette. API/data flow untouched.

## 12. Saved Jobs

Saved-jobs page: rebuild of header + empty/error scaffolds on `EmptyState`,
tokenized `SaveJobButton` (saved state accent-tinted vs neutral), and the
same saved-toggle/apply-tracking wiring.

## 13. Applications

`ApplicationStatus.jsx`: status pill map rewritten with per-status token
classes (`info`, `violet`, `success`, `danger`) — labels preserved so status
is never color-only. `ApplicationCard.jsx` and tracked-application scaffold
tokenized. Data/sorting unchanged.

## 14. Profile Page

`student-dashboard/profile/page.js` wrapped in `DashboardShell maxWidth="5xl"`
(in loading/error/main branches), form sections tokenized, resume-data link
card retained; save logic and API sync behavior untouched.

## 15. Resume Experience

`ResumeManager`, `ResumeUpload`, `ResumePreview`, `ExperienceList`,
`EducationList`, `SkillsList`, `CertificationsList`: surfaces, accent action
buttons, hover states, tinted skill tags, sized skeleton states. All
upload/reparse/refresh copy and behavior preserved ("basic parse" labels
kept verbatim).

## 16. Career Insights

`CareerSnapshot`, `CareerDirections`, `ActionPlanSection`, `SkillGapsSection`,
`AICareerInsights`, `CareerInsightsEmpty`, `priority.js`: tokenized badges,
progress bars, chart tints, and empty states. The AI fallback copy
("AI insights temporarily unavailable…") and deterministic-analysis framing
were preserved verbatim.

## 17. Animations, Accessibility & Responsiveness

- Animations (motion-safe only): hero/stat/CTA `fade-in-up` + `fade-in`
  staggers, navbar product-glow, button hover lift, modal `scale-in`,
  theme-toggle sun/moon morph, shimmer loading.
- `prefers-reduced-motion` disables all animated utilities.
- Visible `focus-visible` outlines, `:focus-visible` ring utilities on
  interactive elements, aria-labels on icon-only controls keep a11y intact.
- Responsive: dashboard shell throttles from 1 → 2 → 3 columns across
  `lg`/`xl`; sidebar collapses to a mobile top-bar; landing hero stacks;
  auth cards shrink to a single column; navbar mobile menu.

## 18. Validation & Git End-State

| Check | Result |
|---|---|
| `npm run build` (frontend) | Success — all 17 routes compile & prerender |
| Route sizes | `/` 99.6 kB, `/student-dashboard` 111 kB, `/jobs` 110 kB, all routes < 111 kB first load |
| Legacy-token scan (hex `#xxxxxx`, `bg-white`, `slate-*`, `bg-*-50`, `border-border`, `ring-blue-*`) | 0 matches in `app/` + `components/` |
| Final grep fixes | `ThemeToggle` soft variant `hover:bg-white/[0.08]` → `hover:bg-elevated`; public jobs Suspense fallback `bg-white/10` → `bg-elevated` |
| Gold accent applied | Landing eyebrows + hero badge (`text-gold` / `border-gold/30 bg-gold/10`) |
| Backend touched | None — all diffs are in `frontend/` |
| `git status` | 69 modified files + 3 new files (DashboardShell, ThemeProvider, ThemeToggle) — all under `frontend/`; no backend or `.env` changes |

Files changed (frontend only): 69 modified, 3 added across `app/`, `components/`,
and `tailwind.config.js` (+1443 −908). No package.json changes, no new
dependencies.

## Phase Status

- All aspects of the Phase UI spec are implemented and validated. Theme system,
  token sweep, page redesigns, animations/a11y, and the frontend build are
  complete.
- Standing issues carried forward (pre-existing, out of scope): ESLint is not
  configured (`npm run lint` cannot run); live Gemini 429/503 intermittency is
  transient and unrelated to UI work.

**PHASE UI — COMPLETE**