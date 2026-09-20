"use client";

import { useState, useCallback } from "react";
import { getCareerInsights } from "@/services/careerInsightsService";

export function useCareerInsights() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [noResume, setNoResume] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setNoResume(false);
    try {
      const payload = await getCareerInsights();
      setData(payload);
    } catch (err) {
      if (err.status === 404) {
        setNoResume(true);
        setData(null);
      } else {
        setError(err.message || "Could not load career insights");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, noResume, load };
}