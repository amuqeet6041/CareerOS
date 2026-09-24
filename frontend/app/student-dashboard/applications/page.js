"use client";

import Link from "next/link";

import DashboardShell from "@/components/dashboard/DashboardShell";
import ApplicationCard from "@/components/applications/ApplicationCard";
import EmptyState from "@/components/shared/EmptyState";
import Button from "@/components/shared/Button";
import { useApplications } from "@/hooks/useApplications";

// My Applications list for the authenticated user. Each record embeds the full
// job (ApplicationOut.job), so the page needs exactly one GET /api/applications
// request.
export default function ApplicationsPage() {
  const { applications, loading, error, refetch } = useApplications({
    enabled: true,
  });

  return (
    <DashboardShell>
      <div>
        <h1 className="text-2xl font-bold text-navy">Applications</h1>
        <p className="mt-1 text-sm text-navy/60">
          Jobs you&apos;re actively pursuing, in the status the backend
          reports.
        </p>
      </div>

      {loading ? (
        <div className="space-y-4" aria-busy="true">
          {Array.from({ length: 4 }, (_, index) => (
            <div
              key={index}
              className="h-32 animate-pulse rounded-2xl border border-line bg-elevated"
              aria-hidden="true"
            />
          ))}
        </div>
      ) : error ? (
        <div className="rounded-2xl border border-line bg-surface p-8 text-center shadow-card">
          <h3 className="text-base font-semibold text-navy">
            Couldn&apos;t load applications
          </h3>
          <p className="mx-auto mt-2 max-w-md text-sm text-muted">{error}</p>
          <Button variant="secondary" className="mt-5" onClick={refetch}>
            Try again
          </Button>
        </div>
      ) : applications.length === 0 ? (
        <EmptyState
          title="No applications yet"
          description="Apply to jobs from the job board and they'll show up here so you can track them."
          action={
            <Link href="/jobs">
              <Button>Browse jobs</Button>
            </Link>
          }
        />
      ) : (
        <div className="space-y-4">
          {applications.map((application) => (
            <ApplicationCard key={application.id} application={application} />
          ))}
        </div>
      )}
    </DashboardShell>
  );
}