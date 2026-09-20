import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";

export default function ApplicationsPage() {
  return (
    <div className="flex min-h-screen bg-surface">
      <DashboardSidebar />
      <div className="flex-1">
        <DashboardHeader />
        <main className="mx-auto max-w-6xl px-6 py-8">
          <h1 className="text-2xl font-semibold text-navy">Applications</h1>
          <p className="mt-2 text-navy/70">
            Placeholder list of tracked applications. Wire up to applicationService.js.
          </p>
        </main>
      </div>
    </div>
  );
}
