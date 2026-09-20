import { apiFetch } from "@/lib/api";

// Backend contracts (Phase 4):
//   GET /api/jobs          -> { items: [JobResponse], total, page, page_size, total_pages }
//   GET /api/jobs/{id}     -> JobResponse
//   GET /api/jobs/{id}/match -> JobMatchResponse (auth required)
// Saved jobs arrive in Phase 5; the dead /save endpoint from Phase 3 is intentionally
// not wired up so the UI never fakes persistence.

function buildQuery(params) {
  const search = new URLSearchParams();

  for (const [key, value] of Object.entries(params || {})) {
    if (value === undefined || value === null || value === "") continue;
    if (key === "signal") continue;
    search.set(key, String(value));
  }

  return search.toString();
}

export async function getJobs(filters = {}, options = {}) {
  const query = buildQuery(filters);
  return apiFetch(`/api/jobs${query ? `?${query}` : ""}`, options);
}

export async function getJobById(id) {
  return apiFetch(`/api/jobs/${id}`);
}

export async function getJobMatch(id) {
  return apiFetch(`/api/jobs/${id}/match`);
}