"use client";

import { useEffect } from "react";
import { useResume } from "@/hooks/useResume";
import ResumeUpload from "./ResumeUpload";
import ResumeAnalysis from "./ResumeAnalysis";
import EmptyState from "@/components/shared/EmptyState";

export default function ResumeManager() {
  const { analysis, loading, error, load, upload } = useResume();

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-8">
      <ResumeUpload onUploaded={upload} />

      {loading ? (
        <p className="text-sm text-navy/50">Loading your saved resume analysis...</p>
      ) : null}

      {!loading && error ? (
        <p className="text-sm text-red-600">{error}</p>
      ) : null}

      {!loading ? (
        analysis ? (
          <ResumeAnalysis analysis={analysis} />
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