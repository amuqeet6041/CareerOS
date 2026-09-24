"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useResume } from "@/hooks/useResume";
import ResumeUpload from "./ResumeUpload";
import ResumeAnalysis from "./ResumeAnalysis";
import ResumeProcessingModal from "./ResumeProcessingModal";
import EmptyState from "@/components/shared/EmptyState";

export default function ResumeManager() {
  const { analysis, loading, error, load, applyResult, retryAnalysis } = useResume();
  const [analyzing, setAnalyzing] = useState(false);
  const [flow, setFlow] = useState(null); // null | { status, result?, error? }
  const [flowFileName, setFlowFileName] = useState("");
  const uploadRef = useRef(null);
  const router = useRouter();

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

  const handleFlowStart = useCallback((fileName) => {
    setFlowFileName(fileName || "resume");
    setFlow({ status: "processing" });
  }, []);

  const handleFlowSuccess = useCallback(
    (result) => setFlow({ status: "success", result }),
    [],
  );

  const handleFlowError = useCallback(
    (err) => setFlow({ status: "error", error: err }),
    [],
  );

  const closeFlow = useCallback(() => setFlow(null), []);
  const retryFlow = useCallback(() => uploadRef.current?.submit(), []);

  const go = (href) => {
    closeFlow();
    router.push(href);
  };

  const canAnalyze =
    analysis && analysis.analysis_status !== "ai_analyzed" && !analyzing;

  return (
    <div className="space-y-8">
      <ResumeUpload
        ref={uploadRef}
        onUploaded={applyResult}
        onFlowStart={handleFlowStart}
        onFlowSuccess={handleFlowSuccess}
        onFlowError={handleFlowError}
      />

      {loading ? (
        <div
          role="status"
          aria-label="Loading resume analysis"
          className="space-y-3"
        >
          <div className="skeleton h-4 w-1/3 rounded-lg" />
          <div className="skeleton h-40 w-full rounded-2xl" />
        </div>
      ) : null}

      {!loading && error ? (
        <p className="text-sm text-danger">{error}</p>
      ) : null}

      {!loading ? (
        analysis ? (
          <div className="space-y-4">
            <ResumeAnalysis analysis={analysis} />

            {analysis.analysis_status === "parsed" &&
            (analysis.skills ?? []).length === 0 ? (
              <div className="rounded-lg border border-info/30 bg-info/10 p-4 text-sm text-info">
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
                className="inline-flex w-fit items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-white shadow-glow-primary transition-colors hover:bg-accent-light disabled:cursor-not-allowed disabled:opacity-60"
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

      {flow ? (
        <ResumeProcessingModal
          open
          status={flow.status}
          result={flow.result}
          errorMessage={flow.error?.message}
          fileName={flowFileName}
          onClose={closeFlow}
          onRetry={retryFlow}
          onViewInsights={() => go("/student-dashboard/career-insights")}
        />
      ) : null}
    </div>
  );
}