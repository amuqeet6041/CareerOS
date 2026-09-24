import { apiFetch } from "@/lib/api";

/**
 * Fetch the authenticated user's profile.
 * GET /api/profile
 */
export async function getProfile() {
  return apiFetch("/api/profile");
}

/**
 * Partially update the authenticated user's profile.
 * PATCH /api/profile
 * @param {Object} data — { headline?, bio?, location?, country? }
 */
export async function updateProfile(data) {
  return apiFetch("/api/profile", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

/**
 * Fetch the authenticated user's career preferences.
 * GET /api/profile/preferences
 */
export async function getPreferences() {
  return apiFetch("/api/profile/preferences");
}

/**
 * Partially update the authenticated user's career preferences.
 * PATCH /api/profile/preferences
 * @param {Object} data — any subset of PreferencesUpdate fields
 */
export async function updatePreferences(data) {
  return apiFetch("/api/profile/preferences", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}
