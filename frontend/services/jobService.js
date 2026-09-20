import { apiFetch } from "@/lib/api";

// Connects to the backend /api/jobs routes. The backend returns a paginated
// envelope for lists; detail/save return single records. Phase 4 wires the
// jobs UI to this service.
export async function getJobs(filters = {}) {
  const params = new URLSearchParams(filters).toString();
  return apiFetch(`/api/jobs${params ? `?${params}` : ""}`);
}

export async function getJobById(id) {
  return apiFetch(`/api/jobs/${id}`);
}

export async function saveJob(id) {
  return apiFetch(`/api/jobs/${id}/save`, { method: "POST" });
}
