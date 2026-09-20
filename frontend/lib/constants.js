export const WORK_MODES = ["remote", "hybrid", "onsite"];

export const EMPLOYMENT_TYPES = [
  "full-time",
  "part-time",
  "contract",
  "internship",
  "temporary",
  "freelance",
];

// Alias kept for older call-sites; prefer EMPLOYMENT_TYPES going forward.
export const JOB_TYPES = EMPLOYMENT_TYPES;

export const WORK_MODE_OPTIONS = [
  { value: "", label: "Any work mode" },
  { value: "remote", label: "Remote" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "On-site" },
];

export const EMPLOYMENT_TYPE_OPTIONS = [
  { value: "", label: "Any employment type" },
  ...EMPLOYMENT_TYPES.map((type) => ({
    value: type,
    label: type.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
  })),
];

export const SORT_OPTIONS = [
  { value: "date_newest", label: "Newest" },
  { value: "date_oldest", label: "Oldest" },
  { value: "salary_desc", label: "Highest Salary" },
];

export const DEFAULT_SORT = "date_newest";

export const PAGE_SIZE = 20;

// Cap for per-page match computations on job lists. Phase 5 replaces this with
// server-side scoring so the whole result set can be ordered by match.
export const MAX_LIST_MATCHES = 12;

export const APP_NAME = "CareerOS";