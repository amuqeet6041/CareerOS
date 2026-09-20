import { Suspense } from "react";

import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import JobsExplorer from "@/components/jobs/JobsExplorer";
import { JobCardSkeleton } from "@/components/jobs/Skeletons";

export default function DashboardJobsPage() {
  return (
    <div className="flex min-h-screen bg-surface">
      <DashboardSidebar />
      <div className="flex-1">
        <DashboardHeader />
        <main className="mx-auto max-w-6xl px-6 py-8">
          <h1 className="text-2xl font-semibold text-navy">Job Matches</h1>
          <p className="mt-1 text-sm text-navy/60">
            Search and filter jobs, then see how well each one fits your
            profile.
          </p>
          <Suspense
            fallback={
              <div className="mt-6">
                <div className="mb-5 h-10 max-w-2xl animate-pulse rounded-xl bg-border" />
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
        </main>
      </div>
    </div>
  );
}