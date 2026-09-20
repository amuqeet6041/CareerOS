"use client";

import { useState, useEffect, useCallback } from "react";
import { getJobs } from "@/services/jobService";

// Placeholder hook for fetching/filtering jobs.
export function useJobs(initialFilters = {}) {
  const [jobs, setJobs] = useState([]);
  const [filters, setFilters] = useState(initialFilters);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getJobs(filters);
      setJobs(data);
    } catch (err) {
      setError(err.message || "Failed to load jobs");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  return { jobs, filters, setFilters, loading, error, refetch: fetchJobs };
}
