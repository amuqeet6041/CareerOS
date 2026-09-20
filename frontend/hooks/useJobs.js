"use client";

import { useState, useEffect, useCallback } from "react";
import { getJobs } from "@/services/jobService";

// Hook for fetching/filtering jobs against the paginated /api/jobs contract:
// { items, total, page, page_size, total_pages }.
export function useJobs(initialFilters = {}) {
  const [jobs, setJobs] = useState([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState(initialFilters);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getJobs(filters);
      const items = Array.isArray(data) ? data : data?.items ?? [];
      setJobs(items);
      setTotal(Array.isArray(data) ? items.length : data?.total ?? items.length);
    } catch (err) {
      setError(err.message || "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  return { jobs, total, filters, setFilters, loading, error, refetch: fetchJobs };
}
