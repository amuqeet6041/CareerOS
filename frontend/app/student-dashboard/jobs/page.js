import { Suspense } from "react";

import DashboardShell from "@/components/dashboard/DashboardShell";
import JobsExplorer from "@/components/jobs/JobsExplorer";
import { JobCardSkeleton } from "@/components/jobs/Skeletons";

export default function DashboardJobsPage() {
  return (
    <DashboardShell>
      <div>
        <h1 className="text-2xl font-bold text-navy">Job Matches</h1>
        <p className="mt-1 text-sm text-navy/60">
          Search and filter jobs, then see how well each one fits your
          profile.
        </p>
      </div>
      <Suspense
        fallback={
          <div>
            <div className="mb-5 h-10 max-w-2xl animate-pulse rounded-xl bg-elevated-strong" />
            <div className="grid gap-4 md:grid-cols-2" aria-busy="true">
              {Array.from({ length: 6 }, (_, index) => (
                <JobCardSkeleton key={index} />
              ))}
            </div>
          </div>
        }
      >
        <JobsExplorer variant="dashboard" />
      </Suspense>
    </DashboardShell>
  );
}