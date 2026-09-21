"use client";

import { useCallback, useEffect, useState } from "react";
import { useResume } from "@/hooks/useResume";
import ResumeUpload from "./ResumeUpload";
import ResumeAnalysis from "./ResumeAnalysis";
import EmptyState from "@/components/shared/EmptyState";

export default function ResumeManager() {
  const { analysis, loading, error, load, applyResult, retryAnalysis } = useResume();
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    load();
  }, [load]);

  const onAnalyze = useCallback(async () => {
    setAnalyzing(true);
    try {
      await retryAnalysis();
    } catch {
      // Failure is surfaced by useResume's error state.
    } finally {
      setAnalyzing(false);
    }
  }, [retryAnalysis]);

  const canAnalyze =
    analysis && analysis.analysis_status !== "ai_analyzed" && !analyzing;

  return (
    <div className="space-y-8">
      <ResumeUpload onUploaded={applyResult} />

      {loading ? (
        <p className="text-sm text-navy/50">Loading your saved resume analysis...</p>
      ) : null}

      {!loading && error ? (
        <p className="text-sm text-red-600">{error}</p>
      ) : null}

      {!loading ? (
        analysis ? (
          <div className="space-y-4">
            <ResumeAnalysis analysis={analysis} />

            {analysis.analysis_status === "parsed" &&
            (analysis.skills ?? []).length === 0 ? (
              <div className="rounded-lg border border-sky-200 bg-sky-50 p-4 text-sm text-sky-800">
                Your resume text was extracted, but no skills, education,
                experience, or certifications could be identified yet. If AI
                analysis is enabled, run it below to extract your structured
                resume intelligence.
              </div>
            ) : null}

            {canAnalyze ? (
              <button
                type="button"
                onClick={onAnalyze}
                disabled={analyzing}
                className="inline-flex w-fit items-center gap-1.5 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-light disabled:cursor-not-allowed disabled:opacity-60"
              >
                {analyzing ? "Analyzing..." : "Analyze with AI / Retry analysis"}
              </button>
            ) : null}

            {analyzing ? (
              <p className="text-sm text-navy/50">
                Analyzing your resume with the AI provider...
              </p>
            ) : null}
          </div>
        ) : (
          <EmptyState
            title="No analysis yet"
            description="Upload a resume to see extracted skills, education, experience, and certifications here."
          />
        )
      ) : null}
    </div>
  );
}