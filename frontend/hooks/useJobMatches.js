"use client";

import { useState, useEffect, useRef } from "react";
import { getJobMatch } from "@/services/jobService";
import { MAX_LIST_MATCHES } from "@/lib/constants";

/**
 * Compute match results for the visible jobs on the current list page only.
 *
 * Intentionally bounded (`limit`) so navigation never fires dozens of match
 * requests; the primary match presentation lives on the job detail page and
 * Phase 5 will add server-side match ordering for the full result set.
 */
export function useJobMatches(jobs = [], { enabled = true, limit = MAX_LIST_MATCHES } = {}) {
  const [matchMap, setMatchMap] = useState({});
  const [loadingIds, setLoadingIds] = useState([]);

  // Track the batch so stale responses never overwrite newer ones.
  const batchId = useRef(0);

  const visible = enabled ? jobs.slice(0, limit) : [];
  const visibleIds = visible.map((job) => job.id).sort((a, b) => a - b).join(",");

  useEffect(() => {
    if (!enabled) {
      setMatchMap({});
      setLoadingIds([]);
      return;
    }

    const current = ++batchId.current;
    setMatchMap({});
    setLoadingIds(visible.map((job) => job.id));

    Promise.allSettled(
      visible.map(async (job) => {
        try {
          const data = await getJobMatch(job.id);
          return [job.id, { status: "success", data }];
        } catch (err) {
          const status = err?.status;
          const message = String(err?.message || "").toLowerCase();
          if (status === 403 || status === 401) {
            return [job.id, { status: "sign-in" }];
          }
          if (status === 404 && message.includes("resume")) {
            return [job.id, { status: "no-resume" }];
          }
          return [job.id, { status: "error" }];
        }
      })
    ).then((results) => {
      if (current !== batchId.current) return;
      const next = {};
      for (const result of results) {
        if (result.status === "fulfilled") {
          const [id, entry] = result.value;
          next[id] = entry;
        }
      }
      setMatchMap(next);
      setLoadingIds([]);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visibleIds, enabled]);

  return { matchMap, loadingIds };
}