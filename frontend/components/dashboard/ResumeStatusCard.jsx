"use client";

import Link from "next/link";
import { FileText, UploadCloud, Loader2, RefreshCw } from "lucide-react";
import { SectionError, SectionSkeleton } from "./DashboardSection";
import { formatDate } from "@/utils/formatters";

// Resume status card driven by the real GET /api/resume/analysis response.
// Only the backend's analysis_status values are mapped (parsed / ai_analyzed /
// ai_failed); nothing else is implied. A failed AI analysis offers a Retry
// action backed by POST /api/resume/analyze.

const STATUS_META = {
  ai_analyzed: {
    label: "AI analysis complete",
    style: "border border-green-200 bg-green-50 text-green-700",
  },
  parsed: {
    label: "Basic parse complete",
    style: "border border-sky-200 bg-sky-50 text-sky-700",
  },
  ai_failed: {
    label: "AI analysis failed",
    style: "border border-red-200 bg-red-50 text-red-600",
  },
};

export default function ResumeStatusCard({
  resume = null,
  loading = false,
  error = null,
  retrying = false,
  onRetryAnalysis = null,
  onRetryLoad = null,
}) {
  if (loading && !resume) {
    return (
      <section className="rounded-2xl border border-border bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-base font-semibold text-navy">Resume</h2>
        <SectionSkeleton />
      </section>
    );
  }

  if (!loading && !resume && error) {
    return (
      <section className="rounded-2xl border border-border bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-base font-semibold text-navy">Resume</h2>
        <SectionError message={error} onRetry={onRetryLoad} />
      </section>
    );
  }

  if (!resume) {
    return (
      <section className="rounded-2xl border border-border bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-base font-semibold text-navy">Resume</h2>
        <div className="rounded-xl border border-dashed border-border bg-surface p-6 text-center">
          <UploadCloud className="mx-auto h-8 w-8 text-navy/40" aria-hidden="true" />
          <p className="mt-3 text-sm font-medium text-navy">No resume uploaded yet</p>
          <p className="mt-1 text-xs text-navy/50">
            Upload a resume to unlock matching and recommendations.
          </p>
          <Link
            href="/student-dashboard/resume"
            className="mt-4 inline-block rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-light"
          >
            Upload Resume
          </Link>
        </div>
      </section>
    );
  }

  const meta = STATUS_META[resume.analysis_status] ?? {
    label: resume.analysis_status || "Analysis status unknown",
    style: "border border-border bg-surface text-navy/70",
  };

  return (
    <section className="flex flex-col rounded-2xl border border-border bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-base font-semibold text-navy">Resume</h2>

      <div className="flex items-start gap-3">
        <FileText className="mt-0.5 h-5 w-5 shrink-0 text-navy/40" aria-hidden="true" />
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-navy">
            {resume.file_name}
          </p>
          {resume.uploaded_at ? (
            <p className="mt-0.5 text-xs text-navy/50">
              Uploaded {formatDate(resume.uploaded_at)}
            </p>
          ) : null}
        </div>
      </div>

      <div className="mt-3">
        <span
          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${meta.style}`}
        >
          {meta.label}
        </span>
      </div>

      {resume.total_experience_years != null ? (
        <p className="mt-3 text-xs text-navy/60">
          {resume.total_experience_years} year
          {resume.total_experience_years === 1 ? "" : "s"} of experience recorded
        </p>
      ) : null}

      {resume.analysis_status === "ai_failed" && onRetryAnalysis ? (
        <button
          type="button"
          onClick={onRetryAnalysis}
          disabled={retrying}
          className="mt-4 inline-flex w-fit items-center gap-1.5 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm font-medium text-red-700 transition-colors hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {retrying ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
          )}
          {retrying ? "Retrying..." : "Retry analysis"}
        </button>
      ) : null}

      {error && resume ? (
        <p role="alert" className="mt-3 text-xs text-red-600">
          {error}
        </p>
      ) : null}

      <div className="mt-auto pt-4">
        <Link
          href="/student-dashboard/resume"
          className="text-sm font-medium text-accent transition-colors hover:text-accent-light"
        >
          View resume
        </Link>
      </div>
    </section>
  );
}