"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { getJobs } from "@/services/jobService";
import { serializeFilters, initialFilters } from "@/lib/jobQuery";

/**
 * Fetch a paginated, filterable jobs list against /api/jobs.
 *
 * The URL is the source of truth: `initialFilters` is derived from the URL
 * query string, and every filter/sort/page change is reported back through
 * `onFiltersChange` so the page can keep the address bar in sync. External
 * changes (back/forward navigation, shared links) are re-applied through the
 * `initialFilters` prop without losing focus or resetting the page.
 */
export function useJobs({ initialFilters: externalFilters = {}, onFiltersChange } = {}) {
  const [query, setQueryState] = useState(() => ({
    page: 1,
    ...(externalFilters || {}),
  }));

  const [jobs, setJobs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [nonce, setNonce] = useState(0);

  const activeId = useRef(0);
  const onFiltersChangeRef = useRef(onFiltersChange);

  const queryKey = serializeFilters(query);
  const externalKey = serializeFilters({ page: 1, ...(externalFilters || {}) });
  const prevExternalKey = useRef(externalKey);

  useEffect(() => {
    onFiltersChangeRef.current = onFiltersChange;
  });

  // Apply external (URL) filter changes.
  useEffect(() => {
    if (prevExternalKey.current === externalKey) return;
    prevExternalKey.current = externalKey;
    setQueryState({ page: 1, ...(externalFilters || {}) });
  }, [externalKey, externalFilters]);

  // Report filter changes up so the page can sync the URL.
  useEffect(() => {
    onFiltersChangeRef.current?.(query);
  }, [queryKey]);

  // Fetch the current page of jobs.
  useEffect(() => {
    const requestId = ++activeId.current;
    setLoading(true);
    setError(null);

    getJobs(query)
      .then((data) => {
        if (requestId !== activeId.current) return;
        setJobs(Array.isArray(data?.items) ? data.items : []);
        setTotal(data?.total ?? 0);
        setPage(data?.page ?? 1);
        setPageSize(data?.page_size ?? 20);
        setTotalPages(data?.total_pages ?? 1);
      })
      .catch((err) => {
        if (requestId !== activeId.current) return;
        setError(err.message || "Failed to load jobs");
      })
      .finally(() => {
        if (requestId === activeId.current) setLoading(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [queryKey, nonce]);

  const setQuery = useCallback((updates) => {
    setQueryState((prev) => {
      const next = { ...prev, ...updates };
      // Filter/sort changes restart the search at page 1; explicit page
      // changes are preserved.
      if (!("page" in updates)) next.page = 1;
      return next;
    });
  }, []);

  const clearFilters = useCallback(() => {
    setQueryState({ ...initialFilters(), page: 1 });
  }, []);

  const refetch = useCallback(() => setNonce((value) => value + 1), []);

  return {
    jobs,
    total,
    page,
    pageSize,
    totalPages,
    loading,
    error,
    query,
    setQuery,
    clearFilters,
    refetch,
  };
}