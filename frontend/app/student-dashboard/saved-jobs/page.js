"use client";

import Link from "next/link";

import DashboardShell from "@/components/dashboard/DashboardShell";
import JobCard from "@/components/jobs/JobCard";
import { JobCardSkeleton } from "@/components/jobs/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import Button from "@/components/shared/Button";
import { useSavedJobs } from "@/hooks/useSavedJobs";

// Saved Jobs list for the authenticated user. Renders the real SavedJob rows
// with the job embedded (GET /api/jobs/saved) and lets the user remove rows
// inline.
export default function SavedJobsPage() {
  const { savedJobs, loading, error, refetch, toggle } = useSavedJobs({
    enabled: true,
  });

  return (
    <DashboardShell>
      <div>
        <h1 className="text-2xl font-bold text-navy">Saved Jobs</h1>
        <p className="mt-1 text-sm text-navy/60">
          Jobs you&apos;ve saved to review later.
        </p>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2" aria-busy="true">
          {Array.from({ length: 6 }, (_, index) => (
            <JobCardSkeleton key={index} />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-2xl border border-line bg-surface p-8 text-center shadow-card">
          <h3 className="text-base font-semibold text-navy">
            Couldn&apos;t load saved jobs
          </h3>
          <p className="mx-auto mt-2 max-w-md text-sm text-muted">{error}</p>
          <Button variant="secondary" className="mt-5" onClick={refetch}>
            Try again
          </Button>
        </div>
      ) : savedJobs.length === 0 ? (
        <EmptyState
          title="No saved jobs yet"
          description="Save jobs from the job board and come back to them here later."
          action={
            <Link href="/jobs">
              <Button>Browse jobs</Button>
            </Link>
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {savedJobs.map((item) =>
            item.job ? (
              <JobCard
                key={item.job_id}
                job={item.job}
                saved
                authenticated
                onToggleSave={toggle}
              />
            ) : (
              <UnavailableSavedCard
                key={item.job_id}
                onRemove={() => toggle(item.job_id, true)}
              />
            )
          )}
        </div>
      )}
    </DashboardShell>
  );
}

function UnavailableSavedCard({ onRemove }) {
  return (
    <article className="flex flex-col justify-between rounded-2xl border border-line bg-surface p-5 shadow-card">
      <p className="text-sm text-navy/70">This saved job is no longer available.</p>
      <Button variant="secondary" className="mt-4" onClick={onRemove}>
        Remove from saved jobs
      </Button>
    </article>
  );
}