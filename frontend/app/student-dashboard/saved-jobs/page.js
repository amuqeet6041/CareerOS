import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import JobList from "@/components/jobs/JobList";

export default function SavedJobsPage() {
  return (
    <div className="flex min-h-screen bg-surface">
      <DashboardSidebar />
      <div className="flex-1">
        <DashboardHeader />
        <main className="mx-auto max-w-6xl px-6 py-8">
          <h1 className="text-2xl font-semibold text-navy">Saved Jobs</h1>
          <div className="mt-6">
            <JobList jobs={[]} />
          </div>
        </main>
      </div>
    </div>
  );
}
