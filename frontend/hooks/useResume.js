"use client";

import { useState, useCallback } from "react";
import { uploadResume, getResumeAnalysis, analyzeResume } from "@/services/resumeService";

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

  const upload = useCallback(async (file) => {
    setError(null);
    try {
      const data = await uploadResume(file);
      setAnalysis(data);
      return data;
    } catch (err) {
      setError(err.message || "Resume processing failed");
      throw err;
    }
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

  return { analysis, loading, error, load, upload, retryAnalysis };
}