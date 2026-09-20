import { apiFetch } from "@/lib/api";

export async function getCareerInsights() {
  return apiFetch("/api/career-insights");
}