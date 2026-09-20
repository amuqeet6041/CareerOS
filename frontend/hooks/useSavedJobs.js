"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { getSavedJobs, saveJob, unsaveJob } from "@/services/savedJobService";

/**
 * Saved jobs state for the current user.
 *
 * `savedIds` is a Set of job ids derived from a single GET /api/jobs/saved
 * request, so cards and detail pages never fire one request per card. Toggles
 * only update state after the backend confirms the mutation, so the UI never
 * pretends a save succeeded when the API failed.
 */
export function useSavedJobs({ enabled = true } = {}) {
  const [savedJobs, setSavedJobs] = useState([]);
  const [savedIds, setSavedIds] = useState(() => new Set());
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState(null);
  const [nonce, setNonce] = useState(0);
  const cancelled = useRef(false);

  useEffect(() => {
    if (!enabled) return undefined;
    cancelled.current = false;
    setLoading(true);
    setError(null);

    getSavedJobs()
      .then((items) => {
        if (cancelled.current) return;
        const list = Array.isArray(items) ? items : [];
        setSavedJobs(list);
        setSavedIds(new Set(list.map((item) => item.job_id)));
      })
      .catch((err) => {
        if (cancelled.current) return;
        setError(err.message || "Couldn't load saved jobs");
      })
      .finally(() => {
        if (!cancelled.current) setLoading(false);
      });

    return () => {
      cancelled.current = true;
    };
  }, [enabled, nonce]);

  const toggle = useCallback(async (jobId, currentlySaved) => {
    const nextSaved = !currentlySaved;
    if (nextSaved) {
      await saveJob(jobId);
    } else {
      await unsaveJob(jobId);
    }
    setSavedIds((prev) => {
      const next = new Set(prev);
      if (nextSaved) next.add(jobId);
      else next.delete(jobId);
      return next;
    });
    setSavedJobs((prev) =>
      nextSaved ? prev : prev.filter((item) => item.job_id !== jobId)
    );
    return true;
  }, []);

  const refetch = useCallback(() => setNonce((value) => value + 1), []);

  return { savedJobs, savedIds, loading, error, refetch, toggle };
}