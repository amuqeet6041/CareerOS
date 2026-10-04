"use client";

import Link from "next/link";
import EmptyState from "@/components/shared/EmptyState";
import JobCard from "@/components/jobs/JobCard";
import DashboardSection, {
  SectionError,
  SectionSkeleton,
} from "./DashboardSection";

// Personalized recommendations. The orchestrator passes the ranked result of
// useJobRecommendations (up to 5 live jobs searched from the resume that have
// a real, non-zero overall match score). JobCard renders candidates with full
// save/apply controls and the same match presentation as the Jobs pages.

// The keyless fallback provider's terms require a visible credit link.
const SOURCE_CREDITS = {
  jobicy: { label: "Jobicy", url: "https://jobicy.com" },
};

export default function RecommendedJobs({
  recommendations = [],
  source = null,
  loading = false,
  error = null,
  onRetry = null,
  noResume = false,
  savedIds = new Set(),
  appliedIds = new Set(),
  onToggleSave = null,
  onApplyTracked = null,
}) {
  const browseAction = (
    <Link
      href="/jobs"
      className="inline-block rounded-md bg-primary px-4 py-2 text-sm font-medium text-white shadow-glow-primary transition-colors hover:bg-accent-light"
    >
      Browse jobs
    </Link>
  );

  return (
    <DashboardSection
      title="Recommended for you"
      subtitle="Live openings searched from your resume, ranked by how well you match."
      actionHref="/jobs"
      actionLabel="View all jobs"
    >
      {loading && recommendations.length === 0 ? (
        <SectionSkeleton />
      ) : error ? (
        <SectionError message={error} onRetry={onRetry} />
      ) : recommendations.length === 0 ? (
        <EmptyState
          title={noResume ? "No recommendations yet" : "No strong matches right now"}
          description={
            noResume
              ? "Upload and analyze your resume to get personalized job recommendations."
              : "No live openings closely matched your resume. Add preferred roles in your profile to widen the search, or browse all jobs."
          }
          action={noResume ? (
            <Link
              href="/student-dashboard/resume"
className="inline-block rounded-md bg-primary px-4 py-2 text-sm font-medium text-white shadow-glow-primary transition-colors hover:bg-accent-light"
            >
              Upload resume
            </Link>
          ) : (
            browseAction
          )}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {recommendations.map(({ job, match }) => (
            <JobCard
              key={job.id}
              job={job}
              match={match}
              saved={savedIds.has(job.id)}
              applied={appliedIds.has(job.id)}
              authenticated
              onToggleSave={onToggleSave}
              onApplyTracked={onApplyTracked}
            />
          ))}
        </div>
      )}
      {SOURCE_CREDITS[source] && !error ? (
        <p className="mt-4 text-xs text-muted">
          Remote jobs via{" "}
          <a
            href={SOURCE_CREDITS[source].url}
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-accent"
          >
            {SOURCE_CREDITS[source].label}
          </a>
        </p>
      ) : null}
    </DashboardSection>
  );
}