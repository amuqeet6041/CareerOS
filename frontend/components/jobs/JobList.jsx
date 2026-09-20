import JobCard from "./JobCard";
import { JobCardSkeleton } from "./Skeletons";
import EmptyState from "@/components/shared/EmptyState";

// Job list with explicit loading (skeletons), error (retry) and empty states
// so the UI never renders a blank screen or a misleading "no jobs".
export default function JobList({
  jobs = [],
  loading = false,
  error = null,
  onRetry = null,
  matchMap = null,
  loadingMatchIds = [],
  emptyTitle = "No jobs found",
  emptyDescription = "Try adjusting your search or filters.",
  emptyAction = null,
}) {
  if (loading && jobs.length === 0) {
    return (
      <div className="grid gap-4 md:grid-cols-2" aria-busy="true">
        {Array.from({ length: 6 }, (_, index) => (
          <JobCardSkeleton key={index} />
        ))}
      </div>
    );
  }

  if (error && jobs.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-white p-8 text-center">
        <h3 className="text-base font-semibold text-navy">
          Couldn&apos;t load jobs
        </h3>
        <p className="mx-auto mt-2 max-w-md text-sm text-navy/60">{error}</p>
        {onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            className="mt-5 rounded-md border border-border px-4 py-2 text-sm font-medium text-navy transition-colors hover:bg-surface"
          >
            Try again
          </button>
        ) : null}
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyDescription}
        action={emptyAction}
      />
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {jobs.map((job) => (
        <JobCard
          key={job.id}
          job={job}
          match={matchMap ? matchMap[job.id] ?? null : null}
          matchLoading={loadingMatchIds.includes(job.id)}
        />
      ))}
    </div>
  );
}