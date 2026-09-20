import { apiFetch } from "@/lib/api";

// Placeholder job service. Connect to backend /api/jobs routes.
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
