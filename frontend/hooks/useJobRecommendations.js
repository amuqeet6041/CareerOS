"use client";

import { useState, useEffect, useRef } from "react";
import { getLiveRecommendations } from "@/services/jobService";
import { RECOMMENDATION_DISPLAY_COUNT } from "@/lib/constants";

/**
 * Live, resume-driven dashboard recommendations.
 *
 * One request to /api/jobs/recommendations: the backend builds search queries
 * from the user's resume, fetches live postings, and returns them ranked by
 * match. Only jobs with a real, non-zero overall match are shown (0% means no
 * overlap with the resume -- not a recommendation). Each entry is paired with
 * its match in the shape JobCard's MatchPill expects ({ status, data }).
 *
 * The backend caches results per resume to protect the provider quota;
 * `refetch` forces a fresh live search.
 *
 * Intentionally disabled when no resume exists so we never fire a doomed
 * no-resume 404.
 */
export function useJobRecommendations({
  enabled = true,
  displayCount = RECOMMENDATION_DISPLAY_COUNT,
} = {}) {
  const [items, setItems] = useState([]);
  const [queries, setQueries] = useState([]);
  const [source, setSource] = useState(null);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState(null);
  const [refresh, setRefresh] = useState(0);
  const cancelled = useRef(false);

  useEffect(() => {
    if (!enabled) return undefined;
    cancelled.current = false;
    setLoading(true);
    setError(null);

    getLiveRecommendations({ refresh: refresh > 0 })
      .then((data) => {
        if (cancelled.current) return;
        setItems(Array.isArray(data?.items) ? data.items : []);
        setQueries(Array.isArray(data?.queries) ? data.queries : []);
        setSource(data?.source || null);
      })
      .catch((err) => {
        if (cancelled.current) return;
        setItems([]);
        setError(err.message || "Couldn't load job recommendations");
      })
      .finally(() => {
        if (!cancelled.current) setLoading(false);
      });

    return () => {
      cancelled.current = true;
    };
  }, [enabled, refresh]);

  const recommendations = items
    .filter(({ match }) => match?.overall_match_percentage > 0)
    .slice(0, displayCount)
    .map(({ job, match }) => ({ job, match: { status: "success", data: match } }));

  return {
    recommendations,
    jobs: items.map(({ job }) => job),
    candidateCount: items.length,
    queries,
    source,
    loading,
    error,
    refetch: () => setRefresh((value) => value + 1),
  };
}
