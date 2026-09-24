import Link from "next/link";
import EmptyState from "@/components/shared/EmptyState";
import DashboardSection, {
  SectionError,
  SectionSkeleton,
} from "./DashboardSection";
import { STATUS_LABELS } from "@/components/applications/ApplicationStatus";

// Application stats computed from the real GET /api/applications records. Only
// statuses that actually exist in the data are shown, so the summary never
// claims an "Interview" count when nobody has reached that stage.

const STATUS_ORDER = ["applied", "in_review", "interview", "offer", "rejected"];

export default function ApplicationStats({
  applications = [],
  loading = false,
  error = null,
  onRetry = null,
}) {
  const total = applications.length;

  return (
    <DashboardSection
      title="Applications"
      subtitle="Tracked from the Jobs page."
      actionHref="/student-dashboard/applications"
      actionLabel="View all applications"
    >
      {loading && total === 0 ? (
        <SectionSkeleton />
      ) : error ? (
        <SectionError message={error} onRetry={onRetry} />
      ) : total === 0 ? (
        <EmptyState
          title="No applications yet"
          description="Apply to jobs from the Jobs page and they'll be tracked here."
          action={
            <Link
              href="/jobs"
              className="inline-block rounded-md bg-primary px-4 py-2 text-sm font-medium text-white shadow-glow-primary transition-colors hover:bg-accent-light"
            >
              Browse jobs
            </Link>
          }
        />
      ) : (
        <div>
          <p className="text-3xl font-semibold text-navy">{total}</p>
          <p className="text-xs text-navy/50">
            {total === 1 ? "application" : "applications"} total
          </p>

          <ul className="mt-4 space-y-2">
            {STATUS_ORDER.filter((status) =>
              applications.some((app) => app.status === status)
            ).map((status) => {
              const count = applications.filter(
                (app) => app.status === status
              ).length;
              const pct = Math.round((count / total) * 100);
              return (
                <li key={status}>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-navy/70">
                      {STATUS_LABELS[status] ?? status}
                    </span>
                    <span className="font-medium text-navy">{count}</span>
                  </div>
                  <div
                    className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-line/40"
                    role="progressbar"
                    aria-valuemin={0}
                    aria-valuemax={total}
                    aria-valuenow={count}
                    aria-label={`${STATUS_LABELS[status] ?? status} count`}
                  >
                    <div
                      className="h-full rounded-full bg-accent/70"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </DashboardSection>
  );
}