"use client";

import Link from "next/link";

import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import JobCard from "@/components/jobs/JobCard";
import { JobCardSkeleton } from "@/components/jobs/Skeletons";
import EmptyState from "@/components/shared/EmptyState";
import { useSavedJobs } from "@/hooks/useSavedJobs";

// Saved Jobs list for the authenticated user. Renders the real SavedJob rows
// with the job embedded (GET /api/jobs/saved) and lets the user remove rows
// inline.
export default function SavedJobsPage() {
  const { savedJobs, loading, error, refetch, toggle } = useSavedJobs({
    enabled: true,
  });

  return (
    <div className="flex min-h-screen bg-surface">
      <DashboardSidebar />
      <div className="flex-1">
        <DashboardHeader />
        <main className="mx-auto max-w-6xl px-6 py-8">
          <h1 className="text-2xl font-semibold text-navy">Saved Jobs</h1>
          <p className="mt-2 text-sm text-navy/60">
            Jobs you&apos;ve saved to review later.
          </p>

          <div className="mt-6">
            {loading ? (
              <div className="grid gap-4 md:grid-cols-2" aria-busy="true">
                {Array.from({ length: 6 }, (_, index) => (
                  <JobCardSkeleton key={index} />
                ))}
              </div>
            ) : error ? (
              <div className="rounded-lg border border-border bg-white p-8 text-center">
                <h3 className="text-base font-semibold text-navy">
                  Couldn&apos;t load saved jobs
                </h3>
                <p className="mx-auto mt-2 max-w-md text-sm text-navy/60">
                  {error}
                </p>
                <button
                  type="button"
                  onClick={refetch}
                  className="mt-5 rounded-md border border-border px-4 py-2 text-sm font-medium text-navy transition-colors hover:bg-surface"
                >
                  Try again
                </button>
              </div>
            ) : savedJobs.length === 0 ? (
              <EmptyState
                title="No saved jobs yet"
                description="Save jobs from the job board and come back to them here later."
                action={
                  <Link
                    href="/jobs"
                    className="inline-flex items-center justify-center rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-light"
                  >
                    Browse jobs
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
          </div>
        </main>
      </div>
    </div>
  );
}

function UnavailableSavedCard({ onRemove }) {
  return (
    <article className="flex flex-col justify-between rounded-lg border border-border bg-white p-5 shadow-sm">
      <p className="text-sm text-navy/70">
        This saved job is no longer available.
      </p>
      <button
        type="button"
        onClick={onRemove}
        className="mt-4 inline-flex items-center justify-center rounded-md border border-border px-4 py-2 text-sm font-medium text-navy transition-colors hover:bg-surface"
      >
        Remove from saved jobs
      </button>
    </article>
  );
}