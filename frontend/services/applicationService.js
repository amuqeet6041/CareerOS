import { apiFetch } from "@/lib/api";

// Placeholder application-tracking service. Connect to backend /api/applications routes.
export async function getApplications() {
  return apiFetch("/api/applications");
}

export async function createApplication(jobId) {
  return apiFetch("/api/applications", {
    method: "POST",
    body: JSON.stringify({ job_id: jobId }),
  });
}

export async function updateApplicationStatus(id, status) {
  return apiFetch(`/api/applications/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
