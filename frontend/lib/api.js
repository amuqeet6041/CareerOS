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

// Turn a FastAPI error body into a readable message without leaking backend
// internals. 422 bodies carry an array of validation items; pick the messages.
function detailFromBody(body) {
  if (!body) return "";
  if (typeof body.detail === "string") return body.detail;
  if (Array.isArray(body.detail)) {
    return body.detail
      .map((item) => item?.msg || "Invalid value")
      .filter(Boolean)
      .join("; ");
  }
  return "";
}

export async function apiFetch(path, options = {}) {
  let res;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: buildHeaders(options),
    });
  } catch (_) {
    // Network-level failure: backend unreachable, or the browser blocked the
    // cross-origin request. No backend details exist to surface.
    const err = new Error(
      "Unable to connect to CareerOS API. Please check that the backend is running."
    );
    err.status = 0;
    throw err;
  }

  if (!res.ok) {
    let message = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      const detail = detailFromBody(body);
      if (detail) message = detail;
    } catch (_) {
      // Non-JSON error body; keep the fallback message.
    }
    // An authenticated request that gets a 401 (without a backend-provided
    // detail, e.g. during login the API returns "Invalid email or password")
    // means the token expired while using the app.
    if (res.status === 401 && getToken() && !message.startsWith("Request failed")) {
      message = "Your session has expired. Please sign in again.";
    }
    const err = new Error(message);
    err.status = res.status;
    throw err;
  }

  if (res.status === 204) return null;
  return res.json();
}