import Link from "next/link";

import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import EmptyState from "@/components/shared/EmptyState";

export default function SavedJobsPage() {
  return (
    <div className="flex min-h-screen bg-surface">
      <DashboardSidebar />
      <div className="flex-1">
        <DashboardHeader />
        <main className="mx-auto max-w-6xl px-6 py-8">
          <h1 className="text-2xl font-semibold text-navy">Saved Jobs</h1>
          <div className="mt-6">
            <EmptyState
              title="No saved jobs yet"
              description="Saving jobs for later is coming soon. In the meantime, browse the job board to find roles that fit your profile."
              action={
                <Link
                  href="/jobs"
                  className="inline-flex items-center justify-center rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-light"
                >
                  Browse jobs
                </Link>
              }
            />
          </div>
        </main>
      </div>
    </div>
  );
}