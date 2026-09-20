import { getToken } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function buildHeaders(options) {
  const token = getToken();

  if (options.body instanceof FormData) {
    // Let the browser set the multipart boundary; the token still travels along.
    return {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    };
  }

  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };
}

export async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: buildHeaders(options),
  });

  if (!res.ok) {
    let message = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      if (body && body.detail) message = body.detail;
    } catch (_) {
      // Non-JSON error body; keep the fallback message.
    }
    const err = new Error(message);
    err.status = res.status;
    throw err;
  }

  if (res.status === 204) return null;
  return res.json();
}