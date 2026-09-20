import Link from "next/link";
import EmptyState from "@/components/shared/EmptyState";
import DashboardSection, {
  SectionError,
  SectionSkeleton,
} from "./DashboardSection";
import ApplicationStatus from "@/components/applications/ApplicationStatus";
import { formatDate } from "@/utils/formatters";

// The 3 most recent applications (GET /api/applications returns newest first).
// Each has its status rendered explicitly and links to the job detail page;
// the embedded job data means no extra per-application requests.

export default function RecentApplications({
  applications = [],
  loading = false,
}) {
  const recent = applications.slice(0, 3);

  return (
    <DashboardSection
      title="Recent applications"
      subtitle="Tracked applications, newest first."
      actionHref="/student-dashboard/applications"
      actionLabel="View all applications"
    >
      {loading && applications.length === 0 ? (
        <SectionSkeleton />
      ) : recent.length === 0 ? (
        <EmptyState
          title="No applications yet"
          description="Apply to jobs and track them here."
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
        <ul className="space-y-3">
          {recent.map((app) => (
            <li
              key={app.id}
              className="flex items-center justify-between gap-3 rounded-xl border border-border p-3"
            >
              <div className="min-w-0">
                <p className="truncate text-xs font-medium uppercase tracking-wide text-navy/50">
                  {app.job?.company}
                </p>
                <Link
                  href={`/jobs/${app.job_id}`}
                  className="mt-0.5 block truncate text-sm font-medium text-navy hover:text-accent"
                >
                  {app.job?.title ?? `Job #${app.job_id}`}
                </Link>
                <p className="mt-0.5 text-xs text-navy/45">
                  {app.applied_at ? formatDate(app.applied_at) : ""}
                </p>
              </div>
              <ApplicationStatus status={app.status} />
            </li>
          ))}
        </ul>
      )}
    </DashboardSection>
  );
}