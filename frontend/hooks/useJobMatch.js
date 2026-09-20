"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { getJobMatch } from "@/services/jobService";

// Statuses describing every reachable state of the /api/jobs/{id}/match
// endpoint so the UI never guesses.
//   success  - full match payload
//   no-resume- job matched without a candidate resume (404 "resume")
//   sign-in  - 401, session invalid or missing
//   error    - transient/failure, retry allowed
export function useJobMatch(jobId, { enabled = true } = {}) {
  const [state, setState] = useState({
    status: "idle",
    data: null,
    error: null,
  });
  const cancelled = useRef(false);

  const load = useCallback(async () => {
    if (!enabled || !jobId) {
      setState({ status: "idle", data: null, error: null });
      return;
    }

    setState((prev) => ({ ...prev, status: "loading", error: null }));

    try {
      const data = await getJobMatch(jobId);
      if (cancelled.current) return;
      setState({ status: "success", data, error: null });
    } catch (err) {
      if (cancelled.current) return;

      const status = err?.status;
      const message = String(err?.message || "").toLowerCase();

      if (status === 404 && message.includes("resume")) {
        setState({ status: "no-resume", data: null, error: null });
      } else if (status === 401) {
        setState({ status: "sign-in", data: null, error: null });
      } else if (status === 404) {
        // Job not found; detail fetch handles the real 404 UI.
        setState({ status: "error", data: null, error: err });
      } else {
        setState({ status: "error", data: null, error: err });
      }
    }
  }, [jobId, enabled]);

  useEffect(() => {
    cancelled.current = false;
    load();
    return () => {
      cancelled.current = true;
    };
  }, [load]);

  const refetch = useCallback(() => load(), [load]);

  return { ...state, refetch };
}