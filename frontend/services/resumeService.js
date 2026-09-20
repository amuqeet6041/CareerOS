import { apiFetch } from "@/lib/api";

// Placeholder resume service. Connect to backend /api/resume routes.
export async function uploadResume(file) {
  const formData = new FormData();
  formData.append("file", file);

  return apiFetch("/api/resume/upload", {
    method: "POST",
    headers: {}, // let the browser set multipart boundary
    body: formData,
  });
}

export async function getResumeAnalysis() {
  return apiFetch("/api/resume/analysis");
}

export async function analyzeResume() {
  return apiFetch("/api/resume/analyze", { method: "POST" });
}
