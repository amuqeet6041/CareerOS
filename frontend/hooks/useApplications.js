"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  getApplications,
  createApplication as createApplicationRequest,
} from "@/services/applicationService";

/**
 * Application-tracking state for the current user.
 *
 * `appliedIds` is a Set of job ids derived from a single GET /api/applications
 * request. Cards use it to show an accurate "Applied" state without one
 * request per card. `markApplied` is used after a 409 (already applied) so
 * the UI converges without duplicating records.
 */
export function useApplications({ enabled = true } = {}) {
  const [applications, setApplications] = useState([]);
  const [appliedIds, setAppliedIds] = useState(() => new Set());
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState(null);
  const [nonce, setNonce] = useState(0);
  const cancelled = useRef(false);

  useEffect(() => {
    if (!enabled) return undefined;
    cancelled.current = false;
    setLoading(true);
    setError(null);

    getApplications()
      .then((items) => {
        if (cancelled.current) return;
        const list = Array.isArray(items) ? items : [];
        setApplications(list);
        setAppliedIds(new Set(list.map((app) => app.job_id)));
      })
      .catch((err) => {
        if (cancelled.current) return;
        setError(err.message || "Couldn't load applications");
      })
      .finally(() => {
        if (!cancelled.current) setLoading(false);
      });

    return () => {
      cancelled.current = true;
    };
  }, [enabled, nonce]);

  const createApplication = useCallback(async (jobId) => {
    const app = await createApplicationRequest(jobId);
    setAppliedIds((prev) => new Set(prev).add(jobId));
    setApplications((prev) =>
      prev.some((existing) => existing.job_id === jobId)
        ? prev
        : [app, ...prev]
    );
    return app;
  }, []);

  const markApplied = useCallback((jobId) => {
    setAppliedIds((prev) => new Set(prev).add(jobId));
  }, []);

  const refetch = useCallback(() => setNonce((value) => value + 1), []);

  return {
    applications,
    appliedIds,
    loading,
    error,
    refetch,
    createApplication,
    markApplied,
  };
}