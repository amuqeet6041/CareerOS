import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import JobFilters from "@/components/jobs/JobFilters";
import JobList from "@/components/jobs/JobList";

export default function DashboardJobsPage() {
  return (
    <div className="flex min-h-screen bg-surface">
      <DashboardSidebar />
      <div className="flex-1">
        <DashboardHeader />
        <main className="mx-auto max-w-6xl px-6 py-8">
          <h1 className="text-2xl font-semibold text-navy">Job Matches</h1>
          <div className="mt-6 grid gap-6 lg:grid-cols-[240px_1fr]">
            <JobFilters />
            <JobList jobs={[]} />
          </div>
        </main>
      </div>
    </div>
  );
}
