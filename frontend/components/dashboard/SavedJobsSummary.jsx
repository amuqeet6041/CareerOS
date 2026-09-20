import Link from "next/link";
import EmptyState from "@/components/shared/EmptyState";
import DashboardSection, {
  SectionError,
  SectionSkeleton,
} from "./DashboardSection";

// Saved jobs summary from the single GET /api/jobs/saved request (newest
// first). Shows the real count plus the 3 most recent entries.

export default function SavedJobsSummary({
  savedJobs = [],
  loading = false,
  error = null,
  onRetry = null,
}) {
  const recent = savedJobs.slice(0, 3);

  return (
    <DashboardSection
      title="Saved jobs"
      subtitle="Bookmarked for later."
      actionHref="/student-dashboard/saved-jobs"
      actionLabel="View saved jobs"
    >
      {loading && savedJobs.length === 0 ? (
        <SectionSkeleton />
      ) : error ? (
        <SectionError message={error} onRetry={onRetry} />
      ) : savedJobs.length === 0 ? (
        <EmptyState
          title="Nothing saved yet"
          description="Save jobs you're interested in and they'll show up here."
          action={
            <Link
              href="/jobs"
              className="inline-block rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-light"
            >
              Browse jobs
            </Link>
          }
        />
      ) : (
        <div>
          <p className="text-3xl font-semibold text-navy">{savedJobs.length}</p>
          <p className="text-xs text-navy/50">
            {savedJobs.length === 1 ? "job saved" : "jobs saved"}
          </p>

          <ul className="mt-4 space-y-2">
            {recent.map((item) => (
              <li key={item.job_id}>
                <Link
                  href={`/jobs/${item.job_id}`}
                  className="block rounded-xl border border-border p-3 transition-colors hover:bg-surface"
                >
                  <p className="truncate text-sm font-medium text-navy">
                    {item.job?.title ?? `Job #${item.job_id}`}
                  </p>
                  <p className="truncate text-xs text-navy/50">
                    {item.job?.company}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </DashboardSection>
  );
}