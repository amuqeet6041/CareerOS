"use client";

import Link from "next/link";

import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import ApplicationCard from "@/components/applications/ApplicationCard";
import EmptyState from "@/components/shared/EmptyState";
import { useApplications } from "@/hooks/useApplications";

// My Applications list for the authenticated user. Each record embeds the full
// job (ApplicationOut.job), so the page needs exactly one GET /api/applications
// request.
export default function ApplicationsPage() {
  const { applications, loading, error, refetch } = useApplications({
    enabled: true,
  });

  return (
    <div className="flex min-h-screen bg-surface">
      <DashboardSidebar />
      <div className="flex-1">
        <DashboardHeader />
        <main className="mx-auto max-w-6xl px-6 py-8">
          <h1 className="text-2xl font-semibold text-navy">Applications</h1>
          <p className="mt-2 text-sm text-navy/60">
            Jobs you&apos;re actively pursuing, in the status the backend
            reports.
          </p>

          <div className="mt-6">
            {loading ? (
              <div className="space-y-4" aria-busy="true">
                {Array.from({ length: 4 }, (_, index) => (
                  <div
                    key={index}
                    className="h-32 animate-pulse rounded-lg border border-border bg-white"
                    aria-hidden="true"
                  />
                ))}
              </div>
            ) : error ? (
              <div className="rounded-lg border border-border bg-white p-8 text-center">
                <h3 className="text-base font-semibold text-navy">
                  Couldn&apos;t load applications
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
            ) : applications.length === 0 ? (
              <EmptyState
                title="No applications yet"
                description="Apply to jobs from the job board and they'll show up here so you can track them."
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
              <div className="space-y-4">
                {applications.map((application) => (
                  <ApplicationCard
                    key={application.id}
                    application={application}
                  />
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}