import { apiFetch } from "@/lib/api";

// Saved jobs are persisted server-side (SavedJob rows) and only exist for
// authenticated users. apiFetch attaches the bearer token automatically.
export async function getSavedJobs() {
  return apiFetch("/api/jobs/saved");
}

export async function saveJob(jobId) {
  return apiFetch(`/api/jobs/${jobId}/save`, { method: "POST" });
}

export async function unsaveJob(jobId) {
  return apiFetch(`/api/jobs/${jobId}/save`, { method: "DELETE" });
}