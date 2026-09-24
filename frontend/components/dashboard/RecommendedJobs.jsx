"use client";

import Link from "next/link";
import EmptyState from "@/components/shared/EmptyState";
import JobCard from "@/components/jobs/JobCard";
import DashboardSection, {
  SectionError,
  SectionSkeleton,
} from "./DashboardSection";

// Personalized recommendations. The orchestrator passes the ranked result of
// the bounded useJobRecommendations hook (up to 5 jobs that have a real,
// non-null overall match score). JobCard renders candidates with full
// save/apply controls and the same match presentation as the Jobs pages.

export default function RecommendedJobs({
  recommendations = [],
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
      subtitle="Ranked by how well your resume matches each job."
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
              : "Try browsing all jobs or save some to keep an eye on them. Recommendations update as more scoring data is available."
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
    </DashboardSection>
  );
}