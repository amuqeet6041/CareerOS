"use client";

import { useState, useEffect, useRef } from "react";
import { getJobs, getJobMatch } from "@/services/jobService";
import {
  RECOMMENDATION_CANDIDATES,
  RECOMMENDATION_DISPLAY_COUNT,
} from "@/lib/constants";

/**
 * Deterministic, bounded dashboard recommendations.
 *
 * Fetch up to `candidates` newest jobs (one request), then one
 * /api/jobs/{id}/match per candidate. A job is only eligible when its overall
 * match score is real and meaningful: non-null and above zero (a 0 score means
 * zero overlap with the resume -- not a recommendation). Eligible jobs are
 * sorted by overall match descending and the top `displayCount` are returned,
 * each paired with its match entry in the shape JobCard's MatchPill expects
 * ({ status: "success", data }).
 *
 * Intentionally disabled when no resume exists so we never fire a doomed
 * batch of no-resume 404s.
 */
export function useJobRecommendations({
  enabled = true,
  candidates = RECOMMENDATION_CANDIDATES,
  displayCount = RECOMMENDATION_DISPLAY_COUNT,
} = {}) {
  const [jobs, setJobs] = useState([]);
  const [matchMap, setMatchMap] = useState({});
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [nonce, setNonce] = useState(0);
  const cancelled = useRef(false);

  useEffect(() => {
    if (!enabled) return undefined;
    cancelled.current = false;
    setLoading(true);
    setError(null);

    getJobs({ page: 1, page_size: candidates })
      .then((data) => {
        if (cancelled.current) return;
        const list = Array.isArray(data?.items)
          ? data.items.slice(0, candidates)
          : [];
        setJobs(list);

        if (list.length === 0) {
          setMatchMap({});
          setRecommendations([]);
          return;
        }

        return Promise.allSettled(
          list.map((job) => getJobMatch(job.id))
        ).then((results) => {
          if (cancelled.current) return;
          const next = {};
          results.forEach((result, idx) => {
            const job = list[idx];
            if (result.status === "fulfilled") {
              next[job.id] = { status: "success", data: result.value };
            } else {
              const status = result.reason?.status;
              const message = String(result.reason?.message || "").toLowerCase();
              if (status === 401 || status === 403) {
                next[job.id] = { status: "sign-in" };
              } else if (status === 404 && message.includes("resume")) {
                next[job.id] = { status: "no-resume" };
              } else {
                next[job.id] = { status: "error" };
              }
            }
          });
          setMatchMap(next);
        });
      })
      .catch((err) => {
        if (cancelled.current) return;
        setError(err.message || "Couldn't load job recommendations");
      })
      .finally(() => {
        if (!cancelled.current) setLoading(false);
      });

    return () => {
      cancelled.current = true;
    };
  }, [enabled, candidates, nonce]);

  useEffect(() => {
    if (jobs.length === 0 || Object.keys(matchMap).length === 0) {
      setRecommendations([]);
      return;
    }
    const scored = jobs
      .filter((job) => {
        const match = matchMap[job.id];
        return (
          match?.status === "success" &&
          match.data?.overall_match_percentage != null &&
          match.data.overall_match_percentage > 0
        );
      })
      .sort(
        (a, b) =>
          matchMap[b.id].data.overall_match_percentage -
          matchMap[a.id].data.overall_match_percentage
      )
      .slice(0, displayCount)
      .map((job) => ({ job, match: matchMap[job.id] }));
    setRecommendations(scored);
  }, [jobs, matchMap, displayCount]);

  return {
    recommendations,
    matchMap,
    jobs,
    candidateCount: jobs.length,
    loading,
    error,
    refetch: () => setNonce((value) => value + 1),
  };
}