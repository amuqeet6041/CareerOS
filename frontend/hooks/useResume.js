"use client";

import { useState, useCallback } from "react";
import { getResumeAnalysis, analyzeResume } from "@/services/resumeService";

export function useResume() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getResumeAnalysis();
      setAnalysis(data);
    } catch (err) {
      if (err.status === 404) {
        setAnalysis(null);
      } else {
        setError(err.message || "Could not load resume analysis");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // Consume the result of an upload performed by ResumeUpload. This must NOT
  // re-upload the parsed result: it only mirrors it into local state.
  const applyResult = useCallback((result) => {
    setError(null);
    setAnalysis(result);
  }, []);

  const retryAnalysis = useCallback(async () => {
    setError(null);
    try {
      const data = await analyzeResume();
      setAnalysis(data);
      return data;
    } catch (err) {
      setError(err.message || "Resume analysis failed");
      throw err;
    }
  }, []);

  return { analysis, loading, error, load, applyResult, retryAnalysis };
}