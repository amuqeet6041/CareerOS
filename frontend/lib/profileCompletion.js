// Deterministic profile completion calculator for the student dashboard.
//
// Completion is a pure function of real, currently-supported profile data:
//   - account      the authenticated user (name + email from GET /api/auth/me)
//   - resume       a resume was uploaded (GET /api/resume/analysis != null)
//   - skills       >= 1 skill was extracted from the resume
//   - education    >= 1 education record was extracted
//   - experience   >= 1 experience record was extracted
//   - certifications >= 1 certification was recorded
//
// The six components always form the denominator, so the number is stable and
// transparent: 6/6 = 100% means every section the platform supports carries
// real data. No component is ever faked, and partially populated resume
// sections count honestly (e.g. no certifications => that component is 0).
//
// This formula is documented in docs/PHASE_6_REPORT.md.

export const COMPLETION_COMPONENTS = [
  { key: "account", label: "Account" },
  { key: "resumeUploaded", label: "Resume uploaded" },
  { key: "skills", label: "Skills extracted" },
  { key: "education", label: "Education recorded" },
  { key: "experience", label: "Experience recorded" },
  { key: "certifications", label: "Certifications recorded" },
];

function hasAny(list) {
  return Array.isArray(list) && list.length > 0;
}

export function computeProfileCompletion({ user = null, resume = null } = {}) {
  const checks = {
    account: Boolean(user && user.name && user.email),
    resumeUploaded: Boolean(resume),
    skills: hasAny(resume?.skills),
    education: hasAny(resume?.education),
    experience: hasAny(resume?.experience),
    certifications: hasAny(resume?.certifications),
  };

  const total = COMPLETION_COMPONENTS.length;
  const completed = COMPLETION_COMPONENTS.filter(({ key }) => checks[key]).length;
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

  return {
    completed,
    total,
    percentage,
    checks,
    components: COMPLETION_COMPONENTS.map(({ key, label }) => ({
      key,
      label,
      met: checks[key],
    })),
  };
}